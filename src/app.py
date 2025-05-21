from flask import Flask, jsonify, g, send_from_directory, request
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
import uuid
import os
import time
import logging
import subprocess
from src.config.settings import settings
from src.api.routes import register_routes
from src.api.docs import register_docs
from src.api.middlewares.error_handler import register_error_handlers
from src.services.video_service import add_audio_to_video
from src.api.middlewares.authentication import require_api_key
from src.scheduler import init_scheduler

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    CORS(app)
    
    app.config['STORAGE_PATH'] = settings.STORAGE_PATH
    app.config['DEBUG'] = settings.DEBUG
    app.config['API_KEY'] = settings.API_KEY
    app.config['ENVIRONMENT'] = settings.ENVIRONMENT
    app.config['REDIS_URL'] = settings.REDIS_URL
    app.config['BASE_URL'] = settings.BASE_URL
    app.config['MEDIA_URL'] = settings.MEDIA_URL
    app.config['TEMP_DIR'] = settings.TEMP_DIR
    app.config['LOG_DIR'] = settings.LOG_DIR
    
    for directory in [settings.STORAGE_PATH, settings.TEMP_DIR, settings.LOG_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    register_routes(app)
    register_docs(app)
    register_error_handlers(app)
    
    init_scheduler(app)

    @app.before_request
    def before_request():
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        g.request_id = request_id
        g.start_time = time.time()
        
        if request.path != '/health':
            logger.info(f"Request {request_id}: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        
        duration = time.time() - g.get('start_time', time.time())
        
        if request.path != '/health':
            logger.info(f"Request {g.get('request_id', 'unknown')} completed in {duration:.3f}s with status {response.status_code}")
        
        return response
    
    @app.route('/')
    def index():
        return jsonify({
            "service": "Video Processing API",
            "status": "operational",
            "version": "1.0.0",
            "documentation": "/api/docs"
        })
    
    @app.route('/health')
    def health():
        ffmpeg_ok = _check_ffmpeg()
        storage_ok = _check_storage()
        
        status = "healthy" if ffmpeg_ok and storage_ok else "degraded"
        
        return jsonify({
            "status": status,
            "storage": "ok" if storage_ok else "error",
            "ffmpeg": "ok" if ffmpeg_ok else "error",
            "timestamp": time.time()
        })
    
    @app.route('/storage/<path:filename>')
    def serve_file(filename):
        if '..' in filename or filename.startswith('/'):
            return jsonify({"error": "Acceso no autorizado"}), 403
        
        if not os.path.exists(os.path.join(settings.STORAGE_PATH, filename)):
            return jsonify({"error": "Archivo no encontrado"}), 404
            
        return send_from_directory(settings.STORAGE_PATH, filename)
    
    @app.route('/api/v1/video/add-audio', methods=['POST'])
    @require_api_key
    def add_audio_direct():
        data = request.get_json()
        
        try:
            job_id = data.get('id')
            
            result = add_audio_to_video(
                video_url=data['video_url'],
                audio_url=data['audio_url'],
                replace_audio=data.get('replace_audio', True),
                audio_volume=data.get('audio_volume', 1.0),
                job_id=job_id,
                webhook_url=data.get('webhook_url')
            )
            
            return jsonify({
                "status": "success",
                "result": result,
                "job_id": job_id
            })
            
        except Exception as e:
            logger.exception(f"Error añadiendo audio a video: {str(e)}")
            return jsonify({
                "status": "error",
                "error": "processing_error",
                "message": str(e)
            }), 500
    
    @app.route('/debug/routes')
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "path": str(rule)
            })
        return jsonify(routes)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception(f"Error no manejado: {str(e)}")
        
        return jsonify({
            "status": "error",
            "message": "Se produjo un error interno del servidor",
            "request_id": g.get('request_id', 'unknown')
        }), 500
    
    logger.info("==========================================")
    logger.info(f"Video API arrancada en entorno: {settings.ENVIRONMENT}")
    logger.info(f"URL base: {settings.BASE_URL}")
    logger.info(f"API_KEY: {settings.API_KEY[:4]}{'*' * (len(settings.API_KEY) - 4)}")
    logger.info(f"REDIS_URL: {settings.REDIS_URL}")
    logger.info(f"STORAGE_PATH: {settings.STORAGE_PATH}")
    logger.info(f"TEMP_DIR: {settings.TEMP_DIR}")
    logger.info(f"LOG_DIR: {settings.LOG_DIR}")
    logger.info("Cleanup scheduler: Enabled (runs every 6 hours)")
    logger.info("==========================================")
    
    return app

def _check_ffmpeg():
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False

def _check_storage():
    try:
        test_file = os.path.join(settings.STORAGE_PATH, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except Exception:
        return False
