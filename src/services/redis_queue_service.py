import json
import logging
import time
import uuid
import redis
from typing import Dict, Any, Callable, Optional
from redis.exceptions import RedisError
from ..config import settings

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

QUEUE_NAME = "video_api:queue"
TASK_INFO_PREFIX = "video_api:task:"

class TaskStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def generate_job_id() -> str:
    return str(uuid.uuid4())

def enqueue_task(task_func_name: str, job_id: str = None, **kwargs) -> Dict[str, Any]:
    global redis_client
    
    if redis_client is None:
        redis_client = init_redis_client()
    
    if redis_client is None:
        raise RuntimeError("Redis no disponible para encolado de tareas")
    
    try:
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
        redis_client.set(task_key, json.dumps(task_data))
        
        redis_client.lpush(QUEUE_NAME, json.dumps({
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
    except redis.exceptions.RedisError as e:
        # Intentar reconectar en caso de error de Redis
        logger.error(f"Error de Redis durante encolado: {str(e)}")
        redis_client = init_redis_client()
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return enqueue_task(task_func_name, job_id, **kwargs)

def get_task_status(job_id: str) -> Optional[Dict[str, Any]]:
    global redis_client
    
    if redis_client is None:
        redis_client = init_redis_client()
    
    if redis_client is None:
        raise RuntimeError("Redis no disponible para consultar estado")
    
    try:
        task_key = f"{TASK_INFO_PREFIX}{job_id}"
        task_data = redis_client.get(task_key)
        
        if not task_data:
            return None
        
        return json.loads(task_data)
    except redis.exceptions.RedisError as e:
        # Intentar reconectar en caso de error de Redis
        logger.error(f"Error de Redis durante consulta de estado: {str(e)}")
        redis_client = init_redis_client()
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return get_task_status(job_id)

def update_task_status(job_id: str, status: str, result=None, error=None) -> bool:
    global redis_client
    
    if redis_client is None:
        redis_client = init_redis_client()
    
    if redis_client is None:
        raise RuntimeError("Redis no disponible para actualizar estado")
    
    try:
        task_key = f"{TASK_INFO_PREFIX}{job_id}"
        task_data_str = redis_client.get(task_key)
        
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
        
        redis_client.set(task_key, json.dumps(task_data))
        logger.debug(f"Actualizado estado de tarea {job_id} a {status}")
        
        return True
    except redis.exceptions.RedisError as e:
        # Intentar reconectar en caso de error de Redis
        logger.error(f"Error de Redis durante actualización de estado: {str(e)}")
        redis_client = init_redis_client()
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return update_task_status(job_id, status, result, error)

def fetch_pending_task() -> Optional[Dict[str, Any]]:
    global redis_client
    
    if redis_client is None:
        redis_client = init_redis_client()
    
    if redis_client is None:
        raise RuntimeError("Redis no disponible para obtener tareas")
    
    try:
        task_data = redis_client.rpop(QUEUE_NAME)
        
        if not task_data:
            return None
        
        return json.loads(task_data)
    except redis.exceptions.RedisError as e:
        # Intentar reconectar en caso de error de Redis
        logger.error(f"Error de Redis durante obtención de tarea: {str(e)}")
        redis_client = init_redis_client()
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return fetch_pending_task()

task_functions_registry = {}

def register_task_functions(task_functions: Dict[str, Callable]) -> None:
    global task_functions_registry
    task_functions_registry = task_functions
    logger.info(f"Registradas {len(task_functions)} funciones de tarea")

def get_queue_stats() -> Dict[str, Any]:
    global redis_client
    
    if redis_client is None:
        redis_client = init_redis_client()
    
    if redis_client is None:
        raise RuntimeError("Redis no disponible para estadísticas")
    
    try:
        queue_length = redis_client.llen(QUEUE_NAME)
        
        task_keys = redis_client.keys(f"{TASK_INFO_PREFIX}*")
        status_counts = {
            TaskStatus.QUEUED: 0,
            TaskStatus.PROCESSING: 0,
            TaskStatus.COMPLETED: 0,
            TaskStatus.FAILED: 0
        }
        
        for key in task_keys:
            task_data_str = redis_client.get(key)
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
    except redis.exceptions.RedisError as e:
        # Intentar reconectar en caso de error de Redis
        logger.error(f"Error de Redis durante obtención de estadísticas: {str(e)}")
        redis_client = init_redis_client()
        if redis_client is None:
            raise RuntimeError(f"Redis no disponible tras error: {str(e)}")
        else:
            # Reintento de la operación
            return get_queue_stats()
