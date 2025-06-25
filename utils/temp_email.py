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

class TempEmailAutomation:
    """Automates the process of creating temporary emails and OpenRouter accounts"""
    
    def __init__(self, config_manager):
        """Initialize the TempEmailAutomation
        
        Args:
            config_manager (ConfigManager): The configuration manager
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger('ai_dashboard.temp_email')
        self.config = config_manager.get_config()
        self.temp_email_service = self.config['temp_email']['service']
        self.headless = self.config['temp_email']['headless']
    
    def start_automation(self):
        """Start the automation process
        
        Returns:
            str: Message indicating the result of the automation
        """
        try:
            # Setup Chrome driver
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            
            # Initialize the Chrome driver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Get a temporary email
            email = self._get_temp_email(driver)
            if not email:
                driver.quit()
                return "Failed to get temporary email"
            
            # Sign up for OpenRouter
            api_key = self._signup_openrouter(driver, email)
            if not api_key:
                driver.quit()
                return "Failed to sign up for OpenRouter"
            
            # Add the API key to the config
            from utils.key_rotator import KeyRotator
            key_rotator = KeyRotator(self.config_manager)
            result = key_rotator.add_key(api_key)
            
            # Close the browser
            driver.quit()
            
            return f"Successfully created new OpenRouter account with email {email} and added API key"
        
        except Exception as e:
            self.logger.error(f"Error in temp email automation: {str(e)}")
            return f"Error in temp email automation: {str(e)}"
    
    def _get_temp_email(self, driver):
        """Get a temporary email address
        
        Args:
            driver (WebDriver): The Selenium WebDriver instance
            
        Returns:
            str: The temporary email address or None if failed
        """
        try:
            # Navigate to the temp email service
            if self.temp_email_service == 'temp-mail.org':
                driver.get("https://temp-mail.org/en/")
                
                # Wait for the email to be generated
                wait = WebDriverWait(driver, 30)
                email_element = wait.until(EC.presence_of_element_located((By.ID, "mail")))
                
                # Get the email address
                email = email_element.get_attribute("value")
                self.logger.info(f"Generated temporary email: {email}")
                
                return email
            else:
                self.logger.error(f"Unsupported temp email service: {self.temp_email_service}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting temporary email: {str(e)}")
            return None
    
    def _signup_openrouter(self, driver, email):
        """Sign up for OpenRouter using the temporary email
        
        Args:
            driver (WebDriver): The Selenium WebDriver instance
            email (str): The temporary email address
            
        Returns:
            str: The OpenRouter API key or None if failed
        """
        try:
            # Navigate to OpenRouter signup page
            driver.get("https://openrouter.ai/signup")
            
            # Wait for the signup form to load
            wait = WebDriverWait(driver, 30)
            
            # Fill in the email field
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_field.clear()
            email_field.send_keys(email)
            
            # Click the signup button
            signup_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign up')]")))  # Adjust the selector as needed
            signup_button.click()
            
            # Wait for confirmation that the email has been sent
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Check your email')]")))  # Adjust the selector as needed
            
            # Go back to the temp email site to get the confirmation link
            driver.get("https://temp-mail.org/en/")
            
            # Wait for the email to arrive (this might take some time)
            wait = WebDriverWait(driver, 120)  # Longer timeout for email arrival
            
            # Look for the OpenRouter email in the inbox
            openrouter_email = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'mail-item')]//div[contains(text(), 'OpenRouter')]")
            ))
            openrouter_email.click()
            
            # Wait for the email content to load
            wait.until(EC.presence_of_element_located((By.ID, "mail-content")))  # Adjust the selector as needed
            
            # Find the confirmation link in the email
            confirmation_link = driver.find_element(By.XPATH, "//a[contains(@href, 'openrouter.ai/verify')]")
            confirmation_url = confirmation_link.get_attribute("href")
            
            # Navigate to the confirmation link
            driver.get(confirmation_url)
            
            # Wait for the dashboard to load after confirmation
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Dashboard')]")))  # Adjust the selector as needed
            
            # Navigate to the API keys page
            driver.get("https://openrouter.ai/keys")
            
            # Wait for the API keys page to load
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'API Keys')]")))  # Adjust the selector as needed
            
            # Find the API key
            api_key_element = driver.find_element(By.XPATH, "//div[contains(@class, 'api-key')]//code")  # Adjust the selector as needed
            api_key = api_key_element.text.strip()
            
            self.logger.info(f"Successfully signed up for OpenRouter with email {email}")
            return api_key
        
        except Exception as e:
            self.logger.error(f"Error signing up for OpenRouter: {str(e)}")
            return None