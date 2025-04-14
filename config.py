import os

# SSH Tunnel Configuration
SSH_CONFIG = {
    'ssh_host': 'ec2-18-191-239-86.us-east-2.compute.amazonaws.com',  # The SSH server hostname
    'ssh_username': 'ubuntu',  # SSH username
    'ssh_private_key': 'C:/Users/makennahockenberry/Downloads/main.pem',  # Path to your private key file
    'remote_bind_address': ('gym-database.clqqsuqke2sz.us-east-2.rds.amazonaws.com', 3306)  # RDS endpoint and port
}

# Database Configuration
DATABASE_CONFIG = {
    'host': 'gym-database.clqqsuqke2sz.us-east-2.rds.amazonaws.com',  # RDS endpoint
    'user': 'root',
    'password': 'COSCAdmin',
    'database': 'gym_management_test',
    'port': 3306
}

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-if-missing")