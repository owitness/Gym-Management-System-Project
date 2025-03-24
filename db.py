import mysql.connector
from config import DATABASE_CONFIG

def get_db_connection():
    try:
        print("🔄 Attempting to connect to the database...")  # Debugging message

        conn = mysql.connector.connect(
            host=DATABASE_CONFIG['host'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            database=DATABASE_CONFIG['database'],
            port=DATABASE_CONFIG['port']
        )

        if conn.is_connected():
            print("✅ Database Connection Successful!")
            return conn
        else:
            print("❌ Database connection failed!")
            return None

    except mysql.connector.Error as e:
        print(f"❌ Database Error: {e}")  # Print specific error message
        return None

if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        print("✅ Test: Connection to database works!")
    else:
        print("❌ Test: Database connection failed!")
