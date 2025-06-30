import time
import logging
import threading
from utils.APIError import APIError

class DaemonMonitor:
    """Service for monitoring and auto-rotating API keys in the background
    
    This class provides a daemon thread that periodically checks the status of
    the current API key and rotates it if necessary. It uses threading.Event for
    clean thread termination and RLock for thread-safety.
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
        
        # Thread management
        self.daemon_thread = None
        self.stop_event = threading.Event()
        self.lock = threading.RLock()
        
        # Status tracking
        self.status = 'stopped'
        self.last_check_time = 0
        self.last_run_time = None
    
    def start(self):
        """Start the daemon thread
        
        Returns:
            bool: True if the daemon was started, False if it was already running
        """
        with self.lock:
            if self.daemon_thread and self.daemon_thread.is_alive():
                self.logger.info("Daemon is already running")
                return False
            
            self.stop_event.clear()
            self.daemon_thread = threading.Thread(target=self._daemon_loop, daemon=True)
            self.daemon_thread.start()
            self.status = 'running'
            self.logger.info("Started daemon thread")
            return True
    
    def stop(self):
        """Stop the daemon thread
        
        Returns:
            bool: True if the daemon was stopped, False if it was not running
        """
        with self.lock:
            if not self.daemon_thread or not self.daemon_thread.is_alive():
                self.logger.info("Daemon is not running")
                self.status = 'stopped'
                return False
            
            self.logger.info("Stopping daemon thread...")
            self.stop_event.set()
            
            # Wait for the thread to terminate
            self.daemon_thread.join(timeout=5)
            
            # Check if the thread is still alive
            if self.daemon_thread.is_alive():
                self.logger.warning("Daemon thread did not terminate within timeout")
                self.status = 'hung'
            else:
                self.logger.info("Daemon thread stopped successfully")
                self.status = 'stopped'
            
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
        with self.lock:
            return self.daemon_thread is not None and self.daemon_thread.is_alive()
    
    def get_status(self):
        """Get the current status of the daemon
        
        Returns:
            dict: The current status
        """
        with self.lock:
            return {
                'status': self.status,
                'running': self.is_running(),
                'last_run': self.last_run_time,
                'last_check': self.last_check_time
            }
    
    def _daemon_loop(self):
        """The main daemon loop
        
        This method runs in a separate thread and periodically checks the status
        of the current API key, rotating it if necessary.
        """
        self.logger.info("Daemon loop started")
        
        while not self.stop_event.is_set():
            try:
                # Update last run time
                with self.lock:
                    self.last_run_time = time.time()
                
                # Get the current configuration
                config = self.config_manager.get_config()
                
                # Check if auto-rotate is enabled
                if not config.get('auto_rotate', False):
                    self.logger.debug("Auto-rotate is disabled, skipping check")
                    # Wait for stop event or timeout
                    if self.stop_event.wait(timeout=60):  # 1 minute
                        break
                    continue
                
                # Check if the current provider is OpenRouter
                if config.get('current_provider') != 'openrouter':
                    self.logger.debug(f"Current provider is not OpenRouter, skipping check")
                    # Wait for stop event or timeout
                    if self.stop_event.wait(timeout=60):  # 1 minute
                        break
                    continue
                
                # Get the check interval
                check_interval = config.get('check_interval_seconds', 300)  # Default: 5 minutes
                
                # Check if it's time to check the key
                current_time = time.time()
                if current_time - self.last_check_time < check_interval:
                    # Not time to check yet, wait for a bit
                    if self.stop_event.wait(timeout=10):  # 10 seconds
                        break
                    continue
                
                # Update the last check time
                with self.lock:
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
            
            # Wait for stop event or timeout
            if self.stop_event.wait(timeout=10):  # 10 seconds
                break
        
        with self.lock:
            self.status = 'stopped'
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