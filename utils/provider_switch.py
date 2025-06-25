import os
import subprocess
import webbrowser
import logging

class ProviderSwitcher:
    """Manages switching between different AI providers"""
    
    def __init__(self, config_manager):
        """Initialize the ProviderSwitcher
        
        Args:
            config_manager (ConfigManager): The configuration manager
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger('ai_dashboard.provider_switcher')
    
    def switch_to(self, provider):
        """Switch to a different AI provider
        
        Args:
            provider (str): The provider to switch to (openrouter, ollama, phind)
            
        Returns:
            str: Message indicating the result of the switch
        """
        if provider not in ['openrouter', 'ollama', 'phind']:
            raise ValueError(f"Invalid provider: {provider}")
        
        config = self.config_manager.get_config()
        
        # Handle each provider type
        if provider == 'openrouter':
            return self._switch_to_openrouter()
        elif provider == 'ollama':
            return self._switch_to_ollama()
        elif provider == 'phind':
            return self._switch_to_phind()
    
    def _switch_to_openrouter(self):
        """Switch to OpenRouter provider
        
        Returns:
            str: Message indicating the result of the switch
        """
        config = self.config_manager.get_config()
        
        # Check if there are any active keys
        active_key = None
        for key in config['providers']['openrouter']['api_keys']:
            if key['is_active']:
                active_key = key
                break
        
        # If no active key, try to activate one
        if not active_key:
            from utils.key_rotator import KeyRotator
            key_rotator = KeyRotator(self.config_manager)
            result = key_rotator.rotate_key()
            
            # Check if rotation was successful
            if "Rotated to next API key" not in result and "using first key" not in result:
                return "Failed to switch to OpenRouter: No valid API key available"
            
            # Get the newly activated key
            for key in config['providers']['openrouter']['api_keys']:
                if key['is_active']:
                    active_key = key
                    break
        
        if not active_key:
            return "Failed to switch to OpenRouter: No valid API key available"
        
        # Update the Continue config
        model = config['providers']['openrouter']['default_model']
        self._update_continue_config('openrouter', active_key['key'], model)
        
        # Update the application config
        config['current_provider'] = 'openrouter'
        config['current_model'] = model
        self.config_manager.save_config()
        
        return f"Switched to OpenRouter with model {model}"
    
    def _switch_to_ollama(self):
        """Switch to Ollama provider
        
        Returns:
            str: Message indicating the result of the switch
        """
        config = self.config_manager.get_config()
        
        # Get Ollama configuration
        api_base = config['providers']['ollama']['api_base']
        model = config['providers']['ollama']['default_model']
        
        # Update the Continue config
        self._update_continue_config('ollama', None, model, api_base)
        
        # Update the application config
        config['current_provider'] = 'ollama'
        config['current_model'] = model
        self.config_manager.save_config()
        
        # Try to start Ollama if it's not running
        try:
            # Check if Ollama is running by making a request to the API
            import requests
            response = requests.get(f"{api_base}/api/tags")
            if response.status_code != 200:
                # Try to start Ollama
                self._start_ollama()
        except Exception as e:
            self.logger.warning(f"Failed to check Ollama status: {str(e)}")
            # Try to start Ollama anyway
            self._start_ollama()
        
        return f"Switched to Ollama with model {model}"
    
    def _start_ollama(self):
        """Try to start Ollama if it's not running"""
        try:
            # Check the operating system
            if os.name == 'nt':  # Windows
                # Start Ollama using subprocess
                subprocess.Popen(['ollama', 'serve'], 
                                 creationflags=subprocess.CREATE_NO_WINDOW,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            else:  # Unix/Linux/Mac
                # Start Ollama using subprocess
                subprocess.Popen(['ollama', 'serve'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            
            self.logger.info("Started Ollama server")
        except Exception as e:
            self.logger.error(f"Failed to start Ollama: {str(e)}")
    
    def _switch_to_phind(self):
        """Switch to Phind provider by opening it in a browser
        
        Returns:
            str: Message indicating the result of the switch
        """
        config = self.config_manager.get_config()
        
        # Get Phind URL
        phind_url = config['providers']['phind']['url']
        
        # Open Phind in the default browser
        try:
            webbrowser.open(phind_url)
            self.logger.info(f"Opened Phind in browser: {phind_url}")
        except Exception as e:
            self.logger.error(f"Failed to open Phind in browser: {str(e)}")
            return f"Failed to open Phind in browser: {str(e)}"
        
        # Update the application config
        config['current_provider'] = 'phind'
        self.config_manager.save_config()
        
        return f"Opened Phind in browser: {phind_url}"
    
    def update_model(self, model_id):
        """Update the model for the current provider
        
        Args:
            model_id (str): The model ID to use
            
        Returns:
            str: Message indicating the result of the update
        """
        config = self.config_manager.get_config()
        current_provider = config['current_provider']
        
        # Validate the model ID for the current provider
        valid_model = False
        if current_provider in ['openrouter', 'ollama']:
            for model in config['providers'][current_provider]['models']:
                if model['id'] == model_id:
                    valid_model = True
                    break
        
        if not valid_model and current_provider != 'phind':
            raise ValueError(f"Invalid model ID for {current_provider}: {model_id}")
        
        # Update the model in the config
        if current_provider == 'openrouter':
            config['providers']['openrouter']['default_model'] = model_id
            
            # Get the current active key
            active_key = None
            for key in config['providers']['openrouter']['api_keys']:
                if key['is_active']:
                    active_key = key
                    break
            
            if active_key:
                # Update the Continue config
                self._update_continue_config('openrouter', active_key['key'], model_id)
        
        elif current_provider == 'ollama':
            config['providers']['ollama']['default_model'] = model_id
            
            # Update the Continue config
            api_base = config['providers']['ollama']['api_base']
            self._update_continue_config('ollama', None, model_id, api_base)
        
        # Update the current model in the config
        config['current_model'] = model_id
        self.config_manager.save_config()
        
        return f"Updated model to {model_id}"
    
    def _update_continue_config(self, provider, api_key=None, model=None, api_base=None):
        """Update the Continue.dev configuration for the specified provider
        
        Args:
            provider (str): The provider to update
            api_key (str, optional): The API key to use (for OpenRouter)
            model (str, optional): The model to use
            api_base (str, optional): The API base URL (for Ollama)
        """
        # Get the current Continue config
        continue_config = self.config_manager.get_continue_config()
        if not continue_config:
            self.logger.error("Failed to get Continue config")
            return
        
        # Update the providers in the Continue config
        if 'providers' in continue_config:
            for provider_config in continue_config['providers']:
                # Update OpenRouter provider
                if provider == 'openrouter' and 'openrouter' in provider_config['id']:
                    if api_key:
                        provider_config['apiKey'] = api_key
                    if model:
                        provider_config['defaultModel'] = model
                
                # Update Ollama provider
                elif provider == 'ollama' and 'ollama' in provider_config['id']:
                    if api_base:
                        provider_config['apiBase'] = api_base
                    if model:
                        provider_config['defaultModel'] = model
        
        # Save the updated Continue config
        self.config_manager.update_continue_config(continue_config)