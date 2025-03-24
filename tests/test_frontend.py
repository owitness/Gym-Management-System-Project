import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

class TestLoginFrontend(unittest.TestCase):
    def setUp(self):
        """Set up the webdriver"""
        self.driver = webdriver.Chrome()  # Make sure you have ChromeDriver installed
        self.driver.get("http://localhost:5001/login")
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        """Clean up after each test"""
        self.driver.quit()

    def test_successful_login(self):
        """Test successful login flow"""
        # Fill in login form
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = self.driver.find_element(By.ID, "password")
        
        email_input.send_keys("test@example.com")
        password_input.send_keys("testpassword123")
        
        # Submit form
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for redirect and verify we're on the dashboard
        try:
            self.wait.until(EC.url_contains("/dashboard"))
            # Verify we're not on the login page
            self.assertNotIn("/login", self.driver.current_url)
        except TimeoutException:
            self.fail("Login failed or redirect didn't happen")

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Fill in login form with wrong credentials
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = self.driver.find_element(By.ID, "password")
        
        email_input.send_keys("wrong@example.com")
        password_input.send_keys("wrongpassword")
        
        # Submit form
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Verify error message appears
        try:
            error_message = self.wait.until(
                EC.presence_of_element_located((By.ID, "error-message"))
            )
            self.assertTrue(error_message.is_displayed())
            self.assertIn("Invalid email or password", error_message.text)
        except TimeoutException:
            self.fail("Error message didn't appear")

    def test_empty_fields(self):
        """Test login with empty fields"""
        # Submit form without filling in fields
        submit_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']")))
        submit_button.click()
        
        # Verify we're still on the login page
        self.assertIn("/login", self.driver.current_url)

    def test_signup_link(self):
        """Test signup link functionality"""
        # Find and click signup link
        signup_link = self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign up")))
        signup_link.click()
        
        # Verify we're redirected to signup page
        try:
            self.wait.until(EC.url_contains("/signup"))
        except TimeoutException:
            self.fail("Redirect to signup page didn't happen")

    def test_admin_login(self):
        """Test admin login flow"""
        # Fill in login form with admin credentials
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = self.driver.find_element(By.ID, "password")
        
        email_input.send_keys("admin@example.com")
        password_input.send_keys("adminpassword123")
        
        # Submit form
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for redirect and verify we're on the admin dashboard
        try:
            self.wait.until(EC.url_contains("/admin/dashboard"))
        except TimeoutException:
            self.fail("Admin login failed or redirect didn't happen")

if __name__ == '__main__':
    unittest.main() 