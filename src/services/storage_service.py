import os
import shutil
import logging
import uuid
import datetime
from urllib.parse import quote
from ..config import settings
from ..api.middlewares.error_handler import ProcessingError, NotFoundError

logger = logging.getLogger(__name__)

def store_file(file_path, target_dir=None, custom_filename=None):
    """
    Almacena un archivo en el directorio de almacenamiento permanente.
    Retorna la URL pública del archivo almacenado.
    """
    if not os.path.exists(file_path):
        raise NotFoundError(f"Archivo no encontrado: {file_path}")
    
    if not target_dir:
        # Organización en subdirectorios por fecha
        today = datetime.datetime.now().strftime('%Y/%m/%d')
        target_dir = os.path.join(settings.STORAGE_PATH, today)
    
    os.makedirs(target_dir, exist_ok=True)
    
    if not custom_filename:
        # Generar un nombre de archivo único basado en UUID
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        custom_filename = f"{uuid.uuid4()}{ext}"
    
    target_path = os.path.join(target_dir, custom_filename)
    
    try:
        shutil.copy2(file_path, target_path)
        logger.debug(f"Archivo copiado a almacenamiento: {target_path}")
        
        # Construir URL relativa para acceso público
        relative_path = os.path.relpath(target_path, settings.STORAGE_PATH)
        url_path = quote(relative_path.replace('\\', '/'))
        
        # URL completa para acceder al archivo
        media_url = f"{settings.MEDIA_URL}/{url_path}"
        
        return media_url
        
    except Exception as e:
        logger.exception(f"Error almacenando archivo {file_path}: {str(e)}")
        raise ProcessingError(f"Error almacenando archivo: {str(e)}")

def get_file_url(file_path):
    """
    Genera la URL pública para un archivo ya almacenado.
    """
    if not file_path.startswith(settings.STORAGE_PATH):
        raise ValueError("La ruta del archivo debe estar dentro del directorio de almacenamiento")
    
    if not os.path.exists(file_path):
        raise NotFoundError(f"Archivo no encontrado: {file_path}")
    
    # Construir URL relativa para acceso público
    relative_path = os.path.relpath(file_path, settings.STORAGE_PATH)
    url_path = quote(relative_path.replace('\\', '/'))
    
    # URL completa para acceder al archivo
    media_url = f"{settings.MEDIA_URL}/{url_path}"
    
    return media_url

def delete_file(file_path_or_url):
    """
    Elimina un archivo del almacenamiento.
    Puede recibir la ruta completa del archivo o su URL.
    """
    try:
        # Si es una URL, convertir a ruta local
        if file_path_or_url.startswith(settings.MEDIA_URL):
            relative_path = file_path_or_url[len(settings.MEDIA_URL):].lstrip('/')
            file_path = os.path.join(settings.STORAGE_PATH, relative_path)
        else:
            file_path = file_path_or_url
        
        if not os.path.exists(file_path):
            raise NotFoundError(f"Archivo no encontrado: {file_path}")
        
        os.remove(file_path)
        logger.debug(f"Archivo eliminado: {file_path}")
        
        return True
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Error eliminando archivo {file_path_or_url}: {str(e)}")
        raise ProcessingError(f"Error eliminando archivo: {str(e)}")
