import time
import logging
import threading
from utils.APIError import APIError

class DaemonMonitor:
    """Service for monitoring and auto-rotating API keys in the background
    
    This class provides a daemon thread that periodically checks the status of
    the current API key and rotates it if necessary.
    """
    
    def __init__(self, config_manager, key_rotator, provider_switcher):
        """Initialize the DaemonMonitor
        
        Args:
            config_manager (ConfigManager): The configuration manager
            key_rotator (KeyRotator): The key rotation service
            provider_switcher (ProviderSwitcher): The provider switching service
        """
        self.logger = logging.getLogger('ai_dashboard.daemon')
        self.config_manager = config_manager
        self.key_rotator = key_rotator
        self.provider_switcher = provider_switcher
        self.daemon_thread = None
        self.running = False
        self.last_check_time = 0
    
    def start(self):
        """Start the daemon thread
        
        Returns:
            bool: True if the daemon was started, False if it was already running
        """
        if self.running:
            self.logger.info("Daemon is already running")
            return False
        
        self.running = True
        self.daemon_thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self.daemon_thread.start()
        self.logger.info("Started daemon thread")
        return True
    
    def stop(self):
        """Stop the daemon thread
        
        Returns:
            bool: True if the daemon was stopped, False if it was not running
        """
        if not self.running:
            self.logger.info("Daemon is not running")
            return False
        
        self.running = False
        if self.daemon_thread and self.daemon_thread.is_alive():
            self.daemon_thread.join(timeout=5)
        self.logger.info("Stopped daemon thread")
        return True
    
    def restart(self):
        """Restart the daemon thread
        
        Returns:
            bool: True if the daemon was restarted
        """
        self.stop()
        return self.start()
    
    def is_running(self):
        """Check if the daemon is running
        
        Returns:
            bool: True if the daemon is running
        """
        return self.running and self.daemon_thread and self.daemon_thread.is_alive()
    
    def _daemon_loop(self):
        """The main daemon loop
        
        This method runs in a separate thread and periodically checks the status
        of the current API key, rotating it if necessary.
        """
        self.logger.info("Daemon loop started")
        
        while self.running:
            try:
                # Get the current configuration
                config = self.config_manager.get_config()
                
                # Check if auto-rotate is enabled
                if not config.get('auto_rotate', False):
                    self.logger.debug("Auto-rotate is disabled, skipping check")
                    time.sleep(60)  # Sleep for 1 minute before checking again
                    continue
                
                # Check if the current provider is OpenRouter
                if config.get('current_provider') != 'openrouter':
                    self.logger.debug(f"Current provider is not OpenRouter, skipping check")
                    time.sleep(60)  # Sleep for 1 minute before checking again
                    continue
                
                # Get the check interval
                check_interval = config.get('check_interval_seconds', 300)  # Default: 5 minutes
                
                # Check if it's time to check the key
                current_time = time.time()
                if current_time - self.last_check_time < check_interval:
                    # Not time to check yet, sleep for a bit
                    time.sleep(10)  # Sleep for 10 seconds before checking again
                    continue
                
                # Update the last check time
                self.last_check_time = current_time
                
                # Get the current key status
                current_key = self.key_rotator.get_current_key()
                if not current_key:
                    self.logger.warning("No current key found, trying to rotate")
                    self._handle_key_rotation()
                    continue
                
                # Check if the key has too many errors
                max_error_count = config.get('max_error_count', 3)  # Default: 3 errors
                if current_key.get('error_count', 0) >= max_error_count:
                    self.logger.warning(f"Current key has {current_key.get('error_count')} errors, rotating")
                    self._handle_key_rotation()
                    continue
                
                # Test the current key
                try:
                    self.key_rotator.test_current_key()
                    self.logger.debug("Current key is valid")
                except Exception as e:
                    self.logger.warning(f"Error testing current key: {str(e)}")
                    self._handle_key_rotation()
            
            except Exception as e:
                self.logger.error(f"Error in daemon loop: {str(e)}")
            
            # Sleep for a bit before checking again
            time.sleep(10)
        
        self.logger.info("Daemon loop stopped")
    
    def _handle_key_rotation(self):
        """Handle key rotation
        
        This method attempts to rotate the current key, and if that fails,
        it tries to switch to Ollama or Phind.
        """
        try:
            # Try to rotate the key
            self.key_rotator.rotate()
            self.logger.info("Successfully rotated key")
        except Exception as e:
            self.logger.error(f"Failed to rotate key: {str(e)}")
            
            # Try to switch to Ollama
            try:
                self.logger.info("Trying to switch to Ollama")
                self.provider_switcher.switch_to('ollama')
                self.logger.info("Successfully switched to Ollama")
            except Exception as e:
                self.logger.error(f"Failed to switch to Ollama: {str(e)}")
                
                # Try to switch to Phind
                try:
                    self.logger.info("Trying to switch to Phind")
                    self.provider_switcher.switch_to('phind')
                    self.logger.info("Successfully switched to Phind")
                except Exception as e:
                    self.logger.error(f"Failed to switch to Phind: {str(e)}")
                    # At this point, we've tried everything, so just log the error
                    self.logger.critical("Failed to rotate key or switch providers")