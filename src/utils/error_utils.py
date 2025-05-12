import logging
import traceback
import time
from functools import wraps
from ..api.middlewares.error_handler import APIError, ValidationError, ProcessingError, NotFoundError

logger = logging.getLogger(__name__)

def format_exception(exception):
    """
    Formatea una excepción para incluir información detallada.
    
    Args:
        exception: La excepción a formatear
        
    Returns:
        Un string con la excepción formateada
    """
    exc_type = type(exception).__name__
    exc_message = str(exception)
    exc_traceback = traceback.format_exc()
    
    return {
        'error_type': exc_type,
        'error_message': exc_message,
        'traceback': exc_traceback,
        'timestamp': time.time()
    }

def log_exception(exception, level=logging.ERROR, include_traceback=True):
    """
    Registra una excepción en el log.
    
    Args:
        exception: La excepción a registrar
        level: Nivel de logging a usar
        include_traceback: Si se debe incluir el traceback
    """
    exc_type = type(exception).__name__
    exc_message = str(exception)
    
    if include_traceback:
        logger.log(level, f"{exc_type}: {exc_message}", exc_info=True)
    else:
        logger.log(level, f"{exc_type}: {exc_message}")

def handle_service_error(func):
    """
    Decorador para manejar errores en servicios y convertirlos a APIError.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            # Re-lanzar ValidationError sin modificaciones
            raise
        except NotFoundError as e:
            # Re-lanzar NotFoundError sin modificaciones
            raise
        except ProcessingError as e:
            # Re-lanzar ProcessingError sin modificaciones
            raise
        except APIError as e:
            # Re-lanzar APIError sin modificaciones
            raise
        except Exception as e:
            # Convertir excepciones no manejadas a ProcessingError
            log_exception(e)
            raise ProcessingError(f"Error de servicio: {str(e)}")
    
    return wrapper
