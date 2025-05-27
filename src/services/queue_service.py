import logging
import time
import os
import uuid
import functools
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

def enqueue_job(task_name, **kwargs):
    """
    Encola un trabajo para procesamiento. Esta función puede usar diferentes
    mecanismos según la configuración (Redis, base de datos local, etc.)
    
    Args:
        task_name: Nombre de la tarea a ejecutar
        **kwargs: Argumentos para la tarea
        
    Returns:
        Dict con información sobre el trabajo encolado
    """
    # Importar aquí para evitar referencias circulares
    from src.services.redis_queue_service import enqueue_task
    
    # Verificar si la tarea existe antes de encolarla
    if not _task_exists(task_name):
        raise ValueError(f"Tarea desconocida: {task_name}")
    
    # Encolar usando Redis
    return enqueue_task(task_name, **kwargs)

def _task_exists(task_name):
    """
    Verifica si una tarea está registrada en el sistema.
    
    Args:
        task_name: Nombre de la tarea a verificar
        
    Returns:
        Bool indicando si la tarea existe
    """
    # Obtener dinámicamente el registro de tareas
    task_registry = _get_task_registry()
    return task_name in task_registry

def _get_task_registry():
    """
    Obtiene el registro de tareas disponibles.
    
    Returns:
        Dict con las funciones de tarea registradas
    """
    # Importar servicios bajo demanda
    from src.services.video_service import add_captions_to_video, process_meme_overlay, concatenate_videos_service, add_audio_to_video
    from src.services.media_service import extract_audio, transcribe_media
    from src.services.animation_service import animated_text_service
    
    # Construir el registro de tareas
    return {
        'add_captions_to_video': add_captions_to_video,
        'process_meme_overlay': process_meme_overlay,
        'concatenate_videos': concatenate_videos_service,
        'extract_audio': extract_audio,
        'transcribe_media': transcribe_media,
        'animated_text': animated_text_service,
        'add_audio_to_video': add_audio_to_video
    }

def get_task_status(job_id):
    """
    Obtiene el estado de una tarea por su ID.
    
    Args:
        job_id: ID del trabajo
        
    Returns:
        Dict con el estado de la tarea o None si no existe
    """
    # Importar aquí para evitar referencias circulares
    from src.services.redis_queue_service import get_task_status as redis_get_task_status
    
    return redis_get_task_status(job_id)

def process_queue(max_tasks=10):
    """
    Procesa tareas pendientes en la cola.
    
    Args:
        max_tasks: Número máximo de tareas a procesar
        
    Returns:
        Número de tareas procesadas
    """
    # Importar aquí para evitar referencias circulares
    from src.services.redis_queue_service import fetch_pending_task, update_task_status, TaskStatus
    
    tasks_processed = 0
    
    for _ in range(max_tasks):
        task = fetch_pending_task()
        
        if not task:
            break
        
        job_id = task.get('job_id')
        task_func = task.get('task_func')
        kwargs = task.get('kwargs', {})
        
        logger.info(f"Procesando tarea {job_id}: {task_func}")
        
        try:
            update_task_status(job_id, TaskStatus.PROCESSING)
            
            # Obtener la función de tarea dinámicamente
            task_registry = _get_task_registry()
            
            if task_func not in task_registry:
                raise ValueError(f"Función desconocida: {task_func}")
            
            func = task_registry[task_func]
            result = func(**kwargs)
            
            update_task_status(job_id, TaskStatus.COMPLETED, result=result)
            logger.info(f"Tarea {job_id} completada exitosamente")
            
            tasks_processed += 1
            
        except Exception as e:
            logger.exception(f"Error ejecutando tarea {job_id}: {str(e)}")
            update_task_status(job_id, TaskStatus.FAILED, error=str(e))
    
    return tasks_processed

def start_workers(num_workers=2, poll_interval=1):
    """
    Inicia workers para procesar tareas en segundo plano.
    
    Args:
        num_workers: Número de workers a iniciar
        poll_interval: Intervalo de sondeo en segundos
        
    Returns:
        Lista de workers iniciados
    """
    import threading
    
    workers = []
    
    for i in range(num_workers):
        worker = threading.Thread(
            target=_worker_loop,
            args=(i, poll_interval),
            daemon=True,
            name=f"QueueWorker-{i}"
        )
        worker.start()
        workers.append(worker)
        logger.info(f"Worker {i} iniciado")
    
    return workers

def _worker_loop(worker_id, poll_interval):
    """
    Función principal del worker.
    
    Args:
        worker_id: ID del worker
        poll_interval: Intervalo de sondeo en segundos
    """
    logger.info(f"Worker {worker_id} iniciando bucle de procesamiento")
    
    running = True
    
    while running:
        try:
            # Procesar un lote de tareas
            tasks_processed = process_queue(max_tasks=1)
            
            if tasks_processed == 0:
                # Si no hay tareas, esperar antes de volver a verificar
                time.sleep(poll_interval)
        except Exception as e:
            logger.exception(f"Error en worker {worker_id}: {str(e)}")
            time.sleep(poll_interval * 2)  # Esperar más tiempo en caso de error

def queue_task_wrapper(task_name):
    """
    Decorador para encolar una función como tarea asíncrona.
    
    Args:
        task_name: Nombre de la tarea para el registro
        
    Returns:
        Función decorada que encola la tarea en lugar de ejecutarla
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generar ID único para la tarea
            job_id = kwargs.get('job_id') or str(uuid.uuid4())
            kwargs['job_id'] = job_id
            
            # Encolar la tarea
            enqueue_job(task_name, **kwargs)
            
            # Devolver el ID del trabajo para seguimiento
            return {
                'job_id': job_id,
                'status': 'queued',
                'task': task_name
            }
        return wrapper
    return decorator

def register_task(task_name, task_func):
    """
    Registra una nueva función de tarea manualmente.
    Esta función es principalmente para pruebas y extensiones.
    
    Args:
        task_name: Nombre de la tarea
        task_func: Función que implementa la tarea
        
    Returns:
        La función envuelta para encolamiento
    """
    # No almacenamos el registro aquí, solo devolvemos la función decorada
    return queue_task_wrapper(task_name)(task_func)
