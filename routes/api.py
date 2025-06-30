from flask import Blueprint, jsonify, request
from datetime import datetime
import os
from utils.APIError import APIError
from utils.temp_email import TempEmailAutomation

def register_api_routes(app, key_rotator, provider_switcher, config_manager):
    """Register API routes with the Flask application
    
    Args:
        app (Flask): The Flask application
        key_rotator (KeyRotator): The key rotation service
        provider_switcher (ProviderSwitcher): The provider switching service
        config_manager (ConfigManager): The configuration manager
    """
    # Create blueprint
    api = Blueprint('api', __name__, url_prefix='/api')
    
    # Get logger
    logger = app.logger
    
    @api.route('/status')
    def get_status():
        """Get the current status of the AI providers"""
        try:
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
                logger.error(f"Error accessing API keys: {str(key_error)}")
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
        except Exception as e:
            logger.error(f"/api/status failed: {str(e)}", exc_info=True)
            return jsonify({
                'current_provider': 'Error',
                'current_model': 'Unknown',
                'error': str(e)
            }), 500
    
    @api.route('/switch/<provider>', methods=['POST'])
    def switch_provider(provider):
        """Switch to a different AI provider"""
        if provider not in ['openrouter', 'ollama', 'phind']:
            raise APIError(f"Invalid provider: {provider}", 400)
        
        try:
            result = provider_switcher.switch_to(provider)
            logger.info(f"Switched to provider: {provider}")
            return jsonify({'success': True, 'message': result})
        except Exception as e:
            logger.error(f"Error switching to {provider}: {str(e)}")
            raise APIError(f"Failed to switch to {provider}: {str(e)}", 500)
    
    @api.route('/rotate', methods=['POST'])
    def rotate_key():
        """Rotate to the next OpenRouter API key"""
        try:
            result = key_rotator.rotate_key()
            logger.info("Rotated OpenRouter API key")
            return jsonify({'success': True, 'message': result})
        except Exception as e:
            logger.error(f"Error rotating API key: {str(e)}")
            raise APIError(f"Failed to rotate API key: {str(e)}", 500)
    
    @api.route('/test', methods=['POST'])
    def test_key():
        """Test the current OpenRouter API key"""
        try:
            result = key_rotator.test_current_key()
            return jsonify({'success': result['success'], 'message': result['message']})
        except Exception as e:
            logger.error(f"Error testing API key: {str(e)}")
            raise APIError(f"Failed to test API key: {str(e)}", 500)
    
    @api.route('/launch/phind', methods=['POST'])
    def launch_phind():
        """Launch Phind in browser"""
        try:
            result = provider_switcher.switch_to('phind')
            logger.info("Launched Phind in browser")
            return jsonify({'success': True, 'message': result})
        except Exception as e:
            logger.error(f"Error launching Phind: {str(e)}")
            raise APIError(f"Failed to launch Phind: {str(e)}", 500)
    
    @api.route('/temp_email', methods=['POST'])
    def create_temp_email():
        """Start the temp email automation process"""
        try:
            temp_email = TempEmailAutomation(config_manager, key_rotator)
            result = temp_email.start_automation()
            return jsonify({'success': True, 'message': result})
        except Exception as e:
            logger.error(f"Error in temp email automation: {str(e)}")
            raise APIError(f"Failed to create temp email: {str(e)}", 500)
    
    @api.route('/add_key', methods=['POST'])
    def add_key():
        """Add a new OpenRouter API key"""
        key = request.json.get('key')
        if not key:
            raise APIError("No API key provided", 400)
        
        try:
            result = key_rotator.add_key(key)
            logger.info(f"Added new OpenRouter API key")
            return jsonify({'success': True, 'message': result})
        except Exception as e:
            logger.error(f"Error adding API key: {str(e)}")
            raise APIError(f"Failed to add API key: {str(e)}", 500)
    
    @api.route('/update_model', methods=['POST'])
    def update_model():
        """Update the current model for the active provider"""
        model_id = request.json.get('model_id')
        if not model_id:
            raise APIError("No model ID provided", 400)
        
        try:
            result = provider_switcher.update_model(model_id)
            logger.info(f"Updated model to: {model_id}")
            return jsonify({'success': True, 'message': result})
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            raise APIError(f"Failed to update model: {str(e)}", 500)
    
    @api.route('/daemon/restart', methods=['POST'])
    def restart_daemon():
        """Restart the daemon process"""
        try:
            # This will be implemented in the daemon service
            # For now, just return success
            return jsonify({'success': True, 'message': 'Daemon restart requested'})
        except Exception as e:
            logger.error(f"Error restarting daemon: {str(e)}")
            raise APIError(f"Failed to restart daemon: {str(e)}", 500)
    
    @api.route('/settings', methods=['POST'])
    def update_settings():
        """Update settings"""
        try:
            settings = request.json
            if 'auto_rotate' in settings:
                config_manager.update_config({'auto_rotate': settings['auto_rotate']})
                logger.info(f"Auto-rotate set to: {settings['auto_rotate']}")
            
            return jsonify({
                'success': True, 
                'message': "Settings updated successfully"
            })
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            raise APIError(f"Failed to update settings: {str(e)}", 500)
    
    @api.route('/logs', methods=['GET'])
    def get_logs():
        """Get logs from the log file"""
        try:
            # Get log file name from query parameter or use default
            log_file = request.args.get('file', 'status.log')
            limit = int(request.args.get('limit', 100))
            
            # Ensure the log file is in the logs directory for security
            if not log_file.endswith('.log') or '/' in log_file or '\\' in log_file:
                logger.warning(f"Invalid log file name requested: {log_file}")
                raise APIError("Invalid log file name", 400)
            
            # Ensure logs directory exists
            logs_dir = 'logs'
            if not os.path.exists(logs_dir):
                try:
                    os.makedirs(logs_dir)
                    logger.info(f"Created logs directory: {logs_dir}")
                except Exception as mkdir_error:
                    error_msg = f"Error creating logs directory: {str(mkdir_error)}"
                    logger.error(error_msg, exc_info=True)
                    raise APIError(error_msg, 500)
            
            log_path = os.path.join(logs_dir, log_file)
            
            # If log file doesn't exist, create an empty one
            if not os.path.exists(log_path):
                try:
                    with open(log_path, 'w') as f:
                        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ai_dashboard - INFO - Log file created\n")
                    logger.info(f"Created new log file: {log_path}")
                except Exception as create_error:
                    error_msg = f"Error creating log file {log_path}: {str(create_error)}"
                    logger.error(error_msg, exc_info=True)
                    raise APIError(error_msg, 500)
            
            try:
                with open(log_path, 'r') as f:
                    logs = f.readlines()
                    # Get the last 'limit' log entries or all if less than 'limit'
                    logs = logs[-limit:] if len(logs) > limit else logs
            except Exception as file_error:
                error_msg = f"Error reading log file {log_path}: {str(file_error)}"
                logger.error(error_msg, exc_info=True)
                raise APIError(error_msg, 500)
            
            # Get available log files
            try:
                log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
            except Exception as dir_error:
                error_msg = f"Error listing log files: {str(dir_error)}"
                logger.error(error_msg, exc_info=True)
                log_files = [log_file] if os.path.exists(log_path) else []
            
            return jsonify({
                'logs': logs,
                'log_files': log_files,
                'current_file': log_file
            })
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}", exc_info=True)
            return jsonify({'logs': [f"Error: {str(e)}"], 'error': True})
    
    # Register the blueprint with the app
    app.register_blueprint(api)