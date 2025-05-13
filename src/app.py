from flask import Flask, jsonify, g, send_from_directory, request
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
import uuid, os, time, logging
from src.config.settings import settings
from src.api.routes import register_routes
from src.api.docs import register_docs

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
    
    register_routes(app)
    register_docs(app)

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
        return jsonify({
            "status": "healthy",
            "storage": "ok",
            "ffmpeg": "ok"
        })
    
    @app.route('/storage/<path:filename>')
    def serve_file(filename):
        if '..' in filename or filename.startswith('/'):
            return jsonify({"error": "Acceso no autorizado"}), 403
        
        if not os.path.exists(os.path.join(settings.STORAGE_PATH, filename)):
            return jsonify({"error": "Archivo no encontrado"}), 404
            
        return send_from_directory(settings.STORAGE_PATH, filename)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception(f"Error no manejado: {str(e)}")
        
        return jsonify({
            "status": "error",
            "message": "Se produjo un error interno del servidor",
            "request_id": g.get('request_id', 'unknown')
        }), 500
    
    # Imprimir información de arranque
    logger.info("==========================================")
    logger.info(f"Video API arrancada en entorno: {settings.ENVIRONMENT}")
    logger.info(f"URL base: {settings.BASE_URL}")
    logger.info(f"API_KEY: {settings.API_KEY[:4]}{'*' * (len(settings.API_KEY) - 4)}")
    logger.info(f"REDIS_URL: {settings.REDIS_URL}")
    logger.info(f"STORAGE_PATH: {settings.STORAGE_PATH}")
    logger.info(f"TEMP_DIR: {settings.TEMP_DIR}")
    logger.info(f"LOG_DIR: {settings.LOG_DIR}")
    logger.info("==========================================")
    
    return app
