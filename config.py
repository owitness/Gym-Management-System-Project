import os
import sys

# Dynamically get the path to the PEM file based on the current user's home directory
user_home = os.path.expanduser("~")
pem_path = os.path.join(user_home, "Downloads", "main.pem")

# Check if the PEM file exists
if not os.path.isfile(pem_path):
    print(f"[ERROR] PEM file not found at: {pem_path}")
    sys.exit(1)  # Exit the program if the PEM file is missing

# SSH Tunnel Configuration
SSH_CONFIG = {
    'ssh_host': 'ec2-18-191-239-86.us-east-2.compute.amazonaws.com',  # The SSH server hostname
    'ssh_username': 'ubuntu',  # SSH username
    'ssh_private_key': pem_path,  # Path to your private key file
    'remote_bind_address': ('gym-database.clqqsuqke2sz.us-east-2.rds.amazonaws.com', 3306)  # RDS endpoint and port
}

# Database Configuration
DATABASE_CONFIG = {
    'host': 'gym-database.clqqsuqke2sz.us-east-2.rds.amazonaws.com',
    'user': 'root',
    'password': 'COSCAdmin',
    'database': 'gym_management_test',
    'port': 3306
}

# Secret key for JWT and Flask sessions
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-if-missing")
