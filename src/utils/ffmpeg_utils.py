import os
import re
import subprocess
import logging
import json
from ..api.middlewares.error_handler import ProcessingError

logger = logging.getLogger(__name__)

def build_ffmpeg_command(input_files, output_file, filters=None, codec_options=None, extra_options=None):
    """
    Construye un comando FFmpeg basado en los parámetros proporcionados.
    
    Args:
        input_files: Lista de archivos de entrada o dict con archivos y opciones
        output_file: Archivo de salida
        filters: Filtros a aplicar
        codec_options: Opciones de codec
        extra_options: Opciones adicionales
        
    Returns:
        Lista con el comando FFmpeg listo para ejecución
    """
    command = ['ffmpeg']
    
    # Agregar opciones globales
    command.extend(['-y', '-hide_banner'])
    
    # Procesar archivos de entrada
    if isinstance(input_files, list):
        for input_file in input_files:
            command.extend(['-i', input_file])
    elif isinstance(input_files, dict):
        for input_file, options in input_files.items():
            if options:
                command.extend(options)
            command.extend(['-i', input_file])
    else:
        command.extend(['-i', input_files])
    
    # Agregar filtros
    if filters:
        if isinstance(filters, list):
            for filter_complex in filters:
                command.extend(['-filter_complex', filter_complex])
        else:
            command.extend(['-filter_complex', filters])
    
    # Agregar opciones de codec
    if codec_options:
        for option, value in codec_options.items():
            command.extend([f'-{option}', value])
    
    # Agregar opciones adicionales
    if extra_options:
        if isinstance(extra_options, list):
            command.extend(extra_options)
        elif isinstance(extra_options, dict):
            for option, value in extra_options.items():
                command.extend([f'-{option}', value])
    
    # Agregar archivo de salida
    command.append(output_file)
    
    return command

def parse_ffmpeg_output(output):
    """
    Analiza la salida de FFmpeg para extraer información útil.
    
    Args:
        output: Salida de FFmpeg (stderr)
        
    Returns:
        Dict con información extraída
    """
    result = {
        'duration': None,
        'bitrate': None,
        'fps': None,
        'progress': None,
        'speed': None,
        'time': None,
        'size': None
    }
    
    # Extraer duración
    duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', output)
    if duration_match:
        h, m, s, ms = map(int, duration_match.groups())
        result['duration'] = h * 3600 + m * 60 + s + ms / 100
    
    # Extraer bitrate
    bitrate_match = re.search(r'bitrate: (\d+) kb/s', output)
    if bitrate_match:
        result['bitrate'] = int(bitrate_match.group(1))
    
    # Extraer FPS
    fps_match = re.search(r'(\d+\.?\d*) fps', output)
    if fps_match:
        result['fps'] = float(fps_match.group(1))
    
    # Extraer progreso
    progress_match = re.search(r'frame=\s*(\d+)', output)
    if progress_match:
        result['progress'] = int(progress_match.group(1))
    
    # Extraer velocidad de procesamiento
    speed_match = re.search(r'speed=\s*(\d+\.?\d*x)', output)
    if speed_match:
        result['speed'] = speed_match.group(1)
    
    # Extraer tiempo procesado
    time_match = re.search(r'time=\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})', output)
    if time_match:
        h, m, s, ms = map(int, time_match.groups())
        result['time'] = h * 3600 + m * 60 + s + ms / 100
    
    # Extraer tamaño
    size_match = re.search(r'size=\s*(\d+)kB', output)
    if size_match:
        result['size'] = int(size_match.group(1)) * 1024
    
    return result

def validate_ffmpeg_result(output_file, min_size=1024, check_duration=False, min_duration=0.1):
    """
    Valida que el archivo de salida de FFmpeg sea válido.
    
    Args:
        output_file: Ruta al archivo de salida
        min_size: Tamaño mínimo en bytes
        check_duration: Si se debe verificar la duración
        min_duration: Duración mínima en segundos
        
    Returns:
        Bool indicando si el archivo es válido
    """
    if not os.path.exists(output_file):
        logger.error(f"El archivo de salida no existe: {output_file}")
        return False
    
    file_size = os.path.getsize(output_file)
    if file_size < min_size:
        logger.error(f"El archivo de salida es demasiado pequeño: {file_size} bytes < {min_size} bytes")
        return False
    
    if check_duration:
        try:
            command = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                output_file
            ]
            
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            
            if result.returncode != 0:
                logger.error(f"Error verificando duración: {result.stderr}")
                return False
            
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            
            if duration < min_duration:
                logger.error(f"Duración insuficiente: {duration} < {min_duration}")
                return False
        
        except Exception as e:
            logger.exception(f"Error verificando duración: {str(e)}")
            return False
    
    return True

def format_filter_complex(filters):
    """
    Formatea un diccionario de filtros en una cadena de filtros para FFmpeg.
    
    Args:
        filters: Dict con filtros FFmpeg
        
    Returns:
        String con filtros formateados
    """
    if isinstance(filters, str):
        return filters
    
    if isinstance(filters, list):
        return ','.join(filters)
    
    if isinstance(filters, dict):
        filter_strings = []
        
        for filter_name, filter_params in filters.items():
            if isinstance(filter_params, dict):
                params_str = ':'.join([f"{k}={v}" for k, v in filter_params.items()])
                filter_strings.append(f"{filter_name}={params_str}")
            elif isinstance(filter_params, list):
                params_str = ':'.join(filter_params)
                filter_strings.append(f"{filter_name}={params_str}")
            else:
                filter_strings.append(f"{filter_name}={filter_params}")
        
        return ','.join(filter_strings)
    
    return ""
