# src/api/routes/__init__.py
from .video_routes import video_bp
from .media_routes import media_bp
from .image_routes import image_bp
from .system_routes import system_bp
from .ffmpeg_routes import ffmpeg_bp

def register_routes(app):
    app.register_blueprint(video_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(ffmpeg_bp)
