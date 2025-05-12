from flask import Blueprint, jsonify, current_app, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import os
import json
import logging

logger = logging.getLogger(__name__)

# Blueprint for serving OpenAPI spec
api_spec_bp = Blueprint('api_spec', __name__)

@api_spec_bp.route('/api/v1/spec', methods=['GET'])
def get_api_spec():
    """Serve the OpenAPI specification as JSON."""
    try:
        # Path to the OpenAPI spec file
        spec_path = os.path.join(os.path.dirname(__file__), 'openapi.json')
        
        # If spec file exists, return it
        if os.path.exists(spec_path):
            with open(spec_path, 'r') as f:
                return jsonify(json.load(f))
        
        # Otherwise return a basic spec
        return jsonify({
            "openapi": "3.0.0",
            "info": {
                "title": "Video Processing API",
                "description": "API for video, audio, and image processing operations",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": "/api/v1",
                    "description": "API v1"
                }
            ],
            "paths": {
                "/video/caption": {"post": {"summary": "Add captions to a video"}},
                "/video/meme-overlay": {"post": {"summary": "Add a meme overlay to a video"}},
                "/video/animated-text": {"post": {"summary": "Add animated text to a video"}},
                "/video/concatenate": {"post": {"summary": "Concatenate multiple videos"}},
                "/media/media-to-mp3": {"post": {"summary": "Convert media to MP3"}},
                "/media/transcribe": {"post": {"summary": "Transcribe audio from media"}},
                "/image/overlay": {"post": {"summary": "Overlay an image on a video"}},
                "/image/thumbnail": {"post": {"summary": "Generate thumbnail from a video"}},
                "/system/health": {"get": {"summary": "Check API health status"}},
                "/system/version": {"get": {"summary": "Get API version information"}},
                "/system/status": {"get": {"summary": "Get detailed system status"}},
                "/system/cleanup": {"post": {"summary": "Clean up temporary files"}}
            }
        })
    except Exception as e:
        logger.exception(f"Error serving API spec: {str(e)}")
        return jsonify({"error": "Could not load API specification"}), 500

# Create Swagger UI Blueprint
swagger_ui_bp = get_swaggerui_blueprint(
    '/api/docs',  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    '/api/v1/spec',  # Route for the OpenAPI specification
    config={
        'app_name': "Video Processing API",
        'validatorUrl': None  # Disable validation
    }
)

def register_docs(app):
    """Register all documentation-related blueprints with the Flask app."""
    app.register_blueprint(api_spec_bp)
    app.register_blueprint(swagger_ui_bp)
    
    logger.info("API documentation registered at /api/docs")
