import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from utils.APIError import APIError

class TempEmailAutomation:
    """Service for automating the creation of temporary email accounts
    
    This class provides methods for automating the process of creating a
    temporary email account, signing up for OpenRouter, and retrieving the
    generated API key.
    """
    
    def __init__(self, config_manager, key_rotator):
        """Initialize the TempEmailAutomation
        
        Args:
            config_manager (ConfigManager): The configuration manager
            key_rotator (KeyRotator): The key rotation service
        """
        self.logger = logging.getLogger('ai_dashboard.temp_email')
        self.config_manager = config_manager
        self.key_rotator = key_rotator
        self.driver = None
    
    def start_automation(self):
        """Start the automation process
        
        This method orchestrates the process of getting a temporary email,
        signing up for OpenRouter, and adding the generated API key.
        
        Returns:
            str: A message indicating the result of the automation
            
        Raises:
            APIError: If the automation fails
        """
        try:
            # Initialize the WebDriver
            self._init_driver()
            
            # Get email from config or use temporary email
            config = self.config_manager.get_config()
            email = config.get('temp_email', {}).get('user_email')
            
            if not email:
                # Fall back to temporary email if user email not provided
                email = self._get_temp_email()
                self.logger.info(f"Got temporary email: {email}")
            else:
                self.logger.info(f"Using configured email: {email}")
            
            # Sign up for OpenRouter
            api_key = self._signup_openrouter(email)
            self.logger.info(f"Got OpenRouter API key: {api_key}")
            
            # Add the API key
            result = self.key_rotator.add_key(api_key)
            self.logger.info(f"Added OpenRouter API key: {result}")
            
            # Close the WebDriver
            self._close_driver()
            
            return f"Successfully created new OpenRouter account with email {email}"
        except Exception as e:
            self.logger.error(f"Error in temp email automation: {str(e)}")
            # Make sure to close the driver on error
            self._close_driver()
            raise APIError(f"Failed to create temp email: {str(e)}", 500)
    
    def _init_driver(self):
        """Initialize the WebDriver
        
        Raises:
            Exception: If the WebDriver initialization fails
        """
        try:
            # Get the headless setting from the configuration
            config = self.config_manager.get_config()
            headless = config.get('temp_email', {}).get('headless', True)
            
            # Set up Chrome options
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Initialize the WebDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            self.logger.info("Initialized WebDriver")
        except Exception as e:
            self.logger.error(f"Error initializing WebDriver: {str(e)}")
            raise Exception(f"Failed to initialize WebDriver: {str(e)}")
    
    def _close_driver(self):
        """Close the WebDriver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("Closed WebDriver")
        except Exception as e:
            self.logger.error(f"Error closing WebDriver: {str(e)}")
    
    def _get_temp_email(self):
        """Get a temporary email address
        
        Returns:
            str: The temporary email address
            
        Raises:
            Exception: If getting the temporary email fails
        """
        try:
            # Navigate to temp-mail.org
            self.driver.get('https://temp-mail.org/')
            
            # Wait for the email to be generated
            wait = WebDriverWait(self.driver, 30)
            email_element = wait.until(
                EC.presence_of_element_located((By.ID, 'mail'))
            )
            
            # Get the email address
            email = email_element.get_attribute('value')
            
            if not email:
                raise Exception("Failed to get temporary email")
            
            return email
        except Exception as e:
            self.logger.error(f"Error getting temporary email: {str(e)}")
            raise Exception(f"Failed to get temporary email: {str(e)}")
    
    def _signup_openrouter(self, email):
        """Sign up for OpenRouter
        
        Args:
            email (str): The email address to use for signup
            
        Returns:
            str: The generated API key
            
        Raises:
            Exception: If the signup process fails
        """
        try:
            # Navigate to OpenRouter signup page
            self.driver.get('https://openrouter.ai/auth/signup')
            
            # Wait for the email input field
            wait = WebDriverWait(self.driver, 30)
            email_input = wait.until(
                EC.presence_of_element_located((By.ID, 'email'))
            )
            
            # Enter the email address
            email_input.clear()
            email_input.send_keys(email)
            
            # Click the signup button
            signup_button = self.driver.find_element(By.XPATH, '//button[contains(text(), "Sign up")]')
            signup_button.click()
            
            # Wait for the confirmation message
            wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Check your email")]'))
            )
            
            # Check if we're using a temporary email or user's email
            config = self.config_manager.get_config()
            user_email = config.get('temp_email', {}).get('user_email')
            
            if email == user_email:
                # If using user's email, prompt for manual verification
                self.logger.info("Please check your email and verify your account manually.")
                print("\n\n===========================================================")
                print(f"IMPORTANT: Please check {email} for the verification link")
                print("After verifying, press Enter to continue...")
                print("===========================================================\n\n")
                input()
                
                # Navigate directly to the dashboard
                self.driver.get('https://openrouter.ai/dashboard')
            else:
                # Using temporary email, continue with automated process
                # Go back to temp-mail.org to get the confirmation link
                self.driver.get('https://temp-mail.org/')
            
            # Check if we're using a temporary email or user's email
            config = self.config_manager.get_config()
            user_email = config.get('temp_email', {}).get('user_email')
            
            if email != user_email:
                # Only do this for temporary emails
                # Wait for the email to arrive (up to 2 minutes)
                for _ in range(24):  # 24 * 5 seconds = 2 minutes
                    try:
                        # Check if the email has arrived
                        email_item = self.driver.find_element(
                            By.XPATH, '//div[contains(@class, "mail-item")]'
                        )
                        email_item.click()
                        break
                    except Exception:
                        # Wait and try again
                        time.sleep(5)
                else:
                    raise Exception("Confirmation email did not arrive within 2 minutes")
                
                # Wait for the email content to load
                wait.until(
                    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "inbox-data-content")]'))
                )
                
                # Find the confirmation link
                confirmation_link = self.driver.find_element(
                    By.XPATH, '//a[contains(@href, "openrouter.ai/auth/verify")]'
                )
                
                # Get the href attribute
                link = confirmation_link.get_attribute('href')
                
                if not link:
                    raise Exception("Failed to get confirmation link")
                
                # Navigate to the confirmation link
                self.driver.get(link)
            
            # Wait for the dashboard to load
            wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "API Keys")]'))
            )
            
            # Find the API key
            api_key_element = self.driver.find_element(
                By.XPATH, '//div[contains(@class, "api-key")]//span'
            )
            
            # Get the API key
            api_key = api_key_element.text
            
            if not api_key or not api_key.startswith('sk-or-'):
                raise Exception("Failed to get API key")
            
            return api_key
        except Exception as e:
            self.logger.error(f"Error signing up for OpenRouter: {str(e)}")
            raise Exception(f"Failed to sign up for OpenRouter: {str(e)}")