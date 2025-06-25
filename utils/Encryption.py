import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionManager:
    """Manager for encrypting and decrypting sensitive data
    
    This class provides methods for encrypting and decrypting sensitive data,
    such as API keys, using the Fernet symmetric encryption algorithm.
    """
    
    def __init__(self, key_file='.encryption_key'):
        """Initialize the EncryptionManager
        
        Args:
            key_file (str): The file to store the encryption key
        """
        self.logger = logging.getLogger('ai_dashboard.encryption')
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)
    
    def _load_or_generate_key(self):
        """Load the encryption key from file or generate a new one
        
        Returns:
            bytes: The encryption key
        """
        try:
            # Try to load the key from file
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                    self.logger.info("Loaded encryption key from file")
                    return key
            
            # Generate a new key
            self.logger.info("Generating new encryption key")
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
            
            # Save the key to file
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            return key
        except Exception as e:
            self.logger.error(f"Error loading/generating encryption key: {str(e)}")
            # Fallback to a derived key if file operations fail
            # This is less secure but ensures the application can still function
            salt = b'AI_Dashboard_Salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return base64.urlsafe_b64encode(kdf.derive(b'fallback_key'))
    
    def encrypt(self, data):
        """Encrypt the provided data
        
        Args:
            data (str): The data to encrypt
            
        Returns:
            str: The encrypted data as a base64-encoded string
        """
        if not data:
            return data
        
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Error encrypting data: {str(e)}")
            # Return the original data if encryption fails
            return data
    
    def decrypt(self, encrypted_data):
        """Decrypt the provided data
        
        Args:
            encrypted_data (str): The encrypted data as a base64-encoded string
            
        Returns:
            str: The decrypted data
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            # Check if the data is actually encrypted
            # If it doesn't look like base64, return as is
            try:
                decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            except Exception:
                return encrypted_data
            
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Error decrypting data: {str(e)}")
            # Return the original data if decryption fails
            return encrypted_data