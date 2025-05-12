import os
import logging
import uuid
from ..utils.file_utils import download_file, generate_temp_filename, verify_file_integrity
from .ffmpeg_service import run_ffmpeg_command, get_media_info
from .storage_service import store_file
from .webhook_service import notify_job_completed, notify_job_failed
from ..config import settings
from ..api.middlewares.error_handler import ProcessingError

logger = logging.getLogger(__name__)

def overlay_image_on_video(video_url, image_url, position='bottom_right', scale=0.3, 
                          opacity=1.0, job_id=None, webhook_url=None):
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando overlay de imagen en video {video_url}")
    
    video_path = None
    image_path = None
    output_path = None
    
    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video descargado: {video_path}")
        
        image_path = download_file(image_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Imagen descargada: {image_path}")
        
        video_info = get_media_info(video_path)
        video_width = int(video_info.get('width', 0))
        video_height = int(video_info.get('height', 0))
        
        if video_width <= 0 or video_height <= 0:
            raise ProcessingError("No se pudo obtener información del video")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_overlay_", suffix=".mp4")
        
        # Calcular posición para el overlay
        overlay_x = 10
        overlay_y = 10
        
        if position == 'bottom_right':
            overlay_x = f"W-w*{scale}-10"
            overlay_y = f"H-h*{scale}-10"
        elif position == 'bottom_left':
            overlay_x = "10"
            overlay_y = f"H-h*{scale}-10"
        elif position == 'top_right':
            overlay_x = f"W-w*{scale}-10"
            overlay_y = "10"
        elif position == 'center':
            overlay_x = f"(W-w*{scale})/2"
            overlay_y = f"(H-h*{scale})/2"
        
        filter_complex = f"[1:v]scale=iw*{scale}:-1,format=rgba,colorchannelmixer=aa={opacity}[overlay];[0:v][overlay]overlay={overlay_x}:{overlay_y}:enable='between(t,0,999999)'[out]"
        
        command = [
            'ffmpeg',
            '-i', video_path,
            '-i', image_path,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-map', '0:a?',
            '-c:a', 'copy',
            output_path
        ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de video con imagen no es válido")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Video con imagen procesado y almacenado: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error procesando overlay de imagen: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [video_path, image_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {file_path}: {str(e)}")

def generate_thumbnail(video_url, time=0, width=640, height=360, quality=90,
                      job_id=None, webhook_url=None):
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Generando thumbnail para {video_url} en tiempo {time}s")
    
    video_path = None
    output_path = None
    
    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video descargado: {video_path}")
        
        video_info = get_media_info(video_path)
        video_duration = float(video_info.get('duration', 0))
        
        if video_duration <= 0:
            raise ProcessingError("No se pudo obtener la duración del video")
        
        if time > video_duration:
            time = video_duration / 2
            logger.warning(f"Job {job_id}: Tiempo ajustado a {time}s (mitad de la duración del video)")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_thumbnail_", suffix=".jpg")
        
        command = [
            'ffmpeg',
            '-ss', str(time),
            '-i', video_path,
            '-vframes', '1',
            '-vf', f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            '-q:v', str(min(31, 31 - (quality / 3.45))),  # Convertir calidad (0-100) a factor de calidad FFmpeg (2-31)
            output_path
        ]
        
        run_ffmpeg_command(command)
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise ProcessingError("No se pudo generar el thumbnail")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Thumbnail generado y almacenado: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error generando thumbnail: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [video_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {file_path}: {str(e)}")
