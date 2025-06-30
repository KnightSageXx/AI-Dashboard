import logging
import threading
from datetime import datetime
from utils.APIError import APIError

class KeyRotator:
    """Service for managing and rotating OpenRouter API keys
    
    This class provides methods for managing OpenRouter API keys, including
    getting the current active key, testing keys, updating key status, rotating
    to the next available key, and adding new keys. Thread-safety is ensured
    using RLock.
    """
    
    def __init__(self, config_manager, encryption_manager, validator):
        """Initialize the KeyRotator
        
        Args:
            config_manager (ConfigManager): The configuration manager
            encryption_manager (EncryptionManager): The encryption manager
            validator (APIKeyValidator): The API key validator
        """
        self.logger = logging.getLogger('ai_dashboard.key_rotator')
        self.config_manager = config_manager
        self.encryption_manager = encryption_manager
        self.validator = validator
        self.lock = threading.RLock()
        self.error_threshold = 3  # Default error threshold
    
    def get_current_key(self):
        """Get the current active OpenRouter API key
        
        Returns:
            dict: The current active key, or None if no key is active
            
        Raises:
            APIError: If no active key is found
        """
        with self.lock:
            config = self.config_manager.get_config()
            
            # Find the active key
            for key in config['providers']['openrouter']['api_keys']:
                if key.get('is_active', False):
                    # Decrypt the key
                    decrypted_key = self.encryption_manager.decrypt(key['key'])
                    key_copy = key.copy()
                    key_copy['key'] = decrypted_key
                    return key_copy
            
            # No active key found
            self.logger.warning("No active OpenRouter API key found")
            raise APIError("No active OpenRouter API key found", 404)
    
    def test_current_key(self):
        """Test the current active OpenRouter API key
        
        Returns:
            dict: A dictionary with 'success' and 'message' keys
            
        Raises:
            APIError: If no active key is found or the key test fails
        """
        with self.lock:
            try:
                # Get the current key
                current_key = self.get_current_key()
                
                # Test the key
                result = self.validator.test_openrouter_key(current_key['key'])
                
                # Update the key status based on the test result
                if result['success']:
                    # Reset error count on successful test
                    self.update_key_status(error_count=0)
                else:
                    # Increment error count on failed test
                    self.update_key_status(error_count=current_key.get('error_count', 0) + 1)
                
                return result
            except APIError as e:
                # Re-raise API errors
                raise e
            except Exception as e:
                self.logger.error(f"Error testing current key: {str(e)}")
                raise APIError(f"Failed to test current key: {str(e)}", 500)
    
    def update_key_status(self, last_used=None, error_count=None):
        """Update the status of the current active key
        
        Args:
            last_used (str): The last used timestamp
            error_count (int): The error count
            
        Returns:
            dict: The updated configuration
            
        Raises:
            APIError: If no active key is found
        """
        with self.lock:
            try:
                config = self.config_manager.get_config()
                
                # Find the active key
                for i, key in enumerate(config['providers']['openrouter']['api_keys']):
                    if key.get('is_active', False):
                        # Update the key status
                        if last_used is not None:
                            key['last_used'] = last_used or datetime.now().isoformat()
                        if error_count is not None:
                            key['error_count'] = error_count
                        
                        # Save the updated configuration
                        self.config_manager.save_config()
                        return config
                
                # No active key found
                self.logger.warning("No active OpenRouter API key found")
                raise APIError("No active OpenRouter API key found", 404)
            except APIError as e:
                # Re-raise API errors
                raise e
            except Exception as e:
                self.logger.error(f"Error updating key status: {str(e)}")
                raise APIError(f"Failed to update key status: {str(e)}", 500)
    
    def check_and_rotate(self):
        """Check the current key and rotate if necessary
        
        This method checks the current key's error count and validity,
        and rotates to the next key if needed.
        
        Returns:
            bool: True if the key was rotated, False otherwise
        """
        with self.lock:
            try:
                # Get the current configuration
                config = self.config_manager.get_config()
                self.error_threshold = config.get('max_error_count', 3)
                
                # Get the current key
                try:
                    current_key = self.get_current_key()
                except APIError:
                    # No active key found, try to rotate
                    self.rotate()
                    return True
                
                # Check if the key has too many errors
                if current_key.get('error_count', 0) >= self.error_threshold:
                    self.logger.warning(f"Current key has {current_key.get('error_count')} errors, rotating")
                    self.rotate()
                    return True
                
                # Test the current key
                try:
                    result = self.test_current_key()
                    if not result['success']:
                        # Key test failed, check if error count exceeds threshold
                        if current_key.get('error_count', 0) >= self.error_threshold:
                            self.rotate()
                            return True
                    return False
                except Exception as e:
                    self.logger.warning(f"Error testing current key: {str(e)}")
                    # Increment error count
                    self.update_key_status(error_count=current_key.get('error_count', 0) + 1)
                    # Check if error count exceeds threshold
                    if current_key.get('error_count', 0) >= self.error_threshold:
                        self.rotate()
                        return True
                    return False
            except Exception as e:
                self.logger.error(f"Error checking key: {str(e)}")
                return False
    
    def rotate(self):
        """Rotate to the next available OpenRouter API key
        
        Returns:
            str: A message indicating the result of the rotation
            
        Raises:
            APIError: If no keys are available or the rotation fails
        """
        with self.lock:
            try:
                config = self.config_manager.get_config()
                keys = config['providers']['openrouter']['api_keys']
                
                # Check if there are any keys
                if not keys:
                    self.logger.warning("No OpenRouter API keys available")
                    raise APIError("No OpenRouter API keys available", 404)
                
                # Find the current active key
                current_index = -1
                for i, key in enumerate(keys):
                    if key.get('is_active', False):
                        current_index = i
                        # Deactivate the current key
                        key['is_active'] = False
                        break
                
                # Find the next key to activate
                next_index = (current_index + 1) % len(keys)
                keys[next_index]['is_active'] = True
                keys[next_index]['last_used'] = datetime.now().isoformat()
                keys[next_index]['error_count'] = 0
                
                # Save the updated configuration
                self.config_manager.save_config()
                
                # Test the new key
                try:
                    self.test_current_key()
                    return f"Rotated to key {next_index + 1} of {len(keys)}"
                except Exception as e:
                    self.logger.warning(f"New key test failed: {str(e)}")
                    # If the new key fails, try to rotate again
                    if len(keys) > 1:
                        return self.rotate()
                    else:
                        raise APIError("All keys failed testing", 500)
            except APIError as e:
                # Re-raise API errors
                raise e
            except Exception as e:
                self.logger.error(f"Error rotating key: {str(e)}")
                raise APIError(f"Failed to rotate key: {str(e)}", 500)
    
    def add_key(self, key):
        """Add a new OpenRouter API key
        
        Args:
            key (str): The API key to add
            
        Returns:
            str: A message indicating the result of the addition
            
        Raises:
            APIError: If the key is invalid or the addition fails
        """
        with self.lock:
            try:
                # Validate the key
                self.validator.validate_openrouter_key(key)
                
                # Test the key
                result = self.validator.test_openrouter_key(key)
                
                if not result['success']:
                    raise APIError(f"Key validation failed: {result['message']}", 400)
                
                # Encrypt the key
                encrypted_key = self.encryption_manager.encrypt(key)
                
                # Add the key to the configuration
                config = self.config_manager.get_config()
                keys = config['providers']['openrouter']['api_keys']
                
                # Check if the key already exists
                for existing_key in keys:
                    if self.encryption_manager.decrypt(existing_key['key']) == key:
                        raise APIError("Key already exists", 400)
                
                # Add the new key
                new_key = {
                    'key': encrypted_key,
                    'is_active': not keys,  # Activate if it's the first key
                    'last_used': datetime.now().isoformat() if not keys else None,
                    'error_count': 0
                }
                
                keys.append(new_key)
                
                # Save the updated configuration
                self.config_manager.save_config()
                
                return f"Added new OpenRouter API key (total: {len(keys)})"
            except APIError as e:
                # Re-raise API errors
                raise e
            except Exception as e:
                self.logger.error(f"Error adding key: {str(e)}")
                raise APIError(f"Failed to add key: {str(e)}", 500)