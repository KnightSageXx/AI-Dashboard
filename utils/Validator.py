import re
import logging
import requests
from utils.APIError import APIError

class APIKeyValidator:
    """Validator for API keys and other inputs
    
    This class provides methods for validating API keys and other inputs
    to ensure they meet the required format and are valid.
    """
    
    def __init__(self):
        """Initialize the APIKeyValidator"""
        self.logger = logging.getLogger('ai_dashboard.validator')
    
    def validate_openrouter_key(self, key):
        """Validate an OpenRouter API key
        
        Args:
            key (str): The API key to validate
            
        Returns:
            bool: True if the key is valid, False otherwise
            
        Raises:
            APIError: If the key is invalid
        """
        # Check if the key is empty
        if not key or not key.strip():
            raise APIError("API key cannot be empty", 400)
        
        # Check if the key matches the expected format
        # OpenRouter keys typically start with 'sk-or-' followed by a string of alphanumeric characters
        if not re.match(r'^sk-or-[a-zA-Z0-9]{30,}$', key):
            raise APIError("Invalid OpenRouter API key format", 400)
        
        return True
    
    def test_openrouter_key(self, key):
        """Test an OpenRouter API key by making a request to the API
        
        Args:
            key (str): The API key to test
            
        Returns:
            dict: A dictionary with 'success' and 'message' keys
        """
        try:
            # Validate the key format first
            self.validate_openrouter_key(key)
            
            # Make a request to the OpenRouter API to test the key
            headers = {
                'Authorization': f'Bearer {key}',
                'Content-Type': 'application/json'
            }
            
            # Use the models endpoint to test the key
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=10
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'API key is valid'
                }
            else:
                error_message = response.json().get('error', {}).get('message', 'Unknown error')
                return {
                    'success': False,
                    'message': f'API key test failed: {error_message}'
                }
        except APIError as e:
            # Re-raise API validation errors
            raise e
        except Exception as e:
            self.logger.error(f"Error testing OpenRouter API key: {str(e)}")
            return {
                'success': False,
                'message': f'Error testing API key: {str(e)}'
            }