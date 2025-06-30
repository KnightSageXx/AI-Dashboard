from flask import Blueprint, jsonify, request
from utils.errors import wrap_api_exceptions
from utils.APIError import APIError

# Create blueprint
api_keys = Blueprint('api_keys', __name__)


def register_keys_routes(key_rotator):
    """
    Register key-related API routes
    
    Args:
        key_rotator (KeyRotator): The key rotation service
    
    Returns:
        Blueprint: The registered blueprint
    """
    
    @api_keys.route('/rotate', methods=['POST'])
    @wrap_api_exceptions
    def rotate_key():
        """Rotate to the next OpenRouter API key"""
        result = key_rotator.rotate()
        return jsonify({'success': True, 'message': result})
    
    @api_keys.route('/test', methods=['POST'])
    @wrap_api_exceptions
    def test_key():
        """Test the current OpenRouter API key"""
        result = key_rotator.test_current_key()
        return jsonify({'success': result['success'], 'message': result['message']})
    
    @api_keys.route('/add', methods=['POST'])
    @wrap_api_exceptions
    def add_key():
        """Add a new OpenRouter API key"""
        key = request.json.get('key')
        if not key:
            raise APIError("No API key provided", 400)
        
        result = key_rotator.add_key(key)
        return jsonify({'success': True, 'message': result})
    
    @api_keys.route('/check', methods=['POST'])
    @wrap_api_exceptions
    def check_and_rotate():
        """Check the current key and rotate if necessary"""
        rotated = key_rotator.check_and_rotate()
        message = "Key rotated" if rotated else "Key is valid, no rotation needed"
        return jsonify({'success': True, 'rotated': rotated, 'message': message})
    
    return api_keys