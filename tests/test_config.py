import os
import subprocess
import time
import signal
import sys

# Test database configuration
TEST_DATABASE_CONFIG = {
    'host': 'gym-database.clqqsuqke2sz.us-east-2.rds.amazonaws.com',
    'user': 'root',
    'password': 'COSCAdmin',
    'database': 'gym_management',  # Use a separate test database
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
TEST_SERVER_URL = '18.191.239.86:5001'
TEST_API_URL = f'{TEST_SERVER_URL}/api'

# Test timeouts
<<<<<<< HEAD
WAIT_TIMEOUT = 10  # seconds 
=======
WAIT_TIMEOUT = 10  # seconds

def start_test_server():
    """Start the Flask test server"""
    try:
        # Kill any existing process on port 5001
        if sys.platform == 'win32':
            subprocess.run(['netstat', '-ano', '|', 'findstr', ':5001'], shell=True)
        else:
            subprocess.run(['lsof', '-ti:5001', '|', 'xargs', 'kill', '-9'], shell=True)
    except:
        pass

    # Start the Flask server using python3
    server_process = subprocess.Popen(
        ['python3', 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(2)
    return server_process

def stop_test_server(server_process):
    """Stop the Flask test server"""
    if server_process:
        server_process.terminate()
        server_process.wait() 
>>>>>>> 3a0f66f5666a61f5317685fe03f2d551d785f8de
