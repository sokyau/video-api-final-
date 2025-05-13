import json
import logging
import time
import uuid
import redis
from typing import Dict, Any, Callable, Optional
from redis.exceptions import RedisError
from src.config import settings

logger = logging.getLogger(__name__)

def init_redis_client():
    """
    Inicializa el cliente de Redis con reintentos exponenciales.
    
    Returns:
        Cliente Redis o None si no se puede conectar
    """
    for attempt in range(settings.REDIS_RETRY_ATTEMPTS):
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True
            )
            client.ping()
            logger.info(f"Conectado a Redis: {settings.REDIS_URL}")
            return client
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            wait_time = settings.REDIS_RETRY_BACKOFF ** attempt
            logger.warning(f"Error conectando a Redis (intento {attempt+1}/{settings.REDIS_RETRY_ATTEMPTS}): {str(e)}. Reintentando en {wait_time}s")
            time.sleep(wait_time)
    
    logger.error(f"Error conectando a Redis después de {settings.REDIS_RETRY_ATTEMPTS} intentos")
    return None

# Inicializar cliente Redis
redis_client = init_redis_client()

# Constantes
QUEUE_NAME = "video_api:queue"
TASK_INFO_PREFIX = "video_api:task:"

class TaskStatus:
    """Estados posibles de una tarea"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def generate_job_id() -> str:
    """Genera un ID único para un trabajo"""
    return str(uuid.uuid4())

def _ensure_redis_connection():
    """Asegura que hay una conexión Redis disponible, reintenando si es necesario"""
    global redis_client
    
    if redis_client is None:
        redis_client = init_redis_client()
        
    if redis_client is None:
        raise RuntimeError("Redis no disponible para operaciones de cola")
    
    return redis_client

def enqueue_task(task_func_name: str, job_id: str = None, **kwargs) -> Dict[str, Any]:
    """
    Encola una tarea para ser procesada.
    
    Args:
        task_func_name: Nombre de la función de tarea
        job_id: ID único para el trabajo (opcional, se genera si no se proporciona)
        **kwargs: Argumentos para la tarea
        
    Returns:
        Dict con información sobre la tarea encolada
    """
    try:
        client = _ensure_redis_connection()
        
        if not job_id:
            job_id = generate_job_id()
        
        task_data = {
            "job_id": job_id,
            "status": TaskStatus.QUEUED,
            "created_at": time.time(),
            "task_func": task_func_name,
            "kwargs": kwargs,
            "updated_at": time.time()
        }
        
        task_key = f"{TASK_INFO_PREFIX}{job_id}"
        client.set(task_key, json.dumps(task_data))
        
        client.lpush(QUEUE_NAME, json.dumps({
            "job_id": job_id,
            "task_func": task_func_name,
            "kwargs": kwargs
        }))
        
        logger.info(f"Tarea encolada en Redis: {job_id}")
        
        return {
            "job_id": job_id,
            "status": TaskStatus.QUEUED,
            "created_at": task_data["created_at"]
        }
    except RedisError as e:
        # Intentar reconectar en caso de error
        logger.error(f"Error de Redis durante encolado: {str(e)}")
        global redis_client
        redis_client = init_redis_client()
        
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return enqueue_task(task_func_name, job_id, **kwargs)

def get_task_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene el estado de una tarea por su ID.
    
    Args:
        job_id: ID del trabajo
        
    Returns:
        Dict con el estado de la tarea o None si no existe
    """
    try:
        client = _ensure_redis_connection()
        
        task_key = f"{TASK_INFO_PREFIX}{job_id}"
        task_data = client.get(task_key)
        
        if not task_data:
            return None
        
        return json.loads(task_data)
    except RedisError as e:
        # Intentar reconectar en caso de error
        logger.error(f"Error de Redis durante consulta de estado: {str(e)}")
        global redis_client
        redis_client = init_redis_client()
        
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return get_task_status(job_id)

def update_task_status(job_id: str, status: str, result=None, error=None) -> bool:
    """
    Actualiza el estado de una tarea.
    
    Args:
        job_id: ID del trabajo
        status: Nuevo estado de la tarea
        result: Resultado de la tarea (opcional)
        error: Error de la tarea (opcional)
        
    Returns:
        Bool indicando si la actualización fue exitosa
    """
    try:
        client = _ensure_redis_connection()
        
        task_key = f"{TASK_INFO_PREFIX}{job_id}"
        task_data_str = client.get(task_key)
        
        if not task_data_str:
            logger.warning(f"Intento de actualizar tarea inexistente: {job_id}")
            return False
        
        task_data = json.loads(task_data_str)
        task_data["status"] = status
        task_data["updated_at"] = time.time()
        
        if status == TaskStatus.COMPLETED:
            task_data["result"] = result
            task_data["completed_at"] = time.time()
        elif status == TaskStatus.FAILED:
            task_data["error"] = error
        
        client.set(task_key, json.dumps(task_data))
        logger.debug(f"Actualizado estado de tarea {job_id} a {status}")
        
        return True
    except RedisError as e:
        # Intentar reconectar en caso de error
        logger.error(f"Error de Redis durante actualización de estado: {str(e)}")
        global redis_client
        redis_client = init_redis_client()
        
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return update_task_status(job_id, status, result, error)

def fetch_pending_task() -> Optional[Dict[str, Any]]:
    """
    Obtiene y elimina una tarea pendiente de la cola.
    
    Returns:
        Dict con la tarea o None si no hay tareas pendientes
    """
    try:
        client = _ensure_redis_connection()
        
        task_data = client.rpop(QUEUE_NAME)
        
        if not task_data:
            return None
        
        return json.loads(task_data)
    except RedisError as e:
        # Intentar reconectar en caso de error
        logger.error(f"Error de Redis durante obtención de tarea: {str(e)}")
        global redis_client
        redis_client = init_redis_client()
        
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return fetch_pending_task()

def get_queue_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas de la cola.
    
    Returns:
        Dict con estadísticas de la cola
    """
    try:
        client = _ensure_redis_connection()
        
        queue_length = client.llen(QUEUE_NAME)
        
        task_keys = client.keys(f"{TASK_INFO_PREFIX}*")
        status_counts = {
            TaskStatus.QUEUED: 0,
            TaskStatus.PROCESSING: 0,
            TaskStatus.COMPLETED: 0,
            TaskStatus.FAILED: 0
        }
        
        for key in task_keys:
            task_data_str = client.get(key)
            if task_data_str:
                task_data = json.loads(task_data_str)
                status = task_data.get("status")
                if status in status_counts:
                    status_counts[status] += 1
        
        return {
            "queue_length": queue_length,
            "total_tasks": len(task_keys),
            "tasks_by_status": status_counts
        }
    except RedisError as e:
        # Intentar reconectar en caso de error
        logger.error(f"Error de Redis durante obtención de estadísticas: {str(e)}")
        global redis_client
        redis_client = init_redis_client()
        
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return get_queue_stats()
            
def clear_queue():
    """
    Limpia la cola de tareas (útil para pruebas y reinicio).
    
    Returns:
        Bool indicando si la operación fue exitosa
    """
    try:
        client = _ensure_redis_connection()
        
        # Borrar clave de cola
        client.delete(QUEUE_NAME)
        
        # Borrar información de tareas
        task_keys = client.keys(f"{TASK_INFO_PREFIX}*")
        if task_keys:
            client.delete(*task_keys)
        
        logger.info(f"Cola limpiada: {len(task_keys)} tareas eliminadas")
        return True
    except RedisError as e:
        logger.error(f"Error de Redis durante limpieza de cola: {str(e)}")
        return False
