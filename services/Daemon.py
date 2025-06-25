import time
import logging
import threading
from datetime import datetime, timedelta
from utils.APIError import APIError

class DaemonMonitor:
    """Background daemon for monitoring and auto-rotating API keys
    
    This class provides a background daemon that periodically checks the current
    OpenRouter API key and rotates it if necessary, based on the auto-rotate
    setting and the maximum error count.
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
        self.running = False
        self.thread = None
    
    def run(self):
        """Run the daemon
        
        This method starts the daemon loop in a separate thread.
        """
        if self.running:
            self.logger.warning("Daemon is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._daemon_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("Daemon started")
    
    def stop(self):
        """Stop the daemon
        
        This method stops the daemon loop.
        """
        if not self.running:
            self.logger.warning("Daemon is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        self.logger.info("Daemon stopped")
    
    def restart(self):
        """Restart the daemon
        
        This method stops and then starts the daemon loop.
        """
        self.stop()
        self.run()
        
        self.logger.info("Daemon restarted")
    
    def _daemon_loop(self):
        """The main daemon loop
        
        This method runs in a separate thread and periodically checks the current
        OpenRouter API key, rotating it if necessary.
        """
        self.logger.info("Daemon loop started")
        
        try:
            while self.running:
                try:
                    # Get the configuration
                    config = self.config_manager.get_config()
                    check_interval = config.get('check_interval_seconds', 300)
                    auto_rotate = config.get('auto_rotate', True)
                    max_error_count = config.get('max_error_count', 3)
                    current_provider = config.get('current_provider', 'openrouter')
                    
                    # Only check OpenRouter keys
                    if current_provider == 'openrouter' and auto_rotate:
                        self._check_openrouter_key(max_error_count)
                    
                    # Sleep for the check interval
                    time.sleep(check_interval)
                except Exception as e:
                    self.logger.error(f"Error in daemon loop: {str(e)}")
                    time.sleep(60)  # Sleep for 1 minute on error
        except KeyboardInterrupt:
            self.logger.info("Daemon loop interrupted")
        finally:
            self.running = False
            self.logger.info("Daemon loop stopped")
    
    def _check_openrouter_key(self, max_error_count):
        """Check the current OpenRouter API key
        
        This method checks the current OpenRouter API key and rotates it if
        necessary, based on the maximum error count.
        
        Args:
            max_error_count (int): The maximum error count before rotating
        """
        try:
            # Get the current key
            current_key = self.key_rotator.get_current_key()
            
            # Check if the key has exceeded the maximum error count
            if current_key['error_count'] >= max_error_count:
                self.logger.warning(
                    f"Key error count ({current_key['error_count']}) "
                    f"exceeds maximum ({max_error_count}), rotating"
                )
                self.key_rotator.rotate_key()
                return
            
            # Test the key
            result = self.key_rotator.test_current_key()
            
            # If the test failed, check if we need to rotate
            if not result['success']:
                current_key = self.key_rotator.get_current_key()  # Get updated key
                if current_key['error_count'] >= max_error_count:
                    self.logger.warning(
                        f"Key error count ({current_key['error_count']}) "
                        f"exceeds maximum ({max_error_count}), rotating"
                    )
                    try:
                        self.key_rotator.rotate_key()
                    except APIError as e:
                        # If rotation fails, try to switch to Ollama
                        self.logger.warning(f"Key rotation failed: {str(e)}")
                        self.logger.warning("Switching to Ollama as fallback")
                        try:
                            self.provider_switcher.switch_to('ollama')
                        except Exception as e2:
                            # If Ollama fails, try to switch to Phind
                            self.logger.warning(f"Switch to Ollama failed: {str(e2)}")
                            self.logger.warning("Switching to Phind as fallback")
                            try:
                                self.provider_switcher.switch_to('phind')
                            except Exception as e3:
                                self.logger.error(f"Switch to Phind failed: {str(e3)}")
        except Exception as e:
            self.logger.error(f"Error checking OpenRouter key: {str(e)}")