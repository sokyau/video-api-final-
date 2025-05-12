import logging
import time
import os
import importlib

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
    from .redis_queue_service import enqueue_task
    
    # Registro de funciones de procesamiento
    from . import video_service, media_service, animation_service
    
    TASK_REGISTRY = {
        'add_captions_to_video': video_service.add_captions_to_video,
        'process_meme_overlay': video_service.process_meme_overlay,
        'concatenate_videos': video_service.concatenate_videos_service,
        'extract_audio': media_service.extract_audio,
        'transcribe_media': media_service.transcribe_media,
        'animated_text': animation_service.animated_text_service
    }
    
    if task_name not in TASK_REGISTRY:
        raise ValueError(f"Tarea desconocida: {task_name}")
    
    # Encolar usando Redis
    return enqueue_task(task_name, **kwargs)

def process_queue(max_tasks=10):
    """
    Procesa tareas pendientes en la cola.
    
    Args:
        max_tasks: Número máximo de tareas a procesar
        
    Returns:
        Número de tareas procesadas
    """
    from .redis_queue_service import fetch_pending_task, update_task_status, TaskStatus
    
    # Registro de funciones de procesamiento
    from . import video_service, media_service, animation_service
    
    TASK_REGISTRY = {
        'add_captions_to_video': video_service.add_captions_to_video,
        'process_meme_overlay': video_service.process_meme_overlay,
        'concatenate_videos': video_service.concatenate_videos_service,
        'extract_audio': media_service.extract_audio,
        'transcribe_media': media_service.transcribe_media,
        'animated_text': animation_service.animated_text_service
    }
    
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
            
            if task_func not in TASK_REGISTRY:
                raise ValueError(f"Función desconocida: {task_func}")
            
            func = TASK_REGISTRY[task_func]
            result = func(**kwargs)
            
            update_task_status(job_id, TaskStatus.COMPLETED, result=result)
            logger.info(f"Tarea {job_id} completada exitosamente")
            
            tasks_processed += 1
            
        except Exception as e:
            logger.exception(f"Error ejecutando tarea {job_id}: {str(e)}")
            update_task_status(job_id, TaskStatus.FAILED, error=str(e))
    
    return tasks_processed
