import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class Verifier:
    """Class for verifying email links using Selenium
    
    This class provides methods for visiting verification links
    and extracting API keys using a headless Chrome browser.
    """
    
    def __init__(self, headless=True):
        """Initialize the Verifier
        
        Args:
            headless (bool): Whether to run Chrome in headless mode
        """
        self.logger = logging.getLogger('gmail_verification.verifier')
        self.headless = headless
        self.driver = None
    
    def initialize_driver(self):
        """Initialize the Chrome WebDriver
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Setup Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            
            # Initialize the Chrome driver
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            self.logger.info("Chrome WebDriver initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing Chrome WebDriver: {str(e)}")
            return False
    
    def visit_verification_link(self, verification_link):
        """Visit a verification link
        
        Args:
            verification_link (str): The verification link to visit
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Make sure the driver is initialized
            if not self.driver:
                if not self.initialize_driver():
                    return False
            
            # Visit the verification link
            self.driver.get(verification_link)
            
            # Wait for the page to load
            wait = WebDriverWait(self.driver, 30)
            
            # Check if we're redirected to the dashboard
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Dashboard')]")))  # Adjust the selector as needed
                self.logger.info("Successfully verified email")
                return True
            except TimeoutException:
                self.logger.error("Timed out waiting for dashboard to load")
                return False
        
        except Exception as e:
            self.logger.error(f"Error visiting verification link: {str(e)}")
            return False
    
    def extract_api_key(self):
        """Extract the API key from the OpenRouter dashboard
        
        Returns:
            str: The API key or None if not found
        """
        try:
            # Make sure the driver is initialized
            if not self.driver:
                self.logger.error("Driver not initialized")
                return None
            
            # Navigate to the API keys page
            self.driver.get("https://openrouter.ai/keys")
            
            # Wait for the API keys page to load
            wait = WebDriverWait(self.driver, 30)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'API Keys')]")))  # Adjust the selector as needed
            
            # Find the API key
            api_key_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'api-key')]//code")  # Adjust the selector as needed
            api_key = api_key_element.text.strip()
            
            if api_key:
                self.logger.info("Successfully extracted API key")
                return api_key
            else:
                self.logger.error("API key element found but is empty")
                return None
        
        except NoSuchElementException:
            self.logger.error("Could not find API key element")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting API key: {str(e)}")
            return None
    
    def close(self):
        """Close the WebDriver
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("WebDriver closed successfully")
                return True
            return True
        except Exception as e:
            self.logger.error(f"Error closing WebDriver: {str(e)}")
            return False