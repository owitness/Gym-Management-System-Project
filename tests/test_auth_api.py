import unittest
import json
import requests
from tests.test_config import TEST_SERVER_URL, TEST_API_URL, TEST_USER, TEST_ADMIN
from tests.test_db import setup_test_database, cleanup_test_database

class TestAuthAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database before running tests"""
        print("\nSetting up test database...")
        if not setup_test_database():
            raise Exception("Failed to set up test database")

    @classmethod
    def tearDownClass(cls):
        """Clean up test database after running tests"""
        print("\nCleaning up test database...")
        cleanup_test_database()

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

        # Make multiple failed login attempts
        for _ in range(6):  # Should hit rate limit after 5 attempts
            response = requests.post(
                f"{self.api_url}/login",
                json=login_data
            )

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

if __name__ == '__main__':
    unittest.main() 