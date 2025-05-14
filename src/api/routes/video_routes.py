# src/api/routes/video_routes.py
from flask import Blueprint, request, jsonify
from ...services.video_service import add_captions_to_video, concatenate_videos_service
from ...services.image_service import process_meme_overlay
from ...services.animation_service import animated_text_service
from ..middlewares.authentication import require_api_key
from ..middlewares.request_validator import validate_json
import logging

logger = logging.getLogger(__name__)

video_bp = Blueprint('video', __name__, url_prefix='/api/v1/video')

caption_video_schema = {
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "subtitles_url": {"type": "string", "format": "uri"},
        "font": {"type": "string"},
        "font_size": {"type": "integer", "minimum": 12, "maximum": 72},
        "font_color": {"type": "string"},
        "background": {"type": "boolean"},
        "position": {"type": "string", "enum": ["bottom", "top", "center"]},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url", "subtitles_url"],
    "additionalProperties": False
}

meme_overlay_schema = {
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "meme_url": {"type": "string", "format": "uri"},
        "position": {
            "type": "string", 
            # Soporte para posiciones personalizadas y predefinidas
            "description": "Acepta formatos: 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center', o formato personalizado como 'x=50%,y=30%'"
        },
        "scale": {"type": "number", "minimum": 0.1, "maximum": 1.0},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url", "meme_url"],
    "additionalProperties": False
}

concatenate_schema = {
    "type": "object",
    "properties": {
        "video_urls": {
            "type": "array",
            "items": {"type": "string", "format": "uri"},
            "minItems": 2
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_urls"],
    "additionalProperties": False
}

animated_text_schema = {
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "text": {"type": "string"},
        "animation": {
            "type": "string",
            "enum": ["fade", "slide", "zoom", "typewriter", "bounce"]
        },
        "position": {
            "type": "string",
            "enum": ["top", "bottom", "center"]
        },
        "font": {"type": "string"},
        "font_size": {"type": "integer", "minimum": 12, "maximum": 120},
        "color": {"type": "string"},
        "duration": {"type": "number", "minimum": 1, "maximum": 20},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url", "text"],
    "additionalProperties": False
}

@video_bp.route('/caption', methods=['POST'])
@require_api_key
@validate_json(caption_video_schema)
def caption_video():
    """
    Endpoint para añadir subtítulos a un video.
    
    Request JSON:
    {
        "video_url": "https://example.com/video.mp4",
        "subtitles_url": "https://example.com/subtitles.srt",
        "font": "Arial",                  # opcional
        "font_size": 24,                  # opcional
        "font_color": "white",            # opcional
        "background": true,               # opcional
        "position": "bottom",             # opcional
        "webhook_url": "https://...",     # opcional
        "id": "job-123"                   # opcional
    }
    """
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        result = add_captions_to_video(
            video_url=data['video_url'],
            subtitles_url=data['subtitles_url'],
            font=data.get('font', 'Arial'),
            font_size=data.get('font_size', 24),
            font_color=data.get('font_color', 'white'),
            background=data.get('background', True),
            position=data.get('position', 'bottom'),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error processing video with subtitles: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500

@video_bp.route('/meme-overlay', methods=['POST'])
@require_api_key
@validate_json(meme_overlay_schema)
def meme_overlay():
    """
    Endpoint para añadir una imagen superpuesta a un video (meme).
    
    Request JSON:
    {
        "video_url": "https://example.com/video.mp4",
        "meme_url": "https://example.com/meme.png",
        "position": "bottom_right",       # opcional - también acepta 'x=50%,y=30%'
        "scale": 0.3,                     # opcional (0.1 a 1.0)
        "webhook_url": "https://...",     # opcional
        "id": "job-123"                   # opcional
    }
    """
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        result = process_meme_overlay(
            video_url=data['video_url'],
            meme_url=data['meme_url'],
            position=data.get('position', 'bottom_right'),
            scale=data.get('scale', 0.3),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error processing meme overlay: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500

@video_bp.route('/animated-text', methods=['POST'])
@require_api_key
@validate_json(animated_text_schema)
def animated_text():
    """
    Endpoint para añadir texto animado a un video.
    
    Request JSON:
    {
        "video_url": "https://example.com/video.mp4",
        "text": "Texto a animar",
        "animation": "fade",              # opcional
        "position": "bottom",             # opcional
        "font": "Arial",                  # opcional
        "font_size": 36,                  # opcional
        "color": "white",                 # opcional
        "duration": 3.0,                  # opcional
        "webhook_url": "https://...",     # opcional
        "id": "job-123"                   # opcional
    }
    """
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        result = animated_text_service(
            video_url=data['video_url'],
            text=data['text'],
            animation=data.get('animation', 'fade'),
            position=data.get('position', 'bottom'),
            font=data.get('font', 'Arial'),
            font_size=data.get('font_size', 36),
            color=data.get('color', 'white'),
            duration=data.get('duration', 3.0),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error processing animated text: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500

@video_bp.route('/concatenate', methods=['POST'])
@require_api_key
@validate_json(concatenate_schema)
def concatenate_videos():
    """
    Endpoint para concatenar múltiples videos.
    
    Request JSON:
    {
        "video_urls": [
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4",
            ...
        ],
        "webhook_url": "https://...",     # opcional
        "id": "job-123"                   # opcional
    }
    """
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        result = concatenate_videos_service(
            video_urls=data['video_urls'],
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error concatenating videos: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500
