import os
import json
import subprocess
import logging
from ..api.middlewares.error_handler import ProcessingError

logger = logging.getLogger(__name__)

def run_ffmpeg_command(command):
    """
    Ejecuta un comando FFmpeg.
    
    Args:
        command: Lista de strings que representan el comando a ejecutar
        
    Returns:
        Dict con información sobre la ejecución del comando
        
    Raises:
        ProcessingError: Si hay un error ejecutando el comando
    """
    try:
        logger.debug(f"Ejecutando comando FFmpeg: {' '.join(command)}")
        
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if process.returncode != 0:
            logger.error(f"Error FFmpeg (código {process.returncode}): {process.stderr}")
            raise ProcessingError(f"Error FFmpeg: {process.stderr.splitlines()[-1] if process.stderr else 'Desconocido'}")
        
        return {
            'success': True,
            'returncode': process.returncode,
            'stdout': process.stdout,
            'stderr': process.stderr
        }
        
    except Exception as e:
        if isinstance(e, ProcessingError):
            raise
        
        logger.exception(f"Error ejecutando comando FFmpeg: {str(e)}")
        raise ProcessingError(f"Error ejecutando FFmpeg: {str(e)}")

def get_media_info(file_path):
    """
    Obtiene información sobre un archivo multimedia usando FFprobe.
    
    Args:
        file_path: Ruta al archivo multimedia
        
    Returns:
        Dict con información sobre el archivo multimedia
        
    Raises:
        ProcessingError: Si hay un error obteniendo la información
    """
    if not os.path.exists(file_path):
        raise ProcessingError(f"Archivo no encontrado: {file_path}")
    
    try:
        command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if process.returncode != 0:
            logger.error(f"Error FFprobe (código {process.returncode}): {process.stderr}")
            raise ProcessingError(f"Error obteniendo información del archivo: {process.stderr}")
        
        data = json.loads(process.stdout)
        
        # Extraer información relevante
        result = {
            'format': data.get('format', {}).get('format_name', 'unknown'),
            'duration': float(data.get('format', {}).get('duration', 0)),
            'size': int(data.get('format', {}).get('size', 0)),
            'bit_rate': int(data.get('format', {}).get('bit_rate', 0)),
        }
        
        # Información de video y audio
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                result['width'] = stream.get('width', 0)
                result['height'] = stream.get('height', 0)
                result['video_codec'] = stream.get('codec_name', 'unknown')
                result['frame_rate'] = stream.get('r_frame_rate', 'unknown')
                
            elif stream.get('codec_type') == 'audio':
                result['audio_codec'] = stream.get('codec_name', 'unknown')
                result['sample_rate'] = stream.get('sample_rate', 'unknown')
                result['channels'] = stream.get('channels', 0)
        
        return result
        
    except Exception as e:
        if isinstance(e, ProcessingError):
            raise
        
        logger.exception(f"Error obteniendo información del archivo {file_path}: {str(e)}")
        raise ProcessingError(f"Error obteniendo información del archivo: {str(e)}")
