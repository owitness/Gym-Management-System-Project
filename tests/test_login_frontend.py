import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.test_config import TEST_SERVER_URL, TEST_USER, TEST_ADMIN, WAIT_TIMEOUT

class TestLoginFrontend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the webdriver before running tests"""
        cls.driver = webdriver.Chrome()  # Make sure ChromeDriver is in PATH
        cls.wait = WebDriverWait(cls.driver, WAIT_TIMEOUT)

    @classmethod
    def tearDownClass(cls):
        """Clean up the webdriver after running tests"""
        cls.driver.quit()

    def setUp(self):
        """Set up test environment before each test"""
        self.driver.get(f"{TEST_SERVER_URL}/signin")

    def test_successful_login(self):
        """Test successful login with valid credentials"""
        # Find and fill in email field
        email_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_field.send_keys(TEST_USER["email"])

        # Find and fill in password field
        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys(TEST_USER["password"])

        # Click login button
        login_button = self.driver.find_element(By.ID, "login-button")
        login_button.click()

        # Wait for successful login and redirect
        try:
            self.wait.until(
                EC.url_contains("/dashboard")
            )
        except TimeoutException:
            self.fail("Login failed or redirect did not occur")

    def test_admin_login(self):
        """Test successful login with admin credentials"""
        # Find and fill in email field
        email_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_field.send_keys(TEST_ADMIN["email"])

        # Find and fill in password field
        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys(TEST_ADMIN["password"])

        # Click login button
        login_button = self.driver.find_element(By.ID, "login-button")
        login_button.click()

        # Wait for successful login and redirect to admin dashboard
        try:
            self.wait.until(
                EC.url_contains("/admin")
            )
        except TimeoutException:
            self.fail("Admin login failed or redirect did not occur")

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Find and fill in email field
        email_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_field.send_keys(TEST_USER["email"])

        # Find and fill in password field with wrong password
        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys("wrongpassword")

        # Click login button
        login_button = self.driver.find_element(By.ID, "login-button")
        login_button.click()

        # Wait for error message
        try:
            error_message = self.wait.until(
                EC.presence_of_element_located((By.ID, "error-message"))
            )
            self.assertIn("Invalid email or password", error_message.text)
        except TimeoutException:
            self.fail("Error message did not appear")

    def test_empty_fields(self):
        """Test login with empty fields"""
        # Click login button without entering credentials
        login_button = self.wait.until(
            EC.presence_of_element_located((By.ID, "login-button"))
        )
        login_button.click()

        # Wait for error message
        try:
            error_message = self.wait.until(
                EC.presence_of_element_located((By.ID, "error-message"))
            )
            self.assertIn("Please enter both email and password", error_message.text)
        except TimeoutException:
            self.fail("Error message did not appear")

    def test_remember_me(self):
        """Test remember me functionality"""
        # Find and fill in email field
        email_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_field.send_keys(TEST_USER["email"])

        # Find and fill in password field
        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys(TEST_USER["password"])

        # Check remember me checkbox
        remember_me = self.driver.find_element(By.ID, "remember-me")
        remember_me.click()

        # Click login button
        login_button = self.driver.find_element(By.ID, "login-button")
        login_button.click()

        # Wait for successful login
        try:
            self.wait.until(
                EC.url_contains("/dashboard")
            )
        except TimeoutException:
            self.fail("Login failed or redirect did not occur")

        # Check if token is stored in localStorage
        token = self.driver.execute_script("return localStorage.getItem('token');")
        self.assertIsNotNone(token)

    def test_logout(self):
        """Test logout functionality"""
        # Login first
        self.test_successful_login()

        # Find and click logout button
        logout_button = self.wait.until(
            EC.presence_of_element_located((By.ID, "logout-button"))
        )
        logout_button.click()

        # Wait for redirect to login page
        try:
            self.wait.until(
                EC.url_contains("/signin")
            )
        except TimeoutException:
            self.fail("Logout failed or redirect did not occur")

        # Check if token is removed from localStorage
        token = self.driver.execute_script("return localStorage.getItem('token');")
        self.assertIsNone(token)

if __name__ == '__main__':
    unittest.main() 