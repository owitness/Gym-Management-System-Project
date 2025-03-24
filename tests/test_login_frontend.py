import unittest
import os
import tempfile
import time
import psutil
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.test_config import (
    TEST_SERVER_URL, TEST_USER, TEST_ADMIN, WAIT_TIMEOUT,
    start_test_server, stop_test_server
)

def kill_chrome_processes():
    """Kill any existing Chrome processes"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()
                proc.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            pass

class TestLoginFrontend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the webdriver and test server before running tests"""
        # Kill any existing Chrome processes
        kill_chrome_processes()
        
        # Start the test server
        print("\nStarting test server...")
        cls.server_process = start_test_server()
        
        # Create a unique temporary directory for Chrome profile
        timestamp = int(time.time())
        cls.temp_dir = tempfile.mkdtemp(prefix=f'chrome_profile_{timestamp}_')
        
        try:
            # Configure Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument(f'--user-data-dir={cls.temp_dir}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--remote-debugging-port=0')  # Use random port
            
            # Initialize WebDriver with options
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.wait = WebDriverWait(cls.driver, WAIT_TIMEOUT)
        except Exception as e:
            # Clean up on failure
            cls.cleanup()
            raise e

    @classmethod
    def cleanup(cls):
        """Clean up resources"""
        try:
            if hasattr(cls, 'driver'):
                cls.driver.quit()
        except:
            pass
            
        try:
            if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
                shutil.rmtree(cls.temp_dir, ignore_errors=True)
        except:
            pass
            
        try:
            if hasattr(cls, 'server_process'):
                stop_test_server(cls.server_process)
        except:
            pass
            
        kill_chrome_processes()

    @classmethod
    def tearDownClass(cls):
        """Clean up after running tests"""
        cls.cleanup()

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