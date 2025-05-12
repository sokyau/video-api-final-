import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings:
    """Configuraciones globales de la aplicación."""
    
    def __init__(self):
        # Configuración del servidor
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', '8080'))
        
        # Configuración de la API
        self.API_KEY = os.getenv('API_KEY', 'development_key')
        
        # Configuración del entorno
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        self.DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Configuración de directorios
        self.STORAGE_PATH = os.getenv('STORAGE_PATH', './storage')
        self.TEMP_DIR = os.getenv('TEMP_DIR', './temp')
        self.LOG_DIR = os.getenv('LOG_DIR', './logs')
        
        # Configuración de URLs
        self.BASE_URL = os.getenv('BASE_URL', f"http://localhost:{self.PORT}")
        self.MEDIA_URL = os.getenv('MEDIA_URL', f"{self.BASE_URL}/storage")
        
        # Configuración de Redis
        self.REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.REDIS_RETRY_ATTEMPTS = int(os.getenv("REDIS_RETRY_ATTEMPTS", 5))
        self.REDIS_RETRY_BACKOFF = int(os.getenv("REDIS_RETRY_BACKOFF", 2))
        
        # Configuración de logging
        self.LOGGING_CONFIG = {
            'version': 1,
            'formatters': {
                'default': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout',
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'default',
                    'filename': os.path.join(self.LOG_DIR, 'app.log'),
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                },
            },
            'root': {
                'level': self.LOG_LEVEL,
                'handlers': ['console', 'file'],
            },
        }
        
        # Asegurarse de que los directorios existen
        self.ensure_directories()
    
    def ensure_directories(self):
        """Asegurarse de que los directorios necesarios existen."""
        os.makedirs(self.STORAGE_PATH, exist_ok=True)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)

# Instancia de configuración
settings = Settings()

def load_config(app):
    """
    Configura la aplicación Flask con las configuraciones cargadas.
    """
    app.config.update(
        API_KEY=settings.API_KEY,
        DEBUG=settings.DEBUG,
        ENVIRONMENT=settings.ENVIRONMENT,
        STORAGE_PATH=settings.STORAGE_PATH,
        TEMP_DIR=settings.TEMP_DIR,
        LOG_DIR=settings.LOG_DIR,
        REDIS_URL=settings.REDIS_URL,
        BASE_URL=settings.BASE_URL,
        MEDIA_URL=settings.MEDIA_URL
    )
