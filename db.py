import mysql.connector
from mysql.connector import Error
from config import DATABASE_CONFIG

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DATABASE_CONFIG['host'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            database=DATABASE_CONFIG['database'],
            port=DATABASE_CONFIG.get('port', 3306)
        )
        if connection.is_connected():
            print("Connected to MySQL database")
        return connection
    except Error as err:
        print("Error: ", err)
        return None

# For testing, you can add:
if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        conn.close()
