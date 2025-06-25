import requests
import logging
from datetime import datetime

class KeyRotator:
    """Manages OpenRouter API key rotation"""
    
    def __init__(self, config_manager):
        """Initialize the KeyRotator
        
        Args:
            config_manager (ConfigManager): The configuration manager
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger('ai_dashboard.key_rotator')
    
    def get_current_key(self):
        """Get the current active OpenRouter API key
        
        Returns:
            dict: The current active key object or None if not found
        """
        config = self.config_manager.get_config()
        
        # Find the active key
        for key in config['providers']['openrouter']['api_keys']:
            if key['is_active']:
                return key
        
        # If no active key found, return None
        return None
    
    def test_current_key(self):
        """Test the current OpenRouter API key
        
        Returns:
            dict: Result of the test with success and message
        """
        current_key = self.get_current_key()
        if not current_key:
            return {'success': False, 'message': 'No active API key found'}
        
        return self.test_key(current_key['key'])
    
    def test_key(self, api_key):
        """Test an OpenRouter API key
        
        Args:
            api_key (str): The API key to test
            
        Returns:
            dict: Result of the test with success and message
        """
        try:
            # Make a simple request to the OpenRouter API
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use the models endpoint to test the key
            response = requests.get('https://openrouter.ai/api/v1/models', headers=headers)
            
            if response.status_code == 200:
                # Update the key status
                self._update_key_status(api_key, error=False)
                return {'success': True, 'message': 'API key is valid'}
            else:
                # Update the key status with an error
                self._update_key_status(api_key, error=True)
                return {'success': False, 'message': f'API key test failed: {response.status_code} - {response.text}'}
        
        except Exception as e:
            self.logger.error(f"Error testing API key: {str(e)}")
            # Update the key status with an error
            self._update_key_status(api_key, error=True)
            return {'success': False, 'message': f'Error testing API key: {str(e)}'}
    
    def _update_key_status(self, api_key, error=False):
        """Update the status of an API key
        
        Args:
            api_key (str): The API key to update
            error (bool, optional): Whether an error occurred
        """
        config = self.config_manager.get_config()
        
        # Find and update the key
        for key in config['providers']['openrouter']['api_keys']:
            if key['key'] == api_key:
                key['last_used'] = datetime.now().isoformat()
                if error:
                    key['error_count'] += 1
                else:
                    key['error_count'] = 0
                break
        
        # Save the updated config
        self.config_manager.save_config()
    
    def rotate_key(self):
        """Rotate to the next available OpenRouter API key
        
        Returns:
            str: Message indicating the result of the rotation
        """
        config = self.config_manager.get_config()
        api_keys = config['providers']['openrouter']['api_keys']
        
        if not api_keys:
            return "No API keys available"
        
        # Find the current active key
        current_key_index = -1
        for i, key in enumerate(api_keys):
            if key['is_active']:
                current_key_index = i
                key['is_active'] = False
                break
        
        # Find the next key to use
        next_key_index = (current_key_index + 1) % len(api_keys)
        attempts = 0
        
        # Try to find a key with error_count less than max_error_count
        while attempts < len(api_keys):
            next_key = api_keys[next_key_index]
            if next_key['error_count'] < config['max_error_count']:
                next_key['is_active'] = True
                next_key['last_used'] = datetime.now().isoformat()
                
                # Update the Continue config with the new key
                self._update_continue_config(next_key['key'])
                
                # Save the updated config
                self.config_manager.save_config()
                
                return f"Rotated to next API key: {next_key['key'][:4]}...{next_key['key'][-4:]}"
            
            # Try the next key
            next_key_index = (next_key_index + 1) % len(api_keys)
            attempts += 1
        
        # If all keys have too many errors, use the first key anyway
        if current_key_index == -1:
            api_keys[0]['is_active'] = True
            api_keys[0]['last_used'] = datetime.now().isoformat()
            
            # Update the Continue config with the new key
            self._update_continue_config(api_keys[0]['key'])
            
            # Save the updated config
            self.config_manager.save_config()
            
            return f"All keys have errors, using first key: {api_keys[0]['key'][:4]}...{api_keys[0]['key'][-4:]}"
        
        return "No suitable API key found"
    
    def add_key(self, api_key):
        """Add a new OpenRouter API key
        
        Args:
            api_key (str): The API key to add
            
        Returns:
            str: Message indicating the result of adding the key
        """
        config = self.config_manager.get_config()
        
        # Check if the key already exists
        for key in config['providers']['openrouter']['api_keys']:
            if key['key'] == api_key:
                return "API key already exists"
        
        # Test the key before adding it
        test_result = self.test_key(api_key)
        if not test_result['success']:
            return f"Failed to add API key: {test_result['message']}"
        
        # Add the new key
        new_key = {
            "key": api_key,
            "is_active": False,  # Don't make it active by default
            "last_used": None,
            "error_count": 0
        }
        
        config['providers']['openrouter']['api_keys'].append(new_key)
        
        # Save the updated config
        self.config_manager.save_config()
        
        return f"Added new API key: {api_key[:4]}...{api_key[-4:]}"
    
    def _update_continue_config(self, api_key):
        """Update the Continue.dev configuration with the new API key
        
        Args:
            api_key (str): The API key to use
        """
        config = self.config_manager.get_config()
        model = config['current_model']
        
        # Prepare the updates for the Continue config
        updates = {}
        
        # Get the current Continue config
        continue_config = self.config_manager.get_continue_config()
        if not continue_config:
            self.logger.error("Failed to get Continue config")
            return
        
        # Update the providers in the Continue config
        if 'providers' in continue_config:
            for provider in continue_config['providers']:
                if 'openrouter' in provider['id']:
                    provider['apiKey'] = api_key
                    provider['defaultModel'] = model
        
        # Save the updated Continue config
        self.config_manager.update_continue_config(continue_config)