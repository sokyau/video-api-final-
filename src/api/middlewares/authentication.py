from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning('API request without API key')
            return jsonify({
                "status": "error",
                "error": "authentication_error",
                "message": "API key is required"
            }), 401
        
        if api_key != current_app.config.get('API_KEY'):
            logger.warning(f'API request with invalid API key: {api_key[:5]}...')
            return jsonify({
                "status": "error",
                "error": "authentication_error",
                "message": "Invalid API key"
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function
