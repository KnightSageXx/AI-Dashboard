import os
import json
import logging
import threading
from datetime import datetime
from threading import RLock
from utils.APIError import APIError

# Always load environment variables
from dotenv import load_dotenv
load_dotenv()

class ConfigManager:
    """Manager for application configuration
    
    This class provides methods for loading, saving, and updating the application
    configuration, as well as the Continue.dev configuration. Thread-safe operations
    are ensured using RLock, and atomic file writes prevent corruption.
    """
    
    def __init__(self, config_path='config/config.json'):
        """Initialize the ConfigManager
        
        Args:
            config_path (str): The path to the configuration file
        """
        self.logger = logging.getLogger('ai_dashboard.config')
        self.config_path = config_path
        self.lock = RLock()
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
                    ],
                    'default_model': 'openai/gpt-3.5-turbo'
                },
                'ollama': {
                    'models': [
                        'llama3',
                        'mistral',
                        'codellama',
                        'phi3',
                        'gemma',
                        'llava'
                    ],
                    'default_model': 'llama3'
                },
                'phind': {
                    'models': [
                        'phind/phind-codellama-34b',
                    ],
                    'default_model': 'phind/phind-codellama-34b'
                }
            },
            'current_provider': 'openrouter',
            'current_model': 'openai/gpt-3.5-turbo',
            'auto_rotate': True,
            'check_interval_seconds': 300,
            'max_error_count': 3
        }
    
    def load_config(self):
        """Load the configuration from the file
        
        Returns:
            dict: The loaded configuration, or None if the file doesn't exist
        """
        with self.lock:
            if not os.path.exists(self.config_path):
                self.logger.warning(f"Config file not found: {self.config_path}")
                return None
            
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                self.logger.debug(f"Loaded config from {self.config_path}")
                return config
            except Exception as e:
                self.logger.error(f"Error loading config: {str(e)}")
                return None
    
    def save_config(self):
        """Save the configuration to the file
        
        Returns:
            bool: True if the configuration was saved successfully
        """
        with self.lock:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                # Write to a temporary file first
                temp_path = f"{self.config_path}.tmp"
                with open(temp_path, 'w') as f:
                    json.dump(self.config, f, indent=4)
                
                # Atomically replace the original file
                os.replace(temp_path, self.config_path)
                
                self.logger.debug(f"Saved config to {self.config_path}")
                return True
            except Exception as e:
                self.logger.error(f"Error saving config: {str(e)}")
                return False
    
    def get_config(self):
        """Get the current configuration
        
        Returns:
            dict: The current configuration
        """
        with self.lock:
            return self.config
    
    def update_config(self, updates):
        """Update the configuration
        
        Args:
            updates (dict): The updates to apply to the configuration
            
        Returns:
            dict: The updated configuration
        """
        with self.lock:
            # Apply updates
            self._recursive_update(self.config, updates)
            
            # Save the updated configuration
            self.save_config()
            
            return self.config
    
    def _recursive_update(self, target, source):
        """Recursively update a dictionary
        
        Args:
            target (dict): The target dictionary
            source (dict): The source dictionary
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._recursive_update(target[key], value)
            else:
                target[key] = value
    
    def get_api_keys(self):
        """Get the OpenRouter API keys
        
        Returns:
            list: The OpenRouter API keys
        """
        # ALWAYS use environment variable first
        env_keys = os.getenv("OPENROUTER_API_KEYS")
        if env_keys:
            # Split by comma and strip whitespace
            return [key.strip() for key in env_keys.split(',') if key.strip()]
        
        # Fall back to config file only for non-secret values
        with self.lock:
            try:
                return [key['key'] for key in self.config['providers']['openrouter']['api_keys']]
            except (KeyError, TypeError):
                return []
    
    def get_encryption_key(self):
        """Get the encryption key
        
        Returns:
            str: The encryption key
        """
        # ALWAYS prioritize environment variable for secrets
        env_key = os.getenv("ENCRYPTION_KEY")
        if env_key:
            self.logger.debug("Using encryption key from environment variable.")
            return env_key
        
        # Log a security warning that environment variable should be used
        self.logger.warning("ENCRYPTION_KEY environment variable not set. This is a security risk.")
        
        # Fall back to file as a last resort
        try:
            with open('.encryption_key', 'r') as f:
                key = f.read().strip()
                self.logger.warning("Using encryption key from file. For better security, set the ENCRYPTION_KEY environment variable.")
                return key
        except Exception as e:
            self.logger.error(f"Failed to read encryption key: {str(e)}")
            return None