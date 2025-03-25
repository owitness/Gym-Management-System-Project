import os
import subprocess
import time
import signal
import sys
import psutil

# Test database configuration
TEST_DATABASE_CONFIG = {
    'host': 'gym-database.clqqsuqke2sz.us-east-2.rds.amazonaws.com',
    'user': 'root',
    'password': 'COSCAdmin',
    'database': 'gym_management_test',  # Use a separate test database
    'port': 3306
}

# Test user credentials
TEST_USER = {
    'name': 'sdfdfsdfsdffgferg',
    'email': 'test@example.com',
    'password': 'TestPassword123',
    'dob': '1990-01-01',
    'address': '123 Test St',
    'city': 'Test City',
    'state': 'TS',
    'zipcode': '12345',
    'auto_payment': False
}

TEST_ADMIN = {
    'name': 'oifneergerg',
    'email': 'admin@example.com',
    'password': 'AdminPassword123',
    'dob': '1980-01-01',
    'address': '456 Admin St',
    'city': 'Admin City',
    'state': 'AS',
    'zipcode': '67890',
    'auto_payment': False
}

# Test server configuration
TEST_SERVER_HOST = 'localhost'
TEST_SERVER_PORT = 5001
TEST_SERVER_URL = f'http://{TEST_SERVER_HOST}:{TEST_SERVER_PORT}'
TEST_API_URL = f'{TEST_SERVER_URL}/api'

# Test timeouts
WAIT_TIMEOUT = 10  # seconds

def kill_process_on_port(port):
    """Kill any process running on the specified port"""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.connections('inet'):
                    if conn.laddr.port == port:
                        proc.kill()
                        time.sleep(0.5)  # Give the process time to die
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")

def start_test_server():
    """Start the Flask test server"""
    # Kill any existing process on port 5001
    kill_process_on_port(TEST_SERVER_PORT)

    # Set up environment variables
    env = os.environ.copy()
    env['FLASK_ENV'] = 'testing'
    env['FLASK_APP'] = 'app.py'
    env['PYTHONUNBUFFERED'] = '1'  # Ensure Python output is not buffered

    # Start the Flask server
    server_process = subprocess.Popen(
        [sys.executable, 'app.py'],  # Use sys.executable to ensure correct Python
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,  # Use text mode for output
        bufsize=1,  # Line buffered
        universal_newlines=True  # Translate newlines
    )
    
    # Wait for server to start and verify it's running
    for attempt in range(5):  # Try 5 times
        time.sleep(1)
        try:
            # Check if process is still running
            if server_process.poll() is not None:
                # Process has terminated, check error output
                _, stderr = server_process.communicate()
                raise Exception(f"Server failed to start: {stderr}")
            
            # Check if port is being listened on
            for proc in psutil.process_iter(['pid']):
                try:
                    for conn in proc.connections('inet'):
                        if conn.laddr.port == TEST_SERVER_PORT and conn.status == 'LISTEN':
                            print(f"Server started successfully on port {TEST_SERVER_PORT}")
                            return server_process
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error checking server status (attempt {attempt + 1}): {e}")
            if attempt == 4:  # Last attempt
                raise
    
    raise Exception("Server failed to start after multiple attempts")

def stop_test_server(server_process):
    """Stop the Flask test server"""
    if server_process:
        try:
            # Try graceful shutdown first
            if sys.platform == 'win32':
                server_process.terminate()
            else:
                server_process.send_signal(signal.SIGTERM)
            
            # Wait for up to 5 seconds for graceful shutdown
            for _ in range(10):
                if server_process.poll() is not None:
                    break
                time.sleep(0.5)
            
            # If still running, force kill
            if server_process.poll() is None:
                if sys.platform == 'win32':
                    server_process.kill()
                else:
                    server_process.send_signal(signal.SIGKILL)
            
            server_process.wait(timeout=5)  # Wait for process to fully terminate
            
            # Clean up any remaining processes on the port
            kill_process_on_port(TEST_SERVER_PORT)
        except Exception as e:
            print(f"Error stopping server: {e}")
