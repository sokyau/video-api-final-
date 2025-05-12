import logging
import threading
import time
import uuid
import queue
from enum import Enum
from typing import Dict, Any, Callable, Optional, List

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task:
    def __init__(self, task_func: str, kwargs: Dict = None, job_id: str = None):
        self.job_id = job_id or str(uuid.uuid4())
        self.task_func = task_func
        self.kwargs = kwargs or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "task_func": self.task_func,
            "kwargs": self.kwargs,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }

    def mark_processing(self):
        self.status = TaskStatus.PROCESSING
        self.started_at = time.time()

    def mark_completed(self, result=None):
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = time.time()

    def mark_failed(self, error=None):
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = time.time()

class Worker(threading.Thread):
    def __init__(self, task_queue, task_registry, task_store):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.task_registry = task_registry
        self.task_store = task_store
        self.running = False
        self.name = f"Worker-{uuid.uuid4()}"

    def run(self):
        self.running = True
        logger.info(f"Worker {self.name} iniciado")
        
        while self.running:
            try:
                # Obtener tarea de la cola con timeout para permitir finalización limpia
                try:
                    task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                logger.info(f"Worker {self.name} procesando tarea {task.job_id}: {task.task_func}")
                
                # Actualizar estado
                task.mark_processing()
                
                try:
                    # Verificar si la función existe en el registro
                    if task.task_func not in self.task_registry:
                        raise ValueError(f"Función desconocida: {task.task_func}")
                    
                    # Ejecutar la función
                    func = self.task_registry[task.task_func]
                    result = func(**task.kwargs)
                    
                    # Marcar como completada
                    task.mark_completed(result)
                    logger.info(f"Worker {self.name} completó tarea {task.job_id}")
                    
                except Exception as e:
                    # Marcar como fallida
                    logger.exception(f"Worker {self.name} error en tarea {task.job_id}: {str(e)}")
                    task.mark_failed(str(e))
                
                finally:
                    # Indicar que la tarea ha sido procesada
                    self.task_queue.task_done()
                
            except Exception as e:
                logger.exception(f"Worker {self.name} error inesperado: {str(e)}")
                time.sleep(1)
        
        logger.info(f"Worker {self.name} finalizado")

    def stop(self):
        self.running = False

class QueueManager:
    def __init__(self, num_workers=2):
        self.task_queue = queue.Queue()
        self.task_store = {}  # Almacén de tareas por job_id
        self.task_registry = {}  # Registro de funciones por nombre
        self.workers = []
        self.num_workers = num_workers
        self.stats = {
            "tasks_pending": 0,
            "tasks_processing": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_tasks": 0
        }
    
    def register_task_function(self, name: str, func: Callable):
        """Registra una función de tarea con un nombre"""
        self.task_registry[name] = func
        logger.debug(f"Función de tarea registrada: {name}")
    
    def register_task_functions(self, task_functions: Dict[str, Callable]):
        """Registra múltiples funciones de tarea"""
        for name, func in task_functions.items():
            self.register_task_function(name, func)
    
    def enqueue_task(self, task_func: str, **kwargs) -> Dict[str, Any]:
        """Añade una tarea a la cola"""
        job_id = kwargs.pop('job_id', None) or str(uuid.uuid4())
        
        # Crear tarea
        task = Task(task_func, kwargs, job_id)
        
        # Almacenar tarea
        self.task_store[job_id] = task
        
        # Añadir a la cola
        self.task_queue.put(task)
        
        # Actualizar estadísticas
        self._update_stats()
        
        logger.info(f"Tarea encolada: {job_id} - {task_func}")
        
        return task.to_dict()
    
    def get_task_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de una tarea por su job_id"""
        task = self.task_store.get(job_id)
        if task:
            return task.to_dict()
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la cola"""
        self._update_stats()
        return self.stats
    
    def _update_stats(self):
        """Actualiza las estadísticas internas"""
        counts = {
            TaskStatus.PENDING: 0,
            TaskStatus.PROCESSING: 0,
            TaskStatus.COMPLETED: 0,
            TaskStatus.FAILED: 0
        }
        
        for task in self.task_store.values():
            counts[task.status] += 1
        
        self.stats = {
            "tasks_pending": counts[TaskStatus.PENDING],
            "tasks_processing": counts[TaskStatus.PROCESSING],
            "tasks_completed": counts[TaskStatus.COMPLETED],
            "tasks_failed": counts[TaskStatus.FAILED],
            "total_tasks": len(self.task_store),
            "queue_size": self.task_queue.qsize()
        }
    
    def start_workers(self):
        """Inicia los workers para procesar tareas"""
        if self.workers:
            logger.warning("Los workers ya están en ejecución")
            return
        
        for _ in range(self.num_workers):
            worker = Worker(self.task_queue, self.task_registry, self.task_store)
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Iniciados {len(self.workers)} workers")
    
    def stop_workers(self):
        """Detiene los workers"""
        if not self.workers:
            logger.warning("No hay workers en ejecución")
            return
        
        for worker in self.workers:
            worker.stop()
        
        # Esperar a que los workers terminen
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers = []
        logger.info("Workers detenidos")
    
    def cleanup_completed_tasks(self, max_age_seconds=86400):
        """Limpia tareas completadas o fallidas antiguas"""
        current_time = time.time()
        job_ids_to_remove = []
        
        for job_id, task in self.task_store.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                if task.completed_at and (current_time - task.completed_at) > max_age_seconds:
                    job_ids_to_remove.append(job_id)
        
        for job_id in job_ids_to_remove:
            del self.task_store[job_id]
        
        logger.info(f"Limpiadas {len(job_ids_to_remove)} tareas antiguas")
        self._update_stats()
        
        return len(job_ids_to_remove)
