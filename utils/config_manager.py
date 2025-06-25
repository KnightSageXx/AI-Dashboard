import os
import json
import logging
from datetime import datetime

class ConfigManager:
    """Manages the application configuration and Continue config"""
    
    def __init__(self, config_path):
        """Initialize the ConfigManager
        
        Args:
            config_path (str): Path to the application config file
        """
        self.config_path = config_path
        self.logger = logging.getLogger('ai_dashboard.config_manager')
        
        # Load the config file
        self.load_config()
        
    def load_config(self):
        """Load the configuration from the config file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
                
            # Expand the continue_config_path if it contains ~
            if 'continue_config_path' in self.config:
                self.config['continue_config_path'] = os.path.expanduser(self.config['continue_config_path'])
                
            self.logger.info(f"Loaded configuration from {self.config_path}")
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file: {self.config_path}")
            raise
    
    def save_config(self):
        """Save the configuration to the config file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving config file: {str(e)}")
            raise
    
    def get_config(self):
        """Get the current configuration
        
        Returns:
            dict: The current configuration
        """
        return self.config
    
    def update_config(self, updates):
        """Update the configuration with the provided updates
        
        Args:
            updates (dict): Dictionary of updates to apply to the config
            
        Returns:
            dict: The updated configuration
        """
        try:
            # Apply the updates
            for key, value in updates.items():
                if key in self.config:
                    if isinstance(self.config[key], dict) and isinstance(value, dict):
                        # Recursively update nested dictionaries
                        self._update_dict(self.config[key], value)
                    else:
                        self.config[key] = value
                else:
                    self.config[key] = value
            
            # Save the updated config
            self.save_config()
            
            return self.config
        except Exception as e:
            self.logger.error(f"Error updating config: {str(e)}")
            raise
    
    def _update_dict(self, target, updates):
        """Recursively update a dictionary
        
        Args:
            target (dict): The dictionary to update
            updates (dict): The updates to apply
        """
        for key, value in updates.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
    
    def get_continue_config(self):
        """Get the Continue.dev configuration
        
        Returns:
            dict: The Continue.dev configuration
        """
        try:
            continue_config_path = self.config.get('continue_config_path')
            if not continue_config_path:
                self.logger.error("Continue config path not set in config")
                return None
            
            with open(continue_config_path, 'r') as f:
                continue_config = json.load(f)
            
            self.logger.info(f"Loaded Continue config from {continue_config_path}")
            return continue_config
        except FileNotFoundError:
            self.logger.error(f"Continue config file not found: {continue_config_path}")
            return None
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in Continue config file: {continue_config_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading Continue config: {str(e)}")
            return None
    
    def update_continue_config(self, updates):
        """Update the Continue.dev configuration
        
        Args:
            updates (dict): Dictionary of updates to apply to the Continue config
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            continue_config_path = self.config.get('continue_config_path')
            if not continue_config_path:
                self.logger.error("Continue config path not set in config")
                return False
            
            # Load the current Continue config
            continue_config = self.get_continue_config()
            if continue_config is None:
                return False
            
            # Apply the updates
            for key, value in updates.items():
                if key in continue_config:
                    if isinstance(continue_config[key], dict) and isinstance(value, dict):
                        # Recursively update nested dictionaries
                        self._update_dict(continue_config[key], value)
                    else:
                        continue_config[key] = value
                else:
                    continue_config[key] = value
            
            # Save the updated Continue config
            with open(continue_config_path, 'w') as f:
                json.dump(continue_config, f, indent=2)
            
            self.logger.info(f"Updated Continue config at {continue_config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating Continue config: {str(e)}")
            return False
    
    def update_provider_status(self, provider, key=None, model=None, error=None):
        """Update the status of a provider in the config
        
        Args:
            provider (str): The provider to update (openrouter, ollama, phind)
            key (str, optional): The API key to update (for openrouter)
            model (str, optional): The model to update
            error (bool, optional): Whether an error occurred
            
        Returns:
            dict: The updated configuration
        """
        try:
            # Update the current provider and model
            if provider:
                self.config['current_provider'] = provider
            
            if model:
                self.config['current_model'] = model
            
            # Update the key status for OpenRouter
            if provider == 'openrouter' and key:
                for key_obj in self.config['providers']['openrouter']['api_keys']:
                    if key_obj['key'] == key:
                        key_obj['last_used'] = datetime.now().isoformat()
                        if error is not None:
                            if error:
                                key_obj['error_count'] += 1
                            else:
                                key_obj['error_count'] = 0
            
            # Save the updated config
            self.save_config()
            
            return self.config
        except Exception as e:
            self.logger.error(f"Error updating provider status: {str(e)}")
            raise