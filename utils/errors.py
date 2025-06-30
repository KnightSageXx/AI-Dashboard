import traceback
import logging
from functools import wraps
from flask import jsonify

logger = logging.getLogger('ai_dashboard.api')

def wrap_api_exceptions(func):
    """
    Decorator to wrap API endpoints and handle exceptions uniformly.
    
    This decorator catches any exceptions raised by the wrapped function,
    logs the error with a traceback, and returns a standardized JSON error
    response with a 500 status code.
    
    The response format is:
    {
        "success": true/false,
        "message": "...",
        "error": null/"error message",
        "data": {...}
    }
    
    Args:
        func: The function to wrap
        
    Returns:
        The wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # If the result is already a response object, return it as is
            if hasattr(result, 'status_code'):
                return result
            
            # If the result is a tuple with a status code, extract it
            status_code = 200
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
                result, status_code = result
            
            # If the result is already a dict with the expected format, return it
            if isinstance(result, dict) and 'success' in result:
                return jsonify(result), status_code
            
            # Otherwise, wrap the result in the standard format
            return jsonify({
                'success': True,
                'message': None,
                'error': None,
                'data': result
            }), status_code
            
        except Exception as e:
            # Log the error with traceback
            logger.error(f"API Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a standardized error response
            return jsonify({
                'success': False,
                'message': None,
                'error': str(e),
                'trace': traceback.format_exc()
            }), 500
    
    return wrapper