import os

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
TEST_SERVER_URL = 'http://localhost:5001'
TEST_API_URL = f'{TEST_SERVER_URL}/api'

# Test timeouts
WAIT_TIMEOUT = 10  # seconds 
