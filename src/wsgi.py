from src.app import create_app
import logging

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    print("==========================================")
    print(f"Video API arrancada en entorno: {app.config['ENVIRONMENT']}")
    print(f"URL base: {app.config.get('BASE_URL', 'http://localhost:8080')}")
    print(f"API_KEY: {app.config['API_KEY'][:4]}{'*' * (len(app.config['API_KEY']) - 4)}")
    print(f"REDIS_URL: {app.config.get('REDIS_URL', 'No configurado')}")
    print(f"STORAGE_PATH: {app.config.get('STORAGE_PATH', 'No configurado')}")
    print("==========================================")
    
    app.run(host='0.0.0.0', port=8080)
