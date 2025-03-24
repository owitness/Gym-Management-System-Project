import unittest
import json
from app import app
from db import get_db_connection
import bcrypt
import datetime

class TestAuthSystem(unittest.TestCase):
    def setUp(self):
        """Set up test client and test database connection"""
        self.app = app.test_client()
        self.app.testing = True
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        
        # Create test user
        self.test_user = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "dob": "1990-01-01",
            "address": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zipcode": "12345",
            "auto_payment": False
        }
        
        # Hash password for test user
        hashed_pw = bcrypt.hashpw(self.test_user["password"].encode("utf-8"), bcrypt.gensalt())
        
        # Insert test user into database
        self.cursor.execute("""
            INSERT INTO users (name, email, password, role, dob, address, city, state, zipcode, auto_payment, created_at)
            VALUES (%s, %s, %s, 'non_member', %s, %s, %s, %s, %s, %s, NOW())
        """, (
            self.test_user["name"],
            self.test_user["email"],
            hashed_pw,
            self.test_user["dob"],
            self.test_user["address"],
            self.test_user["city"],
            self.test_user["state"],
            self.test_user["zipcode"],
            self.test_user["auto_payment"]
        ))
        self.conn.commit()

    def tearDown(self):
        """Clean up test data"""
        self.cursor.execute("DELETE FROM users WHERE email = %s", (self.test_user["email"],))
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def test_user_registration(self):
        """Test user registration endpoint"""
        # Test successful registration
        new_user = {
            "name": "New User",
            "email": "new@example.com",
            "password": "newpassword123",
            "dob": "1995-01-01",
            "address": "456 New St",
            "city": "New City",
            "state": "NS",
            "zipcode": "67890",
            "auto_payment": True
        }
        
        response = self.app.post('/api/register',
                               data=json.dumps(new_user),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("message", data)
        
        # Test duplicate email registration
        response = self.app.post('/api/register',
                               data=json.dumps(new_user),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_user_login(self):
        """Test user login endpoint"""
        # Test successful login
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        response = self.app.post('/api/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("token", data)
        self.assertIn("role", data)
        self.assertEqual(data["role"], "non_member")
        
        # Test invalid password
        login_data["password"] = "wrongpassword"
        response = self.app.post('/api/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("error", data)
        
        # Test non-existent email
        login_data["email"] = "nonexistent@example.com"
        login_data["password"] = self.test_user["password"]
        response = self.app.post('/api/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_membership_expiry(self):
        """Test membership expiry functionality"""
        # Update test user to member with expired membership
        expiry_date = datetime.datetime.now() - datetime.timedelta(days=1)
        self.cursor.execute("""
            UPDATE users 
            SET role = 'member', membership_expiry = %s 
            WHERE email = %s
        """, (expiry_date, self.test_user["email"]))
        self.conn.commit()
        
        # Try to login
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        response = self.app.post('/api/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["role"], "non_member")  # Should be downgraded to non_member

    def test_user_profile(self):
        """Test user profile endpoint"""
        # Login first to get token
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        response = self.app.post('/api/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        token = json.loads(response.data)["token"]
        
        # Test profile endpoint
        response = self.app.get('/api/profile',
                              headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["email"], self.test_user["email"])
        self.assertEqual(data["name"], self.test_user["name"])
        self.assertNotIn("password", data)  # Password should not be in response

    def test_role_update(self):
        """Test admin role update functionality"""
        # Create admin user
        admin_user = {
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "adminpassword123",
            "dob": "1980-01-01",
            "address": "789 Admin St",
            "city": "Admin City",
            "state": "AS",
            "zipcode": "11111",
            "auto_payment": False
        }
        
        hashed_pw = bcrypt.hashpw(admin_user["password"].encode("utf-8"), bcrypt.gensalt())
        
        self.cursor.execute("""
            INSERT INTO users (name, email, password, role, dob, address, city, state, zipcode, auto_payment, created_at)
            VALUES (%s, %s, %s, 'admin', %s, %s, %s, %s, %s, %s, NOW())
        """, (
            admin_user["name"],
            admin_user["email"],
            hashed_pw,
            admin_user["dob"],
            admin_user["address"],
            admin_user["city"],
            admin_user["state"],
            admin_user["zipcode"],
            admin_user["auto_payment"]
        ))
        self.conn.commit()
        
        # Login as admin
        login_data = {
            "email": admin_user["email"],
            "password": admin_user["password"]
        }
        
        response = self.app.post('/api/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        admin_token = json.loads(response.data)["token"]
        
        # Test role update
        update_data = {"role": "member"}
        response = self.app.put(f'/api/users/{self.test_user["id"]}/role',
                              data=json.dumps(update_data),
                              content_type='application/json',
                              headers={'Authorization': f'Bearer {admin_token}'})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify role was updated
        self.cursor.execute("SELECT role FROM users WHERE email = %s", (self.test_user["email"],))
        updated_role = self.cursor.fetchone()[0]
        self.assertEqual(updated_role, "member")

if __name__ == '__main__':
    unittest.main() 