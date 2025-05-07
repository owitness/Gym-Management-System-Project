import os
from dotenv import load_dotenv

load_dotenv()

# SSH Tunnel Configuration
SSH_CONFIG = {
    'ssh_host': os.getenv('SSH_HOST', ''),
    'ssh_username': os.getenv('SSH_USERNAME', ''),
    'ssh_private_key': os.getenv('SSH_KEY_PATH', ''),
    'remote_bind_address': (os.getenv('REMOTE_HOST', ''), int(os.getenv('REMOTE_PORT', '3306')))
}

# Database Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DATABASE_HOST', ''),
    'user': os.getenv('DATABASE_USER', ''),
    'password': os.getenv('DATABASE_PASSWORD', ''),
    'database': os.getenv('DATABASE_NAME', ''),
    'port': int(os.getenv('DATABASE_PORT', '3306'))
}

# Secret key for JWT and Flask sessions
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application") 