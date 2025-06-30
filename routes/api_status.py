from flask import Blueprint, jsonify
from datetime import datetime
from utils.errors import wrap_api_exceptions

# Create blueprint
api_status = Blueprint('api_status', __name__)


def register_status_routes(config_manager):
    """
    Register status-related API routes
    
    Args:
        config_manager (ConfigManager): The configuration manager
    
    Returns:
        Blueprint: The registered blueprint
    """
    
    @api_status.route('/')
    @wrap_api_exceptions
    def get_status():
        """Get the current status of the AI providers"""
        # Ensure config exists
        config = config_manager.get_config() or {}
        
        # Get active OpenRouter key
        active_key = None
        try:
            if 'providers' in config and 'openrouter' in config['providers'] and 'api_keys' in config['providers']['openrouter']:
                for key in config['providers']['openrouter']['api_keys']:
                    if key.get('is_active', False):
                        active_key = key
                        break
        except (KeyError, TypeError, AttributeError) as key_error:
            active_key = None
        
        # Format the key for display (mask except first/last 4 chars)
        masked_key = None
        if active_key and active_key.get('key'):
            key_str = active_key['key']
            if len(key_str) > 8:
                masked_key = f"{key_str[:4]}...{key_str[-4:]}"
            else:
                masked_key = "****"
        
        # Safely get values with defaults
        current_provider = config.get('current_provider', 'Unknown')
        current_model = config.get('current_model', 'Unknown')
        auto_rotate = config.get('auto_rotate', False)
        
        # Safely count keys
        try:
            total_keys = len(config['providers']['openrouter']['api_keys'])
            active_keys = sum(1 for k in config['providers']['openrouter']['api_keys'] if k.get('is_active'))
        except (KeyError, TypeError):
            total_keys = 0
            active_keys = 0
        
        status = {
            'current_provider': current_provider,
            'current_model': current_model,
            'active_key': masked_key,
            'last_used': active_key.get('last_used') if active_key else None,
            'error_count': active_key.get('error_count', 0) if active_key else 0,
            'total_keys': total_keys,
            'active_keys': active_keys,
            'auto_rotate': auto_rotate,
            'last_check': datetime.now().isoformat()
        }
        
        return jsonify(status)
    
    @api_status.route('/keys')
    @wrap_api_exceptions
    def get_key_status():
        """Get the status of all OpenRouter API keys"""
        config = config_manager.get_config() or {}
        
        # Get all keys
        keys = []
        try:
            if 'providers' in config and 'openrouter' in config['providers'] and 'api_keys' in config['providers']['openrouter']:
                for i, key in enumerate(config['providers']['openrouter']['api_keys']):
                    key_str = key.get('key', '')
                    masked_key = f"{key_str[:6]}...{key_str[-4:]}" if len(key_str) > 10 else "****"
                    
                    keys.append({
                        'index': i,
                        'key': masked_key,
                        'status': 'active' if key.get('is_active', False) else 'inactive',
                        'last_used': key.get('last_used', 'N/A'),
                        'error_count': key.get('error_count', 0),
                    })
        except (KeyError, TypeError, AttributeError):
            pass
        
        return jsonify({
            'success': True,
            'data': {
                'keys': keys
            }
        })
    
    return api_status