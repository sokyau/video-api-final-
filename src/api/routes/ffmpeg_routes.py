from flask import Blueprint, request, jsonify
from ...services.ffmpeg_service import get_media_info
from ..middlewares.authentication import require_api_key
from ..middlewares.request_validator import validate_json
import logging

logger = logging.getLogger(__name__)

ffmpeg_bp = Blueprint('ffmpeg', __name__, url_prefix='/api/v1/ffmpeg')

media_info_schema = {
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"}
    },
    "required": ["media_url"],
    "additionalProperties": False
}

@ffmpeg_bp.route('/media-info', methods=['POST'])
@require_api_key
@validate_json(media_info_schema)
def get_media_info_endpoint():
    from ...utils.file_utils import download_file
    from ...config import settings
    
    data = request.get_json()
    
    try:
        media_url = data['media_url']
        
        # Descargar archivo temporalmente
        media_path = download_file(media_url, settings.TEMP_DIR)
        
        # Obtener información
        media_info = get_media_info(media_path)
        
        # Limpiar archivo
        import os
        if os.path.exists(media_path):
            try:
                os.remove(media_path)
            except Exception as e:
                logger.warning(f"Error eliminando archivo temporal: {str(e)}")
        
        return jsonify({
            "status": "success",
            "result": media_info
        })
        
    except Exception as e:
        logger.exception(f"Error obteniendo información del medio: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500
