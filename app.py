#!/usr/bin/env python3

import os
import logging
from AppFactory import AppFactory
from utils.APIError import APIError
from flask import jsonify

# Create the application factory
factory = AppFactory()

# Create the Flask application
app = factory.create_app()

# Get logger
logger = logging.getLogger('ai_dashboard')

# Register global error handler for APIError
@app.errorhandler(APIError)
def handle_api_error(error):
    """Handle APIError exceptions
    
    Args:
        error (APIError): The APIError exception
        
    Returns:
        Response: JSON response with error details
    """
    response = jsonify({
        'error': error.message,
        'status_code': error.status_code
    })
    response.status_code = error.status_code
    return response

# Routes are now registered through blueprints in the routes/ directory
# See AppFactory._register_routes for details

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Log application start
    logger.info("AI Control Dashboard started")
    
    # Run the Flask app
    app.run(debug=False, host='0.0.0.0', port=5000)