import mysql.connector
from tests.test_config import TEST_DATABASE_CONFIG
import bcrypt
from db_connection import get_db

def setup_test_database():
    """Set up the test database and create necessary tables"""
    try:
        # Use the connection manager to get a connection through the SSH tunnel
        with get_db() as (conn, cursor):
            # Create test database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DATABASE_CONFIG['database']}")
            cursor.execute(f"USE {TEST_DATABASE_CONFIG['database']}")

            # Drop existing tables in the correct order to handle foreign key constraints
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("DROP TABLE IF EXISTS classes")
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'member', 'non_member') DEFAULT 'non_member',
                    dob DATE,
                    address VARCHAR(255),
                    city VARCHAR(255),
                    state VARCHAR(50),
                    zipcode VARCHAR(20),
                    membership_expiry DATETIME,
                    auto_payment BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    instructor_id INT,
                    schedule DATETIME,
                    capacity INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (instructor_id) REFERENCES users(id)
                )
            """)

            # Create test users
            from tests.test_config import TEST_USER, TEST_ADMIN

            # Hash passwords with consistent salt for testing
            salt = bcrypt.gensalt()
            test_user_pw = bcrypt.hashpw(TEST_USER['password'].encode('utf-8'), salt)
            test_admin_pw = bcrypt.hashpw(TEST_ADMIN['password'].encode('utf-8'), salt)

            # Insert test users
            cursor.execute("""
                INSERT INTO users (name, email, password, role, dob, address, city, state, zipcode, auto_payment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                TEST_USER['name'], TEST_USER['email'], test_user_pw, 'non_member',
                TEST_USER['dob'], TEST_USER['address'], TEST_USER['city'],
                TEST_USER['state'], TEST_USER['zipcode'], TEST_USER['auto_payment']
            ))

            cursor.execute("""
                INSERT INTO users (name, email, password, role, dob, address, city, state, zipcode, auto_payment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                TEST_ADMIN['name'], TEST_ADMIN['email'], test_admin_pw, 'admin',
                TEST_ADMIN['dob'], TEST_ADMIN['address'], TEST_ADMIN['city'],
                TEST_ADMIN['state'], TEST_ADMIN['zipcode'], TEST_ADMIN['auto_payment']
            ))

            conn.commit()
            print("✅ Test database setup completed successfully")
            return True

    except mysql.connector.Error as e:
        print(f"❌ Error setting up test database: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error setting up test database: {e}")
        return False

def cleanup_test_database():
    """Clean up the test database"""
    try:
        # Use the connection manager to get a connection through the SSH tunnel
        with get_db() as (conn, cursor):
            # Drop tables in the correct order
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("DROP TABLE IF EXISTS classes")
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.commit()
            print("✅ Test database cleanup completed successfully")
            return True

    except mysql.connector.Error as e:
        print(f"❌ Error cleaning up test database: {e}")
        return False

if __name__ == "__main__":
    # Test the setup and cleanup functions
    print("Setting up test database...")
    if setup_test_database():
        print("Test database setup successful")
    else:
        print("Test database setup failed")

    print("\nCleaning up test database...")
    if cleanup_test_database():
        print("Test database cleanup successful")
    else:
        print("Test database cleanup failed") 
