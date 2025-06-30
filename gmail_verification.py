#!/usr/bin/env python3

import os
import json
import time
import logging
import argparse
from datetime import datetime
from utils.GmailReader import GmailReader
from utils.AliasManager import AliasManager
from utils.Verifier import Verifier

# Configure logging
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'gmail_verification.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('gmail_verification')

class GmailVerificationSystem:
    """Main class for the Gmail auto-verification system
    
    This class integrates the GmailReader, AliasManager, and Verifier
    to create a complete Gmail auto-verification system.
    """
    
    def __init__(self, base_email, credentials_path='credentials.json', token_path='token.json',
                 used_emails_path='used_emails.json', log_path='email_log.txt', headless=True,
                 max_retries=5, retry_delay=60):
        """Initialize the GmailVerificationSystem
        
        Args:
            base_email (str): The base Gmail address (e.g., myemail@gmail.com)
            credentials_path (str): Path to the credentials.json file
            token_path (str): Path to the token.json file
            used_emails_path (str): Path to the JSON file tracking used aliases
            log_path (str): Path to the log file for email usage
            headless (bool): Whether to run Chrome in headless mode
            max_retries (int): Maximum number of retries for checking emails
            retry_delay (int): Delay between retries in seconds
        """
        self.logger = logging.getLogger('gmail_verification.system')
        self.base_email = base_email
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.used_emails_path = used_emails_path
        self.log_path = log_path
        self.headless = headless
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize components
        self.gmail_reader = GmailReader(credentials_path, token_path)
        self.alias_manager = AliasManager(base_email, used_emails_path, log_path)
        self.verifier = Verifier(headless)
    
    def run(self):
        """Run the Gmail auto-verification system
        
        Returns:
            dict: Result of the verification process
        """
        try:
            # Generate the next unused alias
            alias = self.alias_manager.generate_next_alias()
            if not alias:
                self.logger.error("Could not generate a new alias")
                return {'success': False, 'error': 'Could not generate a new alias'}
            
            self.logger.info(f"Using alias: {alias}")
            
            # Authenticate with Gmail API
            if not self.gmail_reader.authenticate():
                self.logger.error("Failed to authenticate with Gmail API")
                return {'success': False, 'error': 'Failed to authenticate with Gmail API'}
            
            # TODO: Here you would typically sign up for OpenRouter using the alias
            # For this example, we'll assume the signup has been done and we're waiting for the verification email
            
            # Check for verification emails
            verification_link = None
            for retry in range(self.max_retries):
                self.logger.info(f"Checking for verification emails (attempt {retry+1}/{self.max_retries})")
                
                # Get verification emails
                emails = self.gmail_reader.get_verification_emails()
                
                if emails:
                    # Extract verification link from the first email
                    verification_link = self.gmail_reader.extract_verification_link(emails[0])
                    
                    if verification_link:
                        # Mark the email as read
                        self.gmail_reader.mark_as_read(emails[0]['id'])
                        break
                
                if retry < self.max_retries - 1:
                    self.logger.info(f"No verification link found. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
            
            if not verification_link:
                self.logger.error("Could not find verification link after maximum retries")
                self.alias_manager.mark_alias_as_used(alias, success=False)
                return {'success': False, 'error': 'Could not find verification link'}
            
            # Visit the verification link
            if not self.verifier.visit_verification_link(verification_link):
                self.logger.error("Failed to visit verification link")
                self.alias_manager.mark_alias_as_used(alias, success=False)
                return {'success': False, 'error': 'Failed to visit verification link'}
            
            # Extract the API key
            api_key = self.verifier.extract_api_key()
            if not api_key:
                self.logger.error("Failed to extract API key")
                self.alias_manager.mark_alias_as_used(alias, success=False)
                return {'success': False, 'error': 'Failed to extract API key'}
            
            # Mark the alias as used
            self.alias_manager.mark_alias_as_used(alias, api_key, success=True)
            
            # Close the verifier
            self.verifier.close()
            
            self.logger.info(f"Successfully verified email and obtained API key: {api_key[:5]}...")
            return {
                'success': True,
                'alias': alias,
                'api_key': api_key
            }
        
        except Exception as e:
            self.logger.error(f"Error in verification process: {str(e)}")
            return {'success': False, 'error': str(e)}

def main():
    """Main function for running the Gmail auto-verification system"""
    parser = argparse.ArgumentParser(description='Gmail Auto-Verification System')
    parser.add_argument('--base-email', type=str, default='knightsagexf@gmail.com',
                        help='Base Gmail address')
    parser.add_argument('--credentials-path', type=str, default='credentials.json',
                        help='Path to the credentials.json file')
    parser.add_argument('--token-path', type=str, default='token.json',
                        help='Path to the token.json file')
    parser.add_argument('--used-emails-path', type=str, default='used_emails.json',
                        help='Path to the JSON file tracking used aliases')
    parser.add_argument('--log-path', type=str, default='email_log.txt',
                        help='Path to the log file for email usage')
    parser.add_argument('--headless', action='store_true',
                        help='Run Chrome in headless mode')
    parser.add_argument('--max-retries', type=int, default=5,
                        help='Maximum number of retries for checking emails')
    parser.add_argument('--retry-delay', type=int, default=60,
                        help='Delay between retries in seconds')
    
    args = parser.parse_args()
    
    system = GmailVerificationSystem(
        base_email=args.base_email,
        credentials_path=args.credentials_path,
        token_path=args.token_path,
        used_emails_path=args.used_emails_path,
        log_path=args.log_path,
        headless=args.headless,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay
    )
    
    result = system.run()
    
    if result['success']:
        print(f"\nSuccess! Verified email: {result['alias']}")
        print(f"API Key: {result['api_key']}")
    else:
        print(f"\nError: {result['error']}")

if __name__ == '__main__':
    main()