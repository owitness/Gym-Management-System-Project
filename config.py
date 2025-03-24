import os

DATABASE_CONFIG = {
    'host': 'gym-database.clqqsuqke2sz.us-east-2.rds.amazonaws.com',
    'user': 'root',
    'password': 'COSCAdmin',
    'database': 'gym_management',
    'port': 3306
}

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-if-missing")