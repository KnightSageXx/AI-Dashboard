from flask import Blueprint, jsonify, request
from utils.errors import wrap_api_exceptions
from utils.APIError import APIError
from utils.temp_email import TempEmailAutomation

# Create blueprint
api_providers = Blueprint('api_providers', __name__)


def register_providers_routes(provider_switcher, config_manager, key_rotator=None):
    """
    Register provider-related API routes
    
    Args:
        provider_switcher (ProviderSwitcher): The provider switching service
        config_manager (ConfigManager): The configuration manager
    
    Returns:
        Blueprint: The registered blueprint
    """
    
    @api_providers.route('/switch/<provider>', methods=['POST'])
    @wrap_api_exceptions
    def switch_provider(provider):
        """Switch to a different AI provider"""
        if provider not in ['openrouter', 'ollama', 'phind']:
            raise APIError(f"Invalid provider: {provider}", 400)
        
        result = provider_switcher.switch_to(provider)
        return jsonify({'success': True, 'message': result})
    
    @api_providers.route('/launch/phind', methods=['POST'])
    @wrap_api_exceptions
    def launch_phind():
        """Launch Phind in browser"""
        result = provider_switcher.switch_to('phind')
        return jsonify({'success': True, 'message': result})
    
    @api_providers.route('/update_model', methods=['POST'])
    @wrap_api_exceptions
    def update_model():
        """Update the current model for the active provider"""
        model_id = request.json.get('model_id')
        if not model_id:
            raise APIError("No model ID provided", 400)
        
        result = provider_switcher.update_model(model_id)
        return jsonify({'success': True, 'message': result})
    
    @api_providers.route('/settings', methods=['POST'])
    @wrap_api_exceptions
    def update_settings():
        """Update settings"""
        settings = request.json
        if 'auto_rotate' in settings:
            config_manager.update_config({'auto_rotate': settings['auto_rotate']})
        
        return jsonify({
            'success': True, 
            'message': "Settings updated successfully"
        })
    
    @api_providers.route('/temp_email', methods=['POST'])
    @wrap_api_exceptions
    def create_temp_email():
        """Start the temp email automation process"""
        if key_rotator is None:
            raise APIError("Key rotator not available", 500)
            
        temp_email = TempEmailAutomation(config_manager, key_rotator)
        result = temp_email.start_automation()
        return jsonify({'success': True, 'message': result})
    
    return api_providers