import mysql.connector
from mysql.connector import pooling
from sshtunnel import SSHTunnelForwarder
from config import DATABASE_CONFIG, SSH_CONFIG
from contextlib import contextmanager
import threading
import time
import logging
import paramiko
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class DatabaseConnectionManager:
    _instance = None
    _lock = threading.Lock()
    _local = threading.local()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the connection manager"""
        self._tunnel = None
        self._pool = None
        self._connections = []
        self._last_connection_time = 0
        self._connection_timeout = 3600  # 1 hour
        self._max_retries = 3
        self._retry_delay = 1  # seconds
    
    def _create_ssh_tunnel(self):
        """Create and start SSH tunnel"""
        try:
            if self._tunnel is None or not self._tunnel.is_active:
                # Log SSH configuration
                logger.debug(f"SSH Config: host={SSH_CONFIG['ssh_host']}, username={SSH_CONFIG['ssh_username']}")
                logger.debug(f"Private key path: {SSH_CONFIG['ssh_private_key']}")
                logger.debug(f"Private key exists: {os.path.exists(SSH_CONFIG['ssh_private_key'])}")
                
                # Create SSH key for authentication
                try:
                    pkey = paramiko.RSAKey.from_private_key_file(SSH_CONFIG['ssh_private_key'])
                    logger.debug("Successfully loaded private key")
                except Exception as e:
                    logger.error(f"Failed to load private key: {str(e)}")
                    raise
                
                try:
                    self._tunnel = SSHTunnelForwarder(
                        (SSH_CONFIG['ssh_host'], 22),
                        ssh_username=SSH_CONFIG['ssh_username'],
                        ssh_pkey=pkey,
                        remote_bind_address=SSH_CONFIG['remote_bind_address'],
                        local_bind_address=('127.0.0.1', 0),  # Let the system choose a free port
                        allow_agent=False
                    )
                    logger.debug("Successfully created SSH tunnel")
                except Exception as e:
                    logger.error(f"Failed to create SSH tunnel: {str(e)}")
                    raise
                
                try:
                    self._tunnel.start()
                    logger.info(f"SSH tunnel established successfully on local port {self._tunnel.local_bind_port}")
                except Exception as e:
                    logger.error(f"Failed to start SSH tunnel: {str(e)}")
                    raise
        except Exception as e:
            logger.error(f"Failed to establish SSH tunnel: {str(e)}")
            raise
    
    def _create_connection_pool(self):
        """Create MySQL connection pool through SSH tunnel"""
        try:
            if self._pool is None:
                # Log database configuration
                logger.debug(f"Creating connection pool with local port {self._tunnel.local_bind_port}")
                
                pool_config = {
                    'pool_name': 'mypool',
                    'pool_size': 5,
                    'host': '127.0.0.1',
                    'port': self._tunnel.local_bind_port,
                    'user': DATABASE_CONFIG['user'],
                    'password': DATABASE_CONFIG['password'],
                    'database': DATABASE_CONFIG['database'],
                    'autocommit': True,
                    'pool_reset_session': True
                }
                logger.debug(f"Pool config: {pool_config}")
                
                try:
                    self._pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
                    self._last_connection_time = time.time()
                    logger.info("Database connection pool created successfully")
                except Exception as e:
                    logger.error(f"Failed to create connection pool: {str(e)}")
                    raise
        except Exception as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            raise

    def _check_connection_age(self):
        """Check if connections need to be refreshed"""
        current_time = time.time()
        if current_time - self._last_connection_time > self._connection_timeout:
            self._refresh_connections()

    def _refresh_connections(self):
        """Refresh all connections in the pool"""
        with self._lock:
            # Close all active connections
            for conn in self._connections:
                try:
                    if conn.is_connected():
                        conn.close()
                except:
                    pass
            self._connections.clear()
            
            # Reset the pool
            self._pool = None
            self._create_connection_pool()

    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool with automatic retry"""
        for attempt in range(self._max_retries):
            try:
                # Ensure SSH tunnel is active
                self._create_ssh_tunnel()
                
                # Create pool if needed
                if self._pool is None:
                    self._create_connection_pool()
                
                # Check connection age
                self._check_connection_age()
                
                # Get connection from pool
                connection = self._pool.get_connection()
                self._connections.append(connection)
                cursor = connection.cursor()
                try:
                    yield connection, cursor
                finally:
                    cursor.close()
                    if connection.is_connected():
                        connection.close()
                    if connection in self._connections:
                        self._connections.remove(connection)
                break
                
            except (mysql.connector.Error, Exception) as e:
                logger.error(f"Database connection error (attempt {attempt + 1}): {str(e)}")
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(self._retry_delay)
                # Force refresh on error
                self._refresh_connections()

    def cleanup(self):
        """Cleanup resources"""
        with self._lock:
            # Close all active connections
            for conn in self._connections:
                try:
                    if conn.is_connected():
                        conn.close()
                except:
                    pass
            self._connections.clear()
            
            # Reset the pool
            self._pool = None
            
            # Close the SSH tunnel
            if self._tunnel is not None and self._tunnel.is_active:
                self._tunnel.close()
                self._tunnel = None

# Global instance
db_manager = DatabaseConnectionManager()

@contextmanager
def get_db():
    """Get a database connection with automatic cleanup."""
    with db_manager.get_connection() as (conn, cursor):
        yield conn

# Export the get_db function
__all__ = ['get_db']

# Example usage:
# with get_db() as (conn, cursor):
#     cursor.execute("SELECT * FROM users")
#     results = cursor.fetchall()
#     cursor.close() 