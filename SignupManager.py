import os
import json
import logging
from utils.temp_email import TempEmailAutomation
from gmail_verification import GmailVerificationSystem

class SignupManager:
    """Class for managing the signup process for OpenRouter
    
    This class integrates the TempEmailAutomation and GmailVerificationSystem
    to provide a complete solution for creating and verifying OpenRouter accounts.
    """
    
    def __init__(self, config_manager, use_gmail_aliases=False, base_email='knightsagexf@gmail.com'):
        """Initialize the SignupManager
        
        Args:
            config_manager (ConfigManager): The configuration manager
            use_gmail_aliases (bool): Whether to use Gmail aliases instead of temp emails
            base_email (str): The base Gmail address to use for aliases
        """
        self.logger = logging.getLogger('ai_dashboard.signup_manager')
        self.config_manager = config_manager
        self.use_gmail_aliases = use_gmail_aliases
        self.base_email = base_email
        
        # Initialize the temp email automation
        self.temp_email_automation = TempEmailAutomation(config_manager)
        
        # Initialize the Gmail verification system if using aliases
        if use_gmail_aliases:
            self.gmail_verification_system = GmailVerificationSystem(
                base_email=base_email,
                headless=config_manager.get_config()['temp_email']['headless']
            )
    
    def create_new_account(self):
        """Create a new OpenRouter account
        
        Returns:
            dict: Result of the account creation process
        """
        try:
            if self.use_gmail_aliases:
                # Use Gmail aliases for signup and verification
                self.logger.info("Creating new OpenRouter account using Gmail aliases")
                result = self.gmail_verification_system.run()
                
                if result['success']:
                    # Add the API key to the config
                    from utils.key_rotator import KeyRotator
                    key_rotator = KeyRotator(self.config_manager)
                    key_rotator.add_key(result['api_key'])
                    
                    return {
                        'success': True,
                        'email': result['alias'],
                        'api_key': result['api_key']
                    }
                else:
                    return {
                        'success': False,
                        'error': result['error']
                    }
            else:
                # Use temporary emails for signup
                self.logger.info("Creating new OpenRouter account using temporary email")
                result = self.temp_email_automation.start_automation()
                
                if 'Failed' not in result and 'Error' not in result:
                    return {
                        'success': True,
                        'message': result
                    }
                else:
                    return {
                        'success': False,
                        'error': result
                    }
        
        except Exception as e:
            self.logger.error(f"Error creating new account: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def rotate_account(self):
        """Rotate to a new OpenRouter account
        
        This method creates a new account and updates the configuration
        to use the new API key as the primary key.
        
        Returns:
            dict: Result of the account rotation process
        """
        try:
            # Create a new account
            result = self.create_new_account()
            
            if result['success']:
                # Update the configuration to use the new API key
                config = self.config_manager.get_config()
                
                if 'api_key' in result:
                    # Move the current primary key to the backup keys if it exists
                    if 'openrouter_api_key' in config and config['openrouter_api_key']:
                        if 'backup_api_keys' not in config:
                            config['backup_api_keys'] = []
                        
                        config['backup_api_keys'].append(config['openrouter_api_key'])
                    
                    # Set the new API key as the primary key
                    config['openrouter_api_key'] = result['api_key']
                    
                    # Save the updated configuration
                    self.config_manager.save_config(config)
                    
                    self.logger.info("Successfully rotated to a new OpenRouter account")
                    return {
                        'success': True,
                        'message': f"Rotated to new account with API key: {result['api_key'][:5]}..."
                    }
                else:
                    self.logger.error("API key not found in result")
                    return {
                        'success': False,
                        'error': "API key not found in result"
                    }
            else:
                return result
        
        except Exception as e:
            self.logger.error(f"Error rotating account: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }