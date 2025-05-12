from flask import jsonify
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API exceptions"""
    status_code = 500
    error_type = "server_error"
    
    def __init__(self, message=None, status_code=None):
        self.message = message or "An unexpected error occurred"
        if status_code is not None:
            self.status_code = status_code
        logger.error(f"{self.__class__.__name__}: {self.message}")
        super().__init__(self.message)

class ValidationError(APIError):
    """Exception raised for validation errors"""
    status_code = 400
    error_type = "validation_error"

class ProcessingError(APIError):
    """Exception raised for processing errors"""
    status_code = 500
    error_type = "processing_error"

class NotFoundError(APIError):
    """Exception raised for resource not found errors"""
    status_code = 404
    error_type = "not_found_error"

def handle_api_error(error):
    response = {
        "status": "error",
        "error": error.error_type,
        "message": error.message
    }
    return jsonify(response), error.status_code

def register_error_handlers(app):
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(ValidationError, handle_api_error)
    app.register_error_handler(ProcessingError, handle_api_error)
    app.register_error_handler(NotFoundError, handle_api_error)
