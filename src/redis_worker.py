import sys
import os
import time
import logging
import signal
import importlib

from src.config.settings import settings
from src.services.redis_queue_service import (
    fetch_pending_task, 
    update_task_status, 
    TaskStatus, 
    init_redis_client
)
from src.services.cleanup_service import cleanup_service

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(settings.LOG_DIR, 'redis_worker.log'))
    ]
)

logger = logging.getLogger(__name__)

# Variable global para controlar la ejecución del worker
running = True

def signal_handler(sig, frame):
    """Manejador de señales para terminar limpiamente."""
    global running
    logger.info(f"Recibida señal {sig}, terminando...")
    running = False

# Registrar manejadores de señales
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Diccionario para almacenar las funciones de tarea
task_functions = {}

def load_task_functions():
    """Carga las funciones de tarea disponibles."""
    global task_functions
    
    # Usamos un diccionario de funciones importadas dinámicamente
    task_functions = {}
    
    # Función helper para importar e incorporar
    def import_and_add(module_path, function_names):
        try:
            module = __import__(module_path, fromlist=function_names)
            for function_name in function_names:
                if hasattr(module, function_name):
                    task_functions[function_name] = getattr(module, function_name)
        except Exception as e:
            logger.error(f"Error importando {module_path}.{function_names}: {str(e)}")
    
    # Importar cada servicio por separado
    import_and_add("src.services.video_service", 
                 ["add_captions_to_video", "process_meme_overlay", 
                  "concatenate_videos_service", "add_audio_to_video"])
    
    import_and_add("src.services.media_service",
                 ["extract_audio", "transcribe_media"])
    
    import_and_add("src.services.animation_service",
                 ["animated_text_service"])
    
    import_and_add("src.services.image_service",
                 ["overlay_image_on_video", "generate_thumbnail"])
    
    logger.info(f"Cargadas {len(task_functions)} funciones de tarea")

def process_task(task):
    """Procesa una tarea de la cola."""
    if not task:
        return False
    
    job_id = task.get("job_id")
    task_func_name = task.get("task_func")
    kwargs = task.get("kwargs", {})
    
    logger.info(f"Procesando tarea {job_id}: {task_func_name}")
    
    # Actualizar estado de la tarea
    update_task_status(job_id, TaskStatus.PROCESSING)
    
    try:
        # Verificar si la función existe
        if task_func_name not in task_functions:
            raise ValueError(f"Función desconocida: {task_func_name}")
        
        # Ejecutar la función
        task_func = task_functions[task_func_name]
        result = task_func(**kwargs)
        
        # Actualizar estado a completado
        update_task_status(job_id, TaskStatus.COMPLETED, result=result)
        logger.info(f"Tarea {job_id} completada exitosamente")
        return True
        
    except Exception as e:
        # Actualizar estado a fallido
        logger.exception(f"Error ejecutando tarea {job_id}: {str(e)}")
        update_task_status(job_id, TaskStatus.FAILED, error=str(e))
        return False

def main():
    """Función principal del worker."""
    logger.info("Iniciando worker de Redis...")
    
    # Cargar funciones de tarea
    load_task_functions()
    
    # Iniciar servicio de limpieza
    cleanup_service.start()
    logger.info("Servicio de limpieza iniciado")
    
    # Parámetros de configuración
    poll_interval = 1  # segundos
    reconnect_interval = 5  # segundos
    max_errors = 5
    consecutive_errors = 0
    
    # Inicializar conexión Redis
    redis_client = init_redis_client()
    if not redis_client:
        logger.error("No se pudo conectar a Redis al iniciar. Reintentando...")
    
    # Bucle principal del worker
    while running:
        try:
            # Verificar conexión Redis
            if not redis_client:
                logger.warning("Sin conexión a Redis. Reintentando...")
                redis_client = init_redis_client()
                if not redis_client:
                    time.sleep(reconnect_interval)
                    continue
            
            # Obtener tarea de la cola
            task = fetch_pending_task()
            
            if task:
                # Procesar la tarea
                process_task(task)
                consecutive_errors = 0
            else:
                # No hay tareas, esperar
                time.sleep(poll_interval)
                
        except Exception as e:
            # Error inesperado
            logger.exception(f"Error en bucle de worker: {str(e)}")
            consecutive_errors += 1
            
            # Si hay muchos errores consecutivos, esperar más tiempo
            if consecutive_errors > max_errors:
                logger.error(f"Demasiados errores consecutivos ({consecutive_errors}). Esperando...")
                time.sleep(reconnect_interval * 2)
                consecutive_errors = 0
            else:
                time.sleep(poll_interval)
    
    # Detener servicios
    cleanup_service.stop()
    logger.info("Worker de Redis terminado correctamente")

if __name__ == "__main__":
    main()
