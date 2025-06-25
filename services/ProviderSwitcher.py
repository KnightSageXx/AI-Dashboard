import os
import logging
import subprocess
import webbrowser
from utils.APIError import APIError

class ProviderSwitcher:
    """Service for switching between AI providers
    
    This class provides methods for switching between different AI providers,
    including OpenRouter, Ollama, and Phind, as well as updating the current
    model for the active provider.
    """
    
    def __init__(self, config_manager, key_rotator):
        """Initialize the ProviderSwitcher
        
        Args:
            config_manager (ConfigManager): The configuration manager
            key_rotator (KeyRotator): The key rotation service
        """
        self.logger = logging.getLogger('ai_dashboard.provider_switcher')
        self.config_manager = config_manager
        self.key_rotator = key_rotator
    
    def switch_to(self, provider):
        """Switch to the specified provider
        
        Args:
            provider (str): The provider to switch to
            
        Returns:
            str: A message indicating the result of the switch
            
        Raises:
            APIError: If the provider is invalid or the switch fails
        """
        if provider not in ['openrouter', 'ollama', 'phind']:
            raise APIError(f"Invalid provider: {provider}", 400)
        
        try:
            # Call the appropriate switch method
            if provider == 'openrouter':
                return self._switch_to_openrouter()
            elif provider == 'ollama':
                return self._switch_to_ollama()
            elif provider == 'phind':
                return self._switch_to_phind()
        except APIError as e:
            # Re-raise API errors
            raise e
        except Exception as e:
            self.logger.error(f"Error switching to {provider}: {str(e)}")
            raise APIError(f"Failed to switch to {provider}: {str(e)}", 500)
    
    def _switch_to_openrouter(self):
        """Switch to the OpenRouter provider
        
        Returns:
            str: A message indicating the result of the switch
            
        Raises:
            APIError: If the switch fails
        """
        try:
            # Get the configuration
            config = self.config_manager.get_config()
            
            # Check if there are any OpenRouter keys
            if not config['providers']['openrouter']['api_keys']:
                raise APIError("No OpenRouter API keys available", 404)
            
            # Find the active key or activate the first key
            active_key = None
            for key in config['providers']['openrouter']['api_keys']:
                if key['is_active']:
                    active_key = key
                    break
            
            # If no key is active, activate the first key
            if not active_key:
                config['providers']['openrouter']['api_keys'][0]['is_active'] = True
                active_key = config['providers']['openrouter']['api_keys'][0]
            
            # Update the current provider and model
            default_model = config['providers']['openrouter']['default_model']
            self.config_manager.update_config({
                'current_provider': 'openrouter',
                'current_model': default_model
            })
            
            # Update the Continue.dev configuration
            self._update_continue_config()
            
            return f"Switched to OpenRouter with model {default_model}"
        except APIError as e:
            # Re-raise API errors
            raise e
        except Exception as e:
            self.logger.error(f"Error switching to OpenRouter: {str(e)}")
            raise APIError(f"Failed to switch to OpenRouter: {str(e)}", 500)
    
    def _switch_to_ollama(self):
        """Switch to the Ollama provider
        
        Returns:
            str: A message indicating the result of the switch
            
        Raises:
            APIError: If the switch fails
        """
        try:
            # Get the configuration
            config = self.config_manager.get_config()
            
            # Update the current provider and model
            default_model = config['providers']['ollama']['default_model']
            self.config_manager.update_config({
                'current_provider': 'ollama',
                'current_model': default_model
            })
            
            # Update the Continue.dev configuration
            self._update_continue_config()
            
            # Try to start the Ollama server if it's not running
            try:
                self._start_ollama_server()
            except Exception as e:
                self.logger.warning(f"Failed to start Ollama server: {str(e)}")
            
            return f"Switched to Ollama with model {default_model}"
        except Exception as e:
            self.logger.error(f"Error switching to Ollama: {str(e)}")
            raise APIError(f"Failed to switch to Ollama: {str(e)}", 500)
    
    def _switch_to_phind(self):
        """Switch to the Phind provider
        
        Returns:
            str: A message indicating the result of the switch
            
        Raises:
            APIError: If the switch fails
        """
        try:
            # Get the configuration
            config = self.config_manager.get_config()
            
            # Update the current provider
            self.config_manager.update_config({
                'current_provider': 'phind',
                'current_model': 'phind'
            })
            
            # Open the Phind URL in a browser
            phind_url = config['providers']['phind']['url']
            webbrowser.open(phind_url)
            
            return f"Switched to Phind and opened {phind_url}"
        except Exception as e:
            self.logger.error(f"Error switching to Phind: {str(e)}")
            raise APIError(f"Failed to switch to Phind: {str(e)}", 500)
    
    def _start_ollama_server(self):
        """Start the Ollama server if it's not running
        
        Raises:
            Exception: If the server fails to start
        """
        try:
            # Check if the Ollama server is running
            import requests
            config = self.config_manager.get_config()
            api_base = config['providers']['ollama']['api_base']
            
            try:
                response = requests.get(f"{api_base}/api/tags", timeout=2)
                if response.status_code == 200:
                    self.logger.info("Ollama server is already running")
                    return
            except Exception:
                self.logger.info("Ollama server is not running, attempting to start")
            
            # Start the Ollama server
            if os.name == 'nt':  # Windows
                subprocess.Popen(
                    ['start', 'ollama', 'serve'],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:  # Linux/Mac
                subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            self.logger.info("Started Ollama server")
        except Exception as e:
            self.logger.error(f"Error starting Ollama server: {str(e)}")
            raise Exception(f"Failed to start Ollama server: {str(e)}")
    
    def update_model(self, model_id):
        """Update the current model for the active provider
        
        Args:
            model_id (str): The model ID to update to
            
        Returns:
            str: A message indicating the result of the update
            
        Raises:
            APIError: If the model is invalid or the update fails
        """
        try:
            # Get the configuration
            config = self.config_manager.get_config()
            current_provider = config['current_provider']
            
            # Validate the model ID
            if current_provider == 'openrouter':
                if model_id not in config['providers']['openrouter']['models']:
                    raise APIError(f"Invalid OpenRouter model: {model_id}", 400)
            elif current_provider == 'ollama':
                if model_id not in config['providers']['ollama']['models']:
                    raise APIError(f"Invalid Ollama model: {model_id}", 400)
            elif current_provider == 'phind':
                raise APIError("Cannot update model for Phind", 400)
            
            # Update the current model
            self.config_manager.update_config({
                'current_model': model_id
            })
            
            # Update the default model for the provider
            if current_provider == 'openrouter':
                self.config_manager.update_config({
                    'providers': {
                        'openrouter': {
                            'default_model': model_id
                        }
                    }
                })
            elif current_provider == 'ollama':
                self.config_manager.update_config({
                    'providers': {
                        'ollama': {
                            'default_model': model_id
                        }
                    }
                })
            
            # Update the Continue.dev configuration
            self._update_continue_config()
            
            return f"Updated model to {model_id}"
        except APIError as e:
            # Re-raise API errors
            raise e
        except Exception as e:
            self.logger.error(f"Error updating model: {str(e)}")
            raise APIError(f"Failed to update model: {str(e)}", 500)
    
    def _update_continue_config(self):
        """Update the Continue.dev configuration for the current provider
        
        Raises:
            APIError: If the update fails
        """
        try:
            # Get the configuration
            config = self.config_manager.get_config()
            current_provider = config['current_provider']
            current_model = config['current_model']
            
            # Get the Continue.dev configuration
            continue_config = self.config_manager.get_continue_config()
            
            if not continue_config:
                self.logger.warning("Continue.dev configuration not found")
                return
            
            # Update the Continue.dev configuration based on the provider
            if current_provider == 'openrouter':
                # Get the active key
                active_key = self.key_rotator.get_current_key()
                
                # Update the OpenRouter configuration
                continue_config.setdefault('models', {}).setdefault('openRouter', {})
                continue_config['models']['openRouter']['apiKey'] = active_key['key']
                continue_config['models']['openRouter']['defaultModel'] = current_model
                
                # Set OpenRouter as the default provider
                continue_config.setdefault('defaultModelProvider', 'openRouter')
            elif current_provider == 'ollama':
                # Update the Ollama configuration
                continue_config.setdefault('models', {}).setdefault('ollama', {})
                continue_config['models']['ollama']['apiBase'] = config['providers']['ollama']['api_base']
                continue_config['models']['ollama']['defaultModel'] = current_model
                
                # Set Ollama as the default provider
                continue_config.setdefault('defaultModelProvider', 'ollama')
            
            # Save the updated Continue.dev configuration
            self.config_manager.update_continue_config(continue_config)
        except APIError as e:
            # Re-raise API errors
            raise e
        except Exception as e:
            self.logger.error(f"Error updating Continue.dev configuration: {str(e)}")
            raise APIError(f"Failed to update Continue.dev configuration: {str(e)}", 500)