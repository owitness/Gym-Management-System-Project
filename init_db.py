import mysql.connector
from sshtunnel import SSHTunnelForwarder
import bcrypt
from config import DATABASE_CONFIG, SSH_CONFIG
from datetime import datetime, timedelta

def create_or_update_user(cursor, user_data):
    role, name, dob, email, password, address, city, state, zipcode, membership_expiry, auto_payment = user_data
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if not user:
        # Insert new user
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO users (role, name, dob, email, password, address, city, state, zipcode, membership_expiry, auto_payment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (role, name, dob, email, hashed_password, address, city, state, zipcode, membership_expiry, auto_payment))
        print(f"✅ Created new user: {email}")
        return cursor.lastrowid
    else:
        # Update existing user
        cursor.execute("""
            UPDATE users 
            SET role = %s, name = %s, dob = %s, address = %s, 
                city = %s, state = %s, zipcode = %s, 
                membership_expiry = %s, auto_payment = %s
            WHERE email = %s
        """, (role, name, dob, address, city, state, zipcode, membership_expiry, auto_payment, email))
        print(f"✅ Updated existing user: {email}")
        return user[0]

def create_or_update_membership(cursor, member_id):
    cursor.execute("SELECT id FROM memberships WHERE member_id = %s", (member_id,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO memberships (member_id, start_date, expiry_date, status)
            VALUES (%s, %s, %s, 'active')
        """, (member_id, datetime.now().date(), '2024-12-31'))
        print(f"✅ Created new membership for user ID: {member_id}")

def create_or_update_payment_method(cursor, member_id):
    cursor.execute("SELECT id FROM payment_methods WHERE user_id = %s", (member_id,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO payment_methods (user_id, card_number, exp, cvv, card_holder_name, saved)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """, (member_id, '4111111111111111', '2025-12-31', '123', 'Test User'))
        print(f"✅ Created new payment method for user ID: {member_id}")

def create_payment(cursor, member_id):
    cursor.execute("""
        INSERT INTO payments (user_id, amount, status, payment_method_id, membership_duration, membership_expiry)
        SELECT %s, 50.00, 'Completed', pm.id, 12, '2024-12-31'
        FROM payment_methods pm
        WHERE pm.user_id = %s
        AND NOT EXISTS (
            SELECT 1 FROM payments p 
            WHERE p.user_id = %s 
            AND DATE(p.transaction_date) = CURDATE()
        )
    """, (member_id, member_id, member_id))
    if cursor.rowcount > 0:
        print(f"✅ Created new payment for user ID: {member_id}")

def create_or_update_classes(cursor, trainer_id):
    class_times = [
        ('Morning Yoga', '08:00:00'),
        ('Afternoon HIIT', '14:00:00'),
        ('Evening Cardio', '18:00:00')
    ]
    
    for class_name, time in class_times:
        for day in range(30):
            class_date = datetime.now() + timedelta(days=day)
            class_datetime = datetime.strptime(f"{class_date.date()} {time}", "%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                INSERT INTO classes (class_name, trainer_id, schedule_time, capacity)
                SELECT %s, %s, %s, 20
                WHERE NOT EXISTS (
                    SELECT 1 FROM classes 
                    WHERE class_name = %s 
                    AND schedule_time = %s
                )
            """, (class_name, trainer_id, class_datetime, class_name, class_datetime))
            
    print("✅ Classes updated successfully!")

def create_attendance_records(cursor, member_id):
    for day in range(5):
        check_in = datetime.now() - timedelta(days=day, hours=8)
        check_out = check_in + timedelta(hours=2)
        
        cursor.execute("""
            INSERT INTO attendance (member_id, check_in_time, check_out_time)
            SELECT %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM attendance 
                WHERE member_id = %s 
                AND DATE(check_in_time) = DATE(%s)
            )
        """, (member_id, check_in, check_out, member_id, check_in))
        
    if cursor.rowcount > 0:
        print(f"✅ Created new attendance records for user ID: {member_id}")

def create_class_bookings(cursor, member_id):
    cursor.execute("""
        SELECT c.id FROM classes c
        LEFT JOIN class_bookings cb ON c.id = cb.class_id AND cb.member_id = %s
        WHERE cb.id IS NULL
        LIMIT 5
    """, (member_id,))
    
    available_classes = cursor.fetchall()
    for (class_id,) in available_classes:
        cursor.execute("""
            INSERT INTO class_bookings (member_id, class_id)
            VALUES (%s, %s)
        """, (member_id, class_id))
    
    if cursor.rowcount > 0:
        print(f"✅ Created new class bookings for user ID: {member_id}")

def init_database():
    tunnel = None
    try:
        # Establish SSH tunnel
        print("🔄 Setting up SSH tunnel...")
        tunnel = SSHTunnelForwarder(
            (SSH_CONFIG['ssh_host'], 22),
            ssh_username=SSH_CONFIG['ssh_username'],
            ssh_pkey=SSH_CONFIG['ssh_private_key'],
            remote_bind_address=SSH_CONFIG['remote_bind_address']
        )
        
        tunnel.start()
        print("✅ SSH tunnel established successfully!")

        # Connect to the database through the SSH tunnel
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            port=tunnel.local_bind_port,
            database=DATABASE_CONFIG['database']
        )
        cursor = conn.cursor()

        # Sample user data
        users_data = [
            ('admin', 'Admin User', '1990-01-01', 'admin@gym.com', 'admin123', '123 Admin St', 'Nashville', 'TN', '37201', None, False),
            ('trainer', 'John Trainer', '1985-05-15', 'trainer@gym.com', 'trainer123', '456 Fitness Ave', 'Nashville', 'TN', '37201', None, False),
            ('member', 'Jane Member', '1995-03-20', 'jane@email.com', 'member123', '789 Workout St', 'Nashville', 'TN', '37201', '2024-12-31', True),
            ('member', 'Bob Smith', '1988-07-12', 'bob@email.com', 'member123', '101 Exercise Rd', 'Nashville', 'TN', '37201', '2024-12-31', True),
            ('non_member', 'Guest User', '1992-11-30', 'guest@email.com', 'guest123', '202 Visit Lane', 'Nashville', 'TN', '37201', None, False)
        ]

        # Process each user and their related data
        print("🔄 Processing users and related data...")
        for user_data in users_data:
            conn.start_transaction()
            try:
                user_id = create_or_update_user(cursor, user_data)
                
                if user_data[0] == 'trainer':
                    trainer_id = user_id
                    create_or_update_classes(cursor, trainer_id)
                
                elif user_data[0] == 'member':
                    create_or_update_membership(cursor, user_id)
                    create_or_update_payment_method(cursor, user_id)
                    create_payment(cursor, user_id)
                    create_attendance_records(cursor, user_id)
                    create_class_bookings(cursor, user_id)
                
                conn.commit()
                print(f"✅ Successfully processed all data for user: {user_data[3]}")
                
            except Exception as e:
                conn.rollback()
                print(f"❌ Error processing user {user_data[3]}: {str(e)}")
                raise

        print("✅ Database initialization completed successfully!")

    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
        raise
    except Exception as e:
        print(f"❌ SSH Tunnel Error: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        if tunnel:
            print("🔄 Closing SSH tunnel...")
            tunnel.close()
            print("✅ SSH tunnel closed successfully!")

if __name__ == "__main__":
    init_database() 