import os
import base64
import logging
import re
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class GmailReader:
    """Class for reading Gmail messages using the Gmail API
    
    This class provides methods for authenticating with the Gmail API,
    reading inbox messages, and finding verification emails.
    """
    
    def __init__(self, credentials_path='credentials.json', token_path='token.json', scopes=None):
        """Initialize the GmailReader
        
        Args:
            credentials_path (str): Path to the credentials.json file
            token_path (str): Path to the token.json file
            scopes (list): List of API scopes to request
        """
        self.logger = logging.getLogger('gmail_verification.gmail_reader')
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = scopes or ['https://www.googleapis.com/auth/gmail.readonly']
        self.service = None
    
    def authenticate(self):
        """Authenticate with the Gmail API
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        creds = None
        
        # Check if token.json exists
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_info(
                json.loads(open(self.token_path).read()), self.scopes)
        
        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            # Build the Gmail API service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Successfully authenticated with Gmail API")
            return True
        except Exception as e:
            self.logger.error(f"Error authenticating with Gmail API: {str(e)}")
            return False
    
    def get_verification_emails(self, sender='noreply@openrouter.ai', max_results=10):
        """Get verification emails from a specific sender
        
        Args:
            sender (str): The email address of the sender
            max_results (int): Maximum number of emails to retrieve
            
        Returns:
            list: List of email messages
        """
        try:
            # Make sure we're authenticated
            if not self.service:
                if not self.authenticate():
                    return []
            
            # Search for emails from the specified sender
            query = f"from:{sender} is:unread"
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                self.logger.info(f"No unread messages found from {sender}")
                return []
            
            # Get the full message for each email
            verification_emails = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', id=message['id']).execute()
                verification_emails.append(msg)
            
            self.logger.info(f"Found {len(verification_emails)} verification emails")
            return verification_emails
        
        except Exception as e:
            self.logger.error(f"Error getting verification emails: {str(e)}")
            return []
    
    def extract_verification_link(self, message):
        """Extract the verification link from an email message
        
        Args:
            message (dict): The email message
            
        Returns:
            str: The verification link or None if not found
        """
        try:
            # Get the email body
            if 'payload' not in message or 'parts' not in message['payload']:
                return None
            
            parts = message['payload']['parts']
            body = None
            
            # Look for the HTML part of the email
            for part in parts:
                if part['mimeType'] == 'text/html':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            
            if not body:
                # Try to get the plain text part if HTML is not available
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            
            if not body:
                self.logger.error("Could not find email body")
                return None
            
            # Look for verification link in the email body
            # This regex pattern looks for URLs containing 'openrouter.ai/verify'
            verification_link_pattern = r'https?://[\w.-]+openrouter\.ai/verify[\w\d\?\=\&\-\.\/]+'
            match = re.search(verification_link_pattern, body)
            
            if match:
                verification_link = match.group(0)
                self.logger.info(f"Found verification link: {verification_link}")
                return verification_link
            else:
                self.logger.error("Could not find verification link in email")
                return None
        
        except Exception as e:
            self.logger.error(f"Error extracting verification link: {str(e)}")
            return None
    
    def mark_as_read(self, message_id):
        """Mark an email as read
        
        Args:
            message_id (str): The ID of the message to mark as read
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Make sure we're authenticated
            if not self.service:
                if not self.authenticate():
                    return False
            
            # Modify the labels to remove UNREAD
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            self.logger.info(f"Marked message {message_id} as read")
            return True
        
        except Exception as e:
            self.logger.error(f"Error marking message as read: {str(e)}")
            return False