import mysql.connector
from tests.test_config import TEST_DATABASE_CONFIG
import bcrypt

def setup_test_database():
    """Set up the test database and create necessary tables"""
    try:
        # Connect to MySQL without selecting a database
        conn = mysql.connector.connect(
            host=TEST_DATABASE_CONFIG['host'],
            user=TEST_DATABASE_CONFIG['user'],
            password=TEST_DATABASE_CONFIG['password'],
            port=TEST_DATABASE_CONFIG['port']
        )
        cursor = conn.cursor()

        # Create test database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DATABASE_CONFIG['database']}")
        cursor.execute(f"USE {TEST_DATABASE_CONFIG['database']}")

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

        # Create test users
        from tests.test_config import TEST_USER, TEST_ADMIN

        # Hash passwords
        test_user_pw = bcrypt.hashpw(TEST_USER['password'].encode('utf-8'), bcrypt.gensalt())
        test_admin_pw = bcrypt.hashpw(TEST_ADMIN['password'].encode('utf-8'), bcrypt.gensalt())

        # Insert test users
        cursor.execute("""
            INSERT INTO users (name, email, password, role, dob, address, city, state, zipcode, auto_payment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            password = VALUES(password),
            role = VALUES(role),
            dob = VALUES(dob),
            address = VALUES(address),
            city = VALUES(city),
            state = VALUES(state),
            zipcode = VALUES(zipcode),
            auto_payment = VALUES(auto_payment)
        """, (
            TEST_USER['name'], TEST_USER['email'], test_user_pw, 'non_member',
            TEST_USER['dob'], TEST_USER['address'], TEST_USER['city'],
            TEST_USER['state'], TEST_USER['zipcode'], TEST_USER['auto_payment']
        ))

        cursor.execute("""
            INSERT INTO users (name, email, password, role, dob, address, city, state, zipcode, auto_payment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            password = VALUES(password),
            role = VALUES(role),
            dob = VALUES(dob),
            address = VALUES(address),
            city = VALUES(city),
            state = VALUES(state),
            zipcode = VALUES(zipcode),
            auto_payment = VALUES(auto_payment)
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
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def cleanup_test_database():
    """Clean up the test database"""
    try:
        conn = mysql.connector.connect(
            host=TEST_DATABASE_CONFIG['host'],
            user=TEST_DATABASE_CONFIG['user'],
            password=TEST_DATABASE_CONFIG['password'],
            port=TEST_DATABASE_CONFIG['port']
        )
        cursor = conn.cursor()

        # Drop the test database
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DATABASE_CONFIG['database']}")
        conn.commit()
        print("✅ Test database cleanup completed successfully")
        return True

    except mysql.connector.Error as e:
        print(f"❌ Error cleaning up test database: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

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