# src/wsgi.py
from src.app import create_app
import logging
from src.services.cleanup_service import init_cleanup_service

logger = logging.getLogger(__name__)

app = create_app()

# Initialize the cleanup service
init_cleanup_service()

if __name__ == '__main__':
    print("==========================================")
    print(f"Video API started in environment: {app.config['ENVIRONMENT']}")
    print(f"Base URL: {app.config.get('BASE_URL', 'http://localhost:8080')}")
    print(f"API_KEY: {app.config['API_KEY'][:4]}{'*' * (len(app.config['API_KEY']) - 4)}")
    print(f"REDIS_URL: {app.config.get('REDIS_URL', 'Not configured')}")
    print(f"STORAGE_PATH: {app.config.get('STORAGE_PATH', 'Not configured')}")
    print("==========================================")
    
    app.run(host='0.0.0.0', port=8080)
