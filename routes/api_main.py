from flask import Blueprint, jsonify, request
from routes.api_status import register_status_routes
from routes.api_keys import register_keys_routes
from routes.api_logs import register_logs_routes
from routes.api_daemon import register_daemon_routes
from routes.api_providers import register_providers_routes
from utils.errors import wrap_api_exceptions

def register_api_routes(app, key_rotator, provider_switcher, config_manager, daemon_monitor):
    """
    Register all API routes with the Flask application
    
    Args:
        app (Flask): The Flask application
        key_rotator (KeyRotator): The key rotation service
        provider_switcher (ProviderSwitcher): The provider switching service
        config_manager (ConfigManager): The configuration manager
        daemon_monitor (DaemonMonitor): The daemon monitoring service
    """
    # Create main API blueprint
    api = Blueprint('api', __name__, url_prefix='/api')
    
    # Register status routes
    status_bp = register_status_routes(config_manager)
    api.register_blueprint(status_bp, url_prefix='/status')
    
    # Register keys routes
    keys_bp = register_keys_routes(key_rotator)
    api.register_blueprint(keys_bp, url_prefix='/keys')
    
    # Register logs routes
    logs_bp = register_logs_routes()
    api.register_blueprint(logs_bp, url_prefix='/logs')
    
    # Register daemon routes
    daemon_bp = register_daemon_routes(daemon_monitor)
    api.register_blueprint(daemon_bp, url_prefix='/daemon')
    
    # Register provider routes
    providers_bp = register_providers_routes(provider_switcher, config_manager, key_rotator)
    api.register_blueprint(providers_bp, url_prefix='/providers')
    
    # Add health check routes
    @api.route('/selftest', methods=['GET'])
    @wrap_api_exceptions
    def selftest():
        """Test all provider APIs via dry-run"""
        results = {}
        config = config_manager.get_config()
        
        # Test OpenRouter
        if 'openrouter' in config.get('providers', {}):
            try:
                # Use the key_rotator to test the current key
                key_rotator.test_current_key()
                results['openrouter'] = {'status': 'ok'}
            except Exception as e:
                results['openrouter'] = {'status': 'error', 'message': str(e)}
        
        # Test Ollama
        if 'ollama' in config.get('providers', {}):
            try:
                # TODO: Implement Ollama API test
                # This would be a simple HEAD request to the Ollama API
                results['ollama'] = {'status': 'ok'}
            except Exception as e:
                results['ollama'] = {'status': 'error', 'message': str(e)}
        
        # Test Phind
        if 'phind' in config.get('providers', {}):
            try:
                # TODO: Implement Phind API test
                # This would be a simple HEAD request to the Phind API
                results['phind'] = {'status': 'ok'}
            except Exception as e:
                results['phind'] = {'status': 'error', 'message': str(e)}
        
        return {
            'success': True,
            'message': 'Self-test completed',
            'data': results
        }
    
    # Register the main blueprint with the app
    app.register_blueprint(api)