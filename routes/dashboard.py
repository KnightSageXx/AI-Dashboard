from flask import Blueprint, render_template, request
from datetime import datetime
import os

def register_dashboard_routes(app, config_manager):
    """Register dashboard routes with the Flask application
    
    Args:
        app (Flask): The Flask application
        config_manager (ConfigManager): The configuration manager
    """
    # Create blueprint
    dashboard = Blueprint('dashboard', __name__)
    
    @dashboard.route('/')
    def index():
        """Render the main dashboard page"""
        config = config_manager.get_config()
        return render_template('index.html', config=config, year=datetime.now().year)
    
    @dashboard.route('/logs')
    def view_logs():
        """Render the logs page"""
        try:
            # Get all log files
            log_files = [f for f in os.listdir('logs') if f.endswith('.log')]
            selected_log = 'app.log'  # Default log file
            
            # Get the requested log file from query parameter
            if 'file' in request.args and request.args['file'] in log_files:
                selected_log = request.args['file']
            
            # Read the log file
            with open(f'logs/{selected_log}', 'r') as f:
                logs = f.readlines()
                # Get the last 100 log entries or all if less than 100
                logs = logs[-100:] if len(logs) > 100 else logs
        except FileNotFoundError:
            logs = ["No logs found."]
            log_files = []
        
        return render_template('logs.html', logs=logs, log_files=log_files, selected_log=selected_log, year=datetime.now().year)
    
    @dashboard.route('/modal-test')
    def modal_test():
        """Render the modal test page"""
        return render_template('modal-test.html', year=datetime.now().year)
    
    # Register the blueprint with the app
    app.register_blueprint(dashboard)