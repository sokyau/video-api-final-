from functools import wraps
from flask import request, jsonify
import jsonschema
import logging
from .error_handler import ValidationError

logger = logging.getLogger(__name__)

def validate_json(schema):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    logger.warning("Request without JSON body")
                    raise ValidationError("JSON body is required")
                
                try:
                    jsonschema.validate(instance=data, schema=schema)
                except jsonschema.exceptions.ValidationError as e:
                    path = ".".join(str(p) for p in e.path) if e.path else "data"
                    error_message = f"Validation error in {path}: {e.message}"
                    logger.warning(f"JSON validation failed: {error_message}")
                    raise ValidationError(error_message)
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "error": "validation_error",
                    "message": str(e)
                }), 400
                
        return decorated_function
    return decorator
