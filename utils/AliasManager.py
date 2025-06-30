import os
import json
import logging
from datetime import datetime

class AliasManager:
    """Class for managing Gmail aliases
    
    This class provides methods for generating and tracking Gmail aliases,
    which are created by adding a plus sign and a number to the base email address.
    For example: myemail+1@gmail.com, myemail+2@gmail.com, etc.
    """
    
    def __init__(self, base_email, used_emails_path='used_emails.json', log_path='email_log.txt'):
        """Initialize the AliasManager
        
        Args:
            base_email (str): The base Gmail address (e.g., myemail@gmail.com)
            used_emails_path (str): Path to the JSON file tracking used aliases
            log_path (str): Path to the log file for email usage
        """
        self.logger = logging.getLogger('gmail_verification.alias_manager')
        self.base_email = base_email
        self.used_emails_path = used_emails_path
        self.log_path = log_path
        self.used_emails = self._load_used_emails()
    
    def _load_used_emails(self):
        """Load the list of used email aliases from the JSON file
        
        Returns:
            dict: Dictionary of used email aliases and their usage info
        """
        try:
            if os.path.exists(self.used_emails_path):
                with open(self.used_emails_path, 'r') as f:
                    return json.load(f)
            else:
                # Create an empty dictionary if the file doesn't exist
                return {}
        except Exception as e:
            self.logger.error(f"Error loading used emails: {str(e)}")
            return {}
    
    def _save_used_emails(self):
        """Save the list of used email aliases to the JSON file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.used_emails_path, 'w') as f:
                json.dump(self.used_emails, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving used emails: {str(e)}")
            return False
    
    def _log_alias_usage(self, alias, api_key=None, success=True):
        """Log the usage of an email alias
        
        Args:
            alias (str): The email alias that was used
            api_key (str): The API key that was obtained (if any)
            success (bool): Whether the verification was successful
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] Alias: {alias} | Success: {success}"
            
            if api_key:
                log_entry += f" | API Key: {api_key}"
            
            with open(self.log_path, 'a') as f:
                f.write(log_entry + "\n")
            
            return True
        except Exception as e:
            self.logger.error(f"Error logging alias usage: {str(e)}")
            return False
    
    def generate_next_alias(self):
        """Generate the next unused email alias
        
        Returns:
            str: The next unused email alias
        """
        try:
            # Parse the base email to get the username and domain
            if '@' not in self.base_email:
                self.logger.error(f"Invalid base email: {self.base_email}")
                return None
            
            username, domain = self.base_email.split('@')
            
            # Start from 1 and increment until we find an unused alias
            counter = 1
            while counter <= 500:  # Gmail has a limit of ~500 aliases per day
                alias = f"{username}+{counter}@{domain}"
                
                if alias not in self.used_emails:
                    self.logger.info(f"Generated new alias: {alias}")
                    return alias
                
                counter += 1
            
            self.logger.error("All aliases have been used (reached limit of 500)")
            return None
        except Exception as e:
            self.logger.error(f"Error generating next alias: {str(e)}")
            return None
    
    def mark_alias_as_used(self, alias, api_key=None, success=True):
        """Mark an email alias as used
        
        Args:
            alias (str): The email alias to mark as used
            api_key (str): The API key that was obtained (if any)
            success (bool): Whether the verification was successful
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add the alias to the used emails dictionary
            self.used_emails[alias] = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'success': success
            }
            
            if api_key:
                self.used_emails[alias]['api_key'] = api_key
            
            # Save the updated dictionary to the JSON file
            self._save_used_emails()
            
            # Log the alias usage
            self._log_alias_usage(alias, api_key, success)
            
            self.logger.info(f"Marked alias as used: {alias}")
            return True
        except Exception as e:
            self.logger.error(f"Error marking alias as used: {str(e)}")
            return False
    
    def get_used_aliases_count(self):
        """Get the count of used email aliases
        
        Returns:
            int: The number of used email aliases
        """
        return len(self.used_emails)
    
    def get_successful_aliases_count(self):
        """Get the count of successfully used email aliases
        
        Returns:
            int: The number of successfully used email aliases
        """
        return sum(1 for alias in self.used_emails.values() if alias.get('success', False))
    
    def get_all_api_keys(self):
        """Get all API keys obtained from successful verifications
        
        Returns:
            list: List of API keys
        """
        return [alias.get('api_key') for alias in self.used_emails.values() 
                if alias.get('success', False) and 'api_key' in alias]