from flask import Blueprint, jsonify
from utils.errors import wrap_api_exceptions

# Create blueprint
api_daemon = Blueprint('api_daemon', __name__)


def register_daemon_routes(daemon_monitor):
    """
    Register daemon-related API routes
    
    Args:
        daemon_monitor (DaemonMonitor): The daemon monitoring service
    
    Returns:
        Blueprint: The registered blueprint
    """
    
    @api_daemon.route('/status', methods=['GET'])
    @wrap_api_exceptions
    def daemon_status():
        """Get the current status of the daemon"""
        status = daemon_monitor.get_status()
        return jsonify({
            'success': True,
            'data': {
                'status': status['status'],
                'running': status['running'],
                'last_run': status['last_run'],
                'last_check': status['last_check']
            }
        })
    
    @api_daemon.route('/start', methods=['POST'])
    @wrap_api_exceptions
    def start_daemon():
        """Start the daemon"""
        result = daemon_monitor.start()
        message = "Daemon started" if result else "Daemon already running"
        return jsonify({'success': True, 'message': message})
    
    @api_daemon.route('/stop', methods=['POST'])
    @wrap_api_exceptions
    def stop_daemon():
        """Stop the daemon"""
        result = daemon_monitor.stop()
        message = "Daemon stopped" if result else "Daemon not running"
        return jsonify({'success': True, 'message': message})
    
    @api_daemon.route('/restart', methods=['POST'])
    @wrap_api_exceptions
    def restart_daemon():
        """Restart the daemon"""
        result = daemon_monitor.restart()
        return jsonify({'success': True, 'message': "Daemon restarted"})
    
    return api_daemon