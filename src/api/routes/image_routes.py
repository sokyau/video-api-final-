from flask import Blueprint, request, jsonify
from ...services.image_service import overlay_image_on_video, generate_thumbnail
from ..middlewares.authentication import require_api_key
from ..middlewares.request_validator import validate_json
import logging

logger = logging.getLogger(__name__)

image_bp = Blueprint('image', __name__, url_prefix='/api/v1/image')

overlay_schema = {
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "image_url": {"type": "string", "format": "uri"},
        "position": {
            "type": "string",
            "enum": ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        },
        "scale": {"type": "number", "minimum": 0.1, "maximum": 1.0},
        "opacity": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url", "image_url"],
    "additionalProperties": False
}

thumbnail_schema = {
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "time": {"type": "number", "minimum": 0},
        "width": {"type": "integer", "minimum": 32, "maximum": 3840},
        "height": {"type": "integer", "minimum": 32, "maximum": 2160},
        "quality": {"type": "integer", "minimum": 1, "maximum": 100},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": False
}

@image_bp.route('/overlay', methods=['POST'])
@require_api_key
@validate_json(overlay_schema)
def overlay():
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        result = overlay_image_on_video(
            video_url=data['video_url'],
            image_url=data['image_url'],
            position=data.get('position', 'bottom_right'),
            scale=data.get('scale', 0.3),
            opacity=data.get('opacity', 1.0),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error overlaying image on video: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500

@image_bp.route('/thumbnail', methods=['POST'])
@require_api_key
@validate_json(thumbnail_schema)
def thumbnail():
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        result = generate_thumbnail(
            video_url=data['video_url'],
            time=data.get('time', 0),
            width=data.get('width', 640),
            height=data.get('height', 360),
            quality=data.get('quality', 90),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error generating thumbnail: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500
