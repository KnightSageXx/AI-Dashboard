import os
import logging
from flask import Flask
from datetime import datetime
from services.KeyRotator import KeyRotator
from services.ProviderSwitcher import ProviderSwitcher
from services.Daemon import DaemonMonitor
from utils.Logger import setup_logger
from utils.Encryption import EncryptionManager
from utils.Validator import APIKeyValidator
from config.ConfigManager import ConfigManager

class AppFactory:
    """Factory class for creating and configuring the application components"""
    
    def __init__(self, config_path='config/config.json'):
        """Initialize the AppFactory
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Create necessary directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('config', exist_ok=True)
        
        # Setup logging
        self.logger = setup_logger('ai_dashboard', 'logs/app.log')
        self.logger.info("Initializing AppFactory")
        
        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.encryption_manager = EncryptionManager()
        self.validator = APIKeyValidator()
        
        # Initialize services
        self.key_rotator = KeyRotator(self.config_manager, self.encryption_manager, self.validator)
        self.provider_switcher = ProviderSwitcher(self.config_manager, self.key_rotator)
        self.daemon = DaemonMonitor(self.config_manager, self.key_rotator, self.provider_switcher)
    
    def create_app(self):
        """Create and configure the Flask application
        
        Returns:
            Flask: The configured Flask application
        """
        app = Flask(__name__, 
                  template_folder='templates',
                  static_folder='static')
        
        # Register routes and configure the app
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app):
        """Register routes with the Flask application
        
        Args:
            app (Flask): The Flask application
        """
        from routes.dashboard import register_dashboard_routes
        from routes.api_main import register_api_routes
        
        # Register route blueprints
        register_dashboard_routes(app, self.config_manager)
        register_api_routes(app, self.key_rotator, self.provider_switcher, self.config_manager, self.daemon)
        
        # Add template context processor for common variables
        @app.context_processor
        def inject_common_variables():
            return {
                'year': datetime.now().year
            }
        
        # Add error handlers
        @app.errorhandler(404)
        def page_not_found(e):
            return "Page not found", 404
        
        @app.errorhandler(500)
        def server_error(e):
            self.logger.error(f"Server error: {str(e)}")
            return "Internal server error", 500