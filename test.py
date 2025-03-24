import mysql.connector
from config import DATABASE_CONFIG

print("🔄 Attempting to connect to AWS RDS via Python...")

try:
    conn = mysql.connector.connect(
        host=DATABASE_CONFIG["host"],
        user=DATABASE_CONFIG["user"],
        password=DATABASE_CONFIG["password"],
        database=DATABASE_CONFIG["database"],
        port=DATABASE_CONFIG["port"]
    )
    
    if conn.is_connected():
        print("✅ Successfully connected to MySQL RDS!")
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES;")
        for db in cursor.fetchall():
            print(f"📌 Found database: {db}")
        cursor.close()
        conn.close()
    else:
        print("❌ Connection failed!")
except mysql.connector.Error as e:
    print(f"❌ MySQL Error: {e}")
