import os
import logging
import threading
import time
import datetime
from ..config import settings

logger = logging.getLogger(__name__)

class CleanupService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.cleanup_interval = 3600  # 1 hora
        self.temp_file_max_age = 86400  # 24 horas

    def start(self):
        if self.running:
            logger.warning("El servicio de limpieza ya está en ejecución")
            return

        self.running = True
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()
        logger.info("Servicio de limpieza iniciado")

    def stop(self):
        if not self.running:
            logger.warning("El servicio de limpieza no está en ejecución")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Servicio de limpieza detenido")

    def _cleanup_loop(self):
        while self.running:
            try:
                self._cleanup_temp_files()
                
                # Dormir por el intervalo configurado, pero comprobar periódicamente
                # si el servicio debe detenerse para permitir una salida rápida
                for _ in range(int(self.cleanup_interval / 5)):
                    if not self.running:
                        break
                    time.sleep(5)
                    
            except Exception as e:
                logger.exception(f"Error en el bucle de limpieza: {str(e)}")
                time.sleep(60)  # Esperar un minuto en caso de error

    def _cleanup_temp_files(self):
        """Elimina archivos temporales antiguos"""
        start_time = time.time()
        logger.info("Iniciando limpieza de archivos temporales")
        
        # Calcular la fecha límite para los archivos a eliminar
        cutoff_time = time.time() - self.temp_file_max_age
        cutoff_datetime = datetime.datetime.fromtimestamp(cutoff_time)
        
        deleted_count = 0
        total_size = 0
        
        # Recorrer el directorio temporal y sus subdirectorios
        for root, _, files in os.walk(settings.TEMP_DIR):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                try:
                    # Obtener la fecha de modificación del archivo
                    file_mtime = os.path.getmtime(file_path)
                    
                    # Si el archivo es más antiguo que el límite, eliminarlo
                    if file_mtime < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        total_size += file_size
                        logger.debug(f"Archivo temporal eliminado: {file_path}")
                        
                except Exception as e:
                    logger.warning(f"Error procesando archivo temporal {file_path}: {str(e)}")
        
        duration = time.time() - start_time
        logger.info(f"Limpieza completada en {duration:.2f}s: {deleted_count} archivos eliminados, "
                   f"{total_size / (1024*1024):.2f} MB liberados")
        
        return {
            "deleted_count": deleted_count,
            "total_size_bytes": total_size,
            "duration_seconds": duration,
            "cutoff_datetime": cutoff_datetime.isoformat()
        }

# Instancia singleton del servicio de limpieza
cleanup_service = CleanupService()

def cleanup_temp_files():
    """
    Función de utilidad para ejecutar la limpieza de archivos temporales bajo demanda.
    """
    return cleanup_service._cleanup_temp_files()
