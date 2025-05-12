import json
import logging
import requests
from requests.exceptions import RequestException
import time

logger = logging.getLogger(__name__)

def notify_job_completed(job_id, webhook_url, result, max_retries=3, retry_delay=2):
    """
    Notifica a un webhook que un trabajo ha sido completado exitosamente.
    
    Args:
        job_id: ID del trabajo
        webhook_url: URL del webhook
        result: Resultado del trabajo
        max_retries: Número máximo de reintentos
        retry_delay: Tiempo de espera entre reintentos (segundos)
    """
    if not webhook_url:
        logger.debug(f"Job {job_id}: No hay webhook configurado")
        return
    
    payload = {
        'job_id': job_id,
        'status': 'completed',
        'result': result,
        'timestamp': time.time()
    }
    
    logger.info(f"Job {job_id}: Notificando finalización a {webhook_url}")
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Job {job_id}: Webhook notificado exitosamente")
                return True
            else:
                logger.warning(f"Job {job_id}: Error en webhook (intento {attempt+1}/{max_retries}), "
                              f"código de estado: {response.status_code}")
                
        except RequestException as e:
            logger.warning(f"Job {job_id}: Error en webhook (intento {attempt+1}/{max_retries}): {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    logger.error(f"Job {job_id}: No se pudo notificar al webhook después de {max_retries} intentos")
    return False

def notify_job_failed(job_id, webhook_url, error_message, max_retries=3, retry_delay=2):
    """
    Notifica a un webhook que un trabajo ha fallado.
    
    Args:
        job_id: ID del trabajo
        webhook_url: URL del webhook
        error_message: Mensaje de error
        max_retries: Número máximo de reintentos
        retry_delay: Tiempo de espera entre reintentos (segundos)
    """
    if not webhook_url:
        logger.debug(f"Job {job_id}: No hay webhook configurado")
        return
    
    payload = {
        'job_id': job_id,
        'status': 'failed',
        'error': error_message,
        'timestamp': time.time()
    }
    
    logger.info(f"Job {job_id}: Notificando error a {webhook_url}")
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Job {job_id}: Webhook de error notificado exitosamente")
                return True
            else:
                logger.warning(f"Job {job_id}: Error en webhook de error (intento {attempt+1}/{max_retries}), "
                              f"código de estado: {response.status_code}")
                
        except RequestException as e:
            logger.warning(f"Job {job_id}: Error en webhook de error (intento {attempt+1}/{max_retries}): {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    logger.error(f"Job {job_id}: No se pudo notificar el error al webhook después de {max_retries} intentos")
    return False
