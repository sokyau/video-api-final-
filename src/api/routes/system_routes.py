from flask import Blueprint, jsonify, current_app
from ...services.redis_queue_service import get_queue_stats
from ...services.cleanup_service import cleanup_temp_files
from ..middlewares.authentication import require_api_key
import logging
import os
import platform
import psutil

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__, url_prefix='/api/v1/system')

@system_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "environment": current_app.config.get('ENVIRONMENT', 'production'),
        "version": "1.0.0"
    })

@system_bp.route('/version', methods=['GET'])
def version():
    return jsonify({
        "version": "1.0.0",
        "api_version": "v1",
        "python_version": platform.python_version(),
        "platform": platform.platform()
    })

@system_bp.route('/status', methods=['GET'])
@require_api_key
def status():
    try:
        disk_usage = psutil.disk_usage('/')
        memory_usage = psutil.virtual_memory()
        
        queue_stats = get_queue_stats()
        
        return jsonify({
            "status": "operational",
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory": {
                    "total": memory_usage.total,
                    "available": memory_usage.available,
                    "percent": memory_usage.percent
                },
                "disk": {
                    "total": disk_usage.total,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent
                }
            },
            "queue": queue_stats
        })
    except Exception as e:
        logger.exception(f"Error getting system status: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "server_error",
            "message": str(e)
        }), 500

@system_bp.route('/cleanup', methods=['POST'])
@require_api_key
def cleanup():
    try:
        result = cleanup_temp_files()
        
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        logger.exception(f"Error during cleanup: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "server_error",
            "message": str(e)
        }), 500

