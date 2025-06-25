import os
import json
import logging
from datetime import datetime
from utils.APIError import APIError

class ConfigManager:
    """Manager for application configuration
    
    This class provides methods for loading, saving, and updating the application
    configuration, as well as the Continue.dev configuration.
    """
    
    def __init__(self, config_path='config/config.json'):
        """Initialize the ConfigManager
        
        Args:
            config_path (str): The path to the configuration file
        """
        self.logger = logging.getLogger('ai_dashboard.config')
        self.config_path = config_path
        self.config = self.load_config()
        
        # Create default config if it doesn't exist
        if not self.config:
            self.config = self._create_default_config()
            self.save_config()
    
    def _create_default_config(self):
        """Create a default configuration
        
        Returns:
            dict: The default configuration
        """
        # Get the user's home directory
        home_dir = os.path.expanduser('~')
        
        # Default configuration
        return {
            'continue_config_path': os.path.join(home_dir, '.continue', 'config.json'),
            'providers': {
                'openrouter': {
                    'api_keys': [],
                    'models': [
                        'openai/gpt-3.5-turbo',
                        'openai/gpt-4',
                        'anthropic/claude-3-opus',
                        'anthropic/claude-3-sonnet',
                        'anthropic/claude-3-haiku',
                        'meta-llama/llama-3-70b-instruct',
                        'meta-llama/llama-3-8b-instruct'
                    ],
                    'default_model': 'openai/gpt-3.5-turbo'
                },
                'ollama': {
                    'api_base': 'http://localhost:11434',
                    'models': [
                        'llama3',
                        'mistral',
                        'codellama',
                        'phi'
                    ],
                    'default_model': 'llama3'
                },
                'phind': {
                    'url': 'https://www.phind.com/'
                }
            },
            'current_provider': 'openrouter',
            'current_model': 'openai/gpt-3.5-turbo',
            'auto_rotate': True,
            'check_interval_seconds': 300,
            'max_error_count': 3,
            'log_file': 'logs/status.log',
            'temp_email': {
                'headless': True
            }
        }
    
    def load_config(self):
        """Load the configuration from file
        
        Returns:
            dict: The loaded configuration
        """
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Load the configuration
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_path}")
                return config
            else:
                self.logger.warning(f"Configuration file {self.config_path} not found")
                return None
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return None
    
    def save_config(self):
        """Save the configuration to file
        
        Returns:
            bool: True if the configuration was saved successfully, False otherwise
        """
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save the configuration
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            self.logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def get_config(self):
        """Get the current configuration
        
        Returns:
            dict: The current configuration
        """
        return self.config
    
    def update_config(self, updates):
        """Update the configuration with the provided updates
        
        Args:
            updates (dict): The updates to apply to the configuration
            
        Returns:
            dict: The updated configuration
        """
        try:
            # Update the configuration recursively
            self._update_dict_recursive(self.config, updates)
            
            # Save the updated configuration
            self.save_config()
            
            return self.config
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            raise APIError(f"Failed to update configuration: {str(e)}", 500)
    
    def _update_dict_recursive(self, target, updates):
        """Update a dictionary recursively
        
        Args:
            target (dict): The dictionary to update
            updates (dict): The updates to apply
        """
        for key, value in updates.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively update nested dictionaries
                self._update_dict_recursive(target[key], value)
            else:
                # Update the value
                target[key] = value
    
    def get_continue_config(self):
        """Get the Continue.dev configuration
        
        Returns:
            dict: The Continue.dev configuration
        """
        try:
            # Get the Continue.dev configuration path
            continue_config_path = self.config.get('continue_config_path', '')
            
            # Expand the path if it contains a tilde
            if '~' in continue_config_path:
                continue_config_path = os.path.expanduser(continue_config_path)
            
            # Load the configuration
            if os.path.exists(continue_config_path):
                with open(continue_config_path, 'r') as f:
                    continue_config = json.load(f)
                return continue_config
            else:
                self.logger.warning(f"Continue.dev configuration file {continue_config_path} not found")
                return None
        except Exception as e:
            self.logger.error(f"Error loading Continue.dev configuration: {str(e)}")
            return None
    
    def update_continue_config(self, updates):
        """Update the Continue.dev configuration with the provided updates
        
        Args:
            updates (dict): The updates to apply to the Continue.dev configuration
            
        Returns:
            dict: The updated Continue.dev configuration
        """
        try:
            # Get the Continue.dev configuration
            continue_config = self.get_continue_config()
            
            if not continue_config:
                self.logger.error("Continue.dev configuration not found")
                raise APIError("Continue.dev configuration not found", 500)
            
            # Update the configuration recursively
            self._update_dict_recursive(continue_config, updates)
            
            # Get the Continue.dev configuration path
            continue_config_path = self.config.get('continue_config_path', '')
            
            # Expand the path if it contains a tilde
            if '~' in continue_config_path:
                continue_config_path = os.path.expanduser(continue_config_path)
            
            # Save the updated configuration
            with open(continue_config_path, 'w') as f:
                json.dump(continue_config, f, indent=4)
            
            self.logger.info(f"Updated Continue.dev configuration at {continue_config_path}")
            return continue_config
        except Exception as e:
            self.logger.error(f"Error updating Continue.dev configuration: {str(e)}")
            raise APIError(f"Failed to update Continue.dev configuration: {str(e)}", 500)
    
    def update_provider_status(self, provider=None, model=None, key_index=None, last_used=None, error_count=None):
        """Update the status of a provider
        
        Args:
            provider (str): The provider to update
            model (str): The model to update
            key_index (int): The index of the key to update
            last_used (str): The last used timestamp
            error_count (int): The error count
            
        Returns:
            dict: The updated configuration
        """
        try:
            updates = {}
            
            # Update the current provider
            if provider:
                updates['current_provider'] = provider
            
            # Update the current model
            if model:
                updates['current_model'] = model
            
            # Update the key status
            if key_index is not None and last_used is not None:
                # Get the current timestamp if not provided
                if not last_used:
                    last_used = datetime.now().isoformat()
                
                # Update the key status
                for i, key in enumerate(self.config['providers']['openrouter']['api_keys']):
                    if i == key_index:
                        key['last_used'] = last_used
                        if error_count is not None:
                            key['error_count'] = error_count
            
            # Save the updated configuration
            self.save_config()
            
            return self.config
        except Exception as e:
            self.logger.error(f"Error updating provider status: {str(e)}")
            raise APIError(f"Failed to update provider status: {str(e)}", 500)