import unittest
import json
import requests
from tests.test_config import (
    TEST_SERVER_URL, TEST_API_URL, TEST_USER, TEST_ADMIN,
    start_test_server, stop_test_server
)
from tests.test_db import setup_test_database, cleanup_test_database
import time

class TestAuthAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database and ensure server is running before running tests"""
        print("\nSetting up test database...")
        if not setup_test_database():
            raise Exception("Failed to set up test database")
            
        # Start the test server
        print("\nStarting test server...")
        cls.server_process = start_test_server()
            
        # Wait for server to be ready
        max_retries = 5
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{TEST_SERVER_URL}/health")
                if response.status_code == 200:
                    print("Server is ready")
                    break
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    print(f"Server not ready, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise Exception("Server failed to start after maximum retries")

    @classmethod
    def tearDownClass(cls):
        """Clean up test database and stop server after running tests"""
        print("\nCleaning up test database...")
        cleanup_test_database()
        
        print("\nStopping test server...")
        stop_test_server(cls.server_process)

    def setUp(self):
        """Set up test environment before each test"""
        self.api_url = TEST_API_URL
        self.test_user = TEST_USER
        self.test_admin = TEST_ADMIN

    def test_user_registration(self):
        """Test user registration endpoint"""
        # Test successful registration
        new_user = {
            "name": "New Test User",
            "email": "newtest@example.com",
            "password": "NewTestPass123",
            "dob": "1995-01-01",
            "address": "789 New St",
            "city": "New City",
            "state": "NS",
            "zipcode": "54321",
            "auto_payment": True
        }

        response = requests.post(
            f"{self.api_url}/register",
            json=new_user
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("message", data)

        # Test duplicate email registration
        response = requests.post(
            f"{self.api_url}/register",
            json=new_user
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_user_login(self):
        """Test user login endpoint"""
        # Test successful login with regular user
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }

        response = requests.post(
            f"{self.api_url}/login",
            json=login_data
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertIn("role", data)
        self.assertEqual(data["role"], "non_member")

        # Test successful login with admin
        admin_login_data = {
            "email": self.test_admin["email"],
            "password": self.test_admin["password"]
        }

        response = requests.post(
            f"{self.api_url}/login",
            json=admin_login_data
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertIn("role", data)
        self.assertEqual(data["role"], "admin")

        # Test invalid password
        login_data["password"] = "wrongpassword"
        response = requests.post(
            f"{self.api_url}/login",
            json=login_data
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

        # Test non-existent email
        login_data["email"] = "nonexistent@example.com"
        login_data["password"] = self.test_user["password"]
        response = requests.post(
            f"{self.api_url}/login",
            json=login_data
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

    def test_rate_limiting(self):
        """Test rate limiting on login endpoint"""
        login_data = {
            "email": self.test_user["email"],
            "password": "wrongpassword"
        }

        # Make multiple failed login attempts with delay
        for _ in range(6):  # Should hit rate limit after 5 attempts
            response = requests.post(
                f"{self.api_url}/login",
                json=login_data
            )
            time.sleep(1)  # Add 1 second delay between attempts

        self.assertEqual(response.status_code, 429)
        data = response.json()
        self.assertIn("error", data)

    def test_user_profile(self):
        """Test user profile endpoint"""
        # Login first to get token
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }

        response = requests.post(
            f"{self.api_url}/login",
            json=login_data
        )

        token = response.json()["token"]

        # Test profile endpoint with token
        response = requests.get(
            f"{self.api_url}/profile",
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.test_user["email"])
        self.assertEqual(data["name"], self.test_user["name"])
        self.assertNotIn("password", data)

        # Test profile endpoint without token
        response = requests.get(f"{self.api_url}/profile")
        self.assertEqual(response.status_code, 401)

    def test_invalid_token(self):
        """Test profile endpoint with invalid token"""
        response = requests.get(
            f"{self.api_url}/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

    def test_missing_token(self):
        """Test profile endpoint with missing token"""
        response = requests.get(f"{self.api_url}/profile")
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

    def test_role_update(self):
        """Test admin role update functionality"""
        # Login as admin
        login_data = {
            "email": self.test_admin["email"],
            "password": self.test_admin["password"]
        }

        response = requests.post(
            f"{self.api_url}/login",
            json=login_data
        )

        admin_token = response.json()["token"]

        # Get test user ID
        response = requests.get(
            f"{self.api_url}/profile",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        test_user_id = response.json()["id"]

        # Test role update
        update_data = {"role": "member"}
        response = requests.put(
            f"{self.api_url}/users/{test_user_id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )

        self.assertEqual(response.status_code, 200)

        # Verify role was updated
        response = requests.get(
            f"{self.api_url}/profile",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(response.json()["role"], "member")

    def test_role_update_unauthorized(self):
        """Test role update without admin privileges"""
        # Login as regular user
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        response = requests.post(
            f"{self.api_url}/login",
            json=login_data
        )
        user_token = response.json()["token"]

        # Try to update role without admin privileges
        update_data = {"role": "member"}
        response = requests.put(
            f"{self.api_url}/users/1/role",
            headers={"Authorization": f"Bearer {user_token}"},
            json=update_data
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)

    def test_role_update_invalid_role(self):
        """Test role update with invalid role"""
        # Login as admin
        login_data = {
            "email": self.test_admin["email"],
            "password": self.test_admin["password"]
        }
        response = requests.post(
            f"{self.api_url}/login",
            json=login_data
        )
        admin_token = response.json()["token"]

        # Try to update role with invalid role
        update_data = {"role": "invalid_role"}
        response = requests.put(
            f"{self.api_url}/users/1/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_role_update_nonexistent_user(self):
        """Test role update for nonexistent user"""
        # Login as admin
        login_data = {
            "email": self.test_admin["email"],
            "password": self.test_admin["password"]
        }
        response = requests.post(
            f"{self.api_url}/login",
            json=login_data
        )
        admin_token = response.json()["token"]

        # Try to update role for nonexistent user
        update_data = {"role": "member"}
        response = requests.put(
            f"{self.api_url}/users/999999/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)

if __name__ == '__main__':
    unittest.main() 