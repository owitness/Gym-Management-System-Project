import mysql.connector
from mysql.connector import pooling
from sshtunnel import SSHTunnelForwarder
from config import DATABASE_CONFIG, SSH_CONFIG
import paramiko
import threading
import os
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

class DatabaseConnectionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._tunnel = None
        self._pool = None
        self._pem_path = os.path.join(os.path.expanduser("~"), "Downloads", "main.pem")
        self._last_connection_time = 0
        self._connection_timeout = 3600
        self._connections = []

    def _create_ssh_tunnel(self):
        if self._tunnel and self._tunnel.is_active:
            return

        logger.debug(f"Loading PEM key from {self._pem_path}")
        if not os.path.exists(self._pem_path):
            logger.error(f"PEM file not found at {self._pem_path}")
            raise FileNotFoundError(f"PEM file not found: {self._pem_path}")

        try:
            key = paramiko.RSAKey.from_private_key_file(self._pem_path)
            logger.debug("PEM key loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load PEM key: {e}")
            raise

        try:
            self._tunnel = SSHTunnelForwarder(
                (SSH_CONFIG['ssh_host'], 22),
                ssh_username=SSH_CONFIG['ssh_username'],
                ssh_pkey=key,
                remote_bind_address=SSH_CONFIG['remote_bind_address'],
                local_bind_address=('127.0.0.1', 0),
                allow_agent=False,
                #look_for_keys=False
            )
            self._tunnel.start()
            logger.info(f"SSH tunnel started on local port {self._tunnel.local_bind_port}")
        except Exception as e:
            logger.error(f"Failed to start SSH tunnel: {e}")
            raise

    def _create_connection_pool(self):
        if self._pool:
            return

        try:
            self._pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="mypool",
                pool_size=10,
                host='127.0.0.1',
                port=self._tunnel.local_bind_port,
                user=DATABASE_CONFIG['user'],
                password=DATABASE_CONFIG['password'],
                database=DATABASE_CONFIG['database'],
                autocommit=True,
                connect_timeout=10
            )
            self._last_connection_time = time.time()
            logger.info("MySQL connection pool created successfully")
        except mysql.connector.Error as e:
            logger.error(f"Failed to create MySQL pool: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating MySQL pool: {e}")
            raise

    def _check_connection_age(self):
        if time.time() - self._last_connection_time > self._connection_timeout:
            self._refresh_connections()

    def _refresh_connections(self):
        for conn in self._connections:
            try:
                if conn.is_connected():
                    conn.close()
            except:
                pass
        self._connections.clear()
        self._pool = None
        self._create_connection_pool()

    @contextmanager
    def get_connection(self):
        try:
            self._create_ssh_tunnel()
            self._create_connection_pool()
            self._check_connection_age()

            conn = self._pool.get_connection()
            cursor = conn.cursor()
            self._connections.append(conn)

            try:
                yield conn, cursor
            finally:
                cursor.close()
                if conn.is_connected():
                    conn.close()
                self._connections.remove(conn)
        except mysql.connector.Error as e:
            logger.error(f"MySQL connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_connection: {e}")
            raise

    def cleanup(self):
        if self._tunnel and self._tunnel.is_active:
            self._tunnel.close()
        for conn in self._connections:
            try:
                if conn.is_connected():
                    conn.close()
            except:
                pass
        self._connections.clear()
        self._pool = None

# Usage wrapper
db_manager = DatabaseConnectionManager()

@contextmanager
def get_db():
    with db_manager.get_connection() as (conn, cursor):
        yield conn
