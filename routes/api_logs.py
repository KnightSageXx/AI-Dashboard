from flask import Blueprint, jsonify, request
import os
from datetime import datetime
from utils.errors import wrap_api_exceptions
from utils.APIError import APIError

# Create blueprint
api_logs = Blueprint('api_logs', __name__)


def register_logs_routes():
    """
    Register log-related API routes
    
    Returns:
        Blueprint: The registered blueprint
    """
    
    @api_logs.route('/', methods=['GET'])
    @wrap_api_exceptions
    def get_logs():
        """Get logs from the log file"""
        # Get log file name from query parameter or use default
        log_file = request.args.get('file', 'status.log')
        limit = int(request.args.get('limit', 100))
        
        # Ensure the log file is in the logs directory for security
        if not log_file.endswith('.log') or '/' in log_file or '\\' in log_file:
            raise APIError("Invalid log file name", 400)
        
        # Ensure logs directory exists
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir)
            except Exception as mkdir_error:
                error_msg = f"Error creating logs directory: {str(mkdir_error)}"
                raise APIError(error_msg, 500)
        
        log_path = os.path.join(logs_dir, log_file)
        
        # If log file doesn't exist, create an empty one
        if not os.path.exists(log_path):
            try:
                with open(log_path, 'w') as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ai_dashboard - INFO - Log file created\n")
            except Exception as create_error:
                error_msg = f"Error creating log file {log_path}: {str(create_error)}"
                raise APIError(error_msg, 500)
        
        try:
            with open(log_path, 'r') as f:
                logs = f.readlines()
                # Get the last 'limit' log entries or all if less than 'limit'
                logs = logs[-limit:] if len(logs) > limit else logs
        except Exception as file_error:
            error_msg = f"Error reading log file {log_path}: {str(file_error)}"
            raise APIError(error_msg, 500)
        
        # Get available log files
        try:
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        except Exception as dir_error:
            error_msg = f"Error listing log files: {str(dir_error)}"
            log_files = [log_file] if os.path.exists(log_path) else []
        
        return jsonify({
            'logs': logs,
            'log_files': log_files,
            'current_file': log_file
        })
    
    return api_logs