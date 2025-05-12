from flask import Blueprint, request, jsonify
from ...services.media_service import extract_audio, transcribe_media
from ..middlewares.authentication import require_api_key
from ..middlewares.request_validator import validate_json
import logging

logger = logging.getLogger(__name__)

media_bp = Blueprint('media', __name__, url_prefix='/api/v1/media')

media_to_mp3_schema = {
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "bitrate": {"type": "string", "pattern": "^[0-9]+k$"},
        "format": {"type": "string", "enum": ["mp3", "wav", "aac", "flac"]},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
}

transcribe_schema = {
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "language": {"type": "string", "minLength": 2, "maxLength": 5},
        "output_format": {"type": "string", "enum": ["txt", "srt", "vtt", "json"]},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
}

@media_bp.route('/media-to-mp3', methods=['POST'])
@require_api_key
@validate_json(media_to_mp3_schema)
def media_to_mp3():
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        result = extract_audio(
            media_url=data['media_url'],
            bitrate=data.get('bitrate', '192k'),
            format=data.get('format', 'mp3'),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error extracting audio: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500

@media_bp.route('/transcribe', methods=['POST'])
@require_api_key
@validate_json(transcribe_schema)
def transcribe():
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        result = transcribe_media(
            media_url=data['media_url'],
            language=data.get('language', 'auto'),
            output_format=data.get('output_format', 'txt'),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error transcribing media: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500
