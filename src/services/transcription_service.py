import os
import logging
import uuid
import json
from ..utils.file_utils import download_file, generate_temp_filename, verify_file_integrity
from .ffmpeg_service import run_ffmpeg_command
from .storage_service import store_file
from .webhook_service import notify_job_completed, notify_job_failed
from ..config import settings
from ..api.middlewares.error_handler import ProcessingError

logger = logging.getLogger(__name__)

def transcribe_audio(audio_url, language='auto', output_format='txt', job_id=None, webhook_url=None):
    """
    Transcribe audio a texto.
    
    Args:
        audio_url: URL del archivo de audio
        language: Código de idioma ('auto' para detección automática)
        output_format: Formato de salida ('txt', 'srt', 'vtt', 'json')
        job_id: ID del trabajo (opcional)
        webhook_url: URL para notificación por webhook (opcional)
        
    Returns:
        URL del archivo de transcripción
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando transcripción de audio desde {audio_url}")
    
    audio_path = None
    wav_path = None
    output_path = None
    
    try:
        # Descargar el archivo de audio
        audio_path = download_file(audio_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Audio descargado: {audio_path}")
        
        # Convertir a WAV para mejor compatibilidad con servicios de ASR
        wav_path = generate_temp_filename(prefix=f"{job_id}_audio_", suffix=".wav")
        
        command = [
            'ffmpeg',
            '-i', audio_path,
            '-ar', '16000',  # Frecuencia de muestreo estándar para ASR
            '-ac', '1',      # Mono
            '-c:a', 'pcm_s16le',  # Formato PCM sin comprimir, 16 bits
            wav_path
        ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(wav_path):
            raise ProcessingError("Error al preparar el archivo de audio para transcripción")
        
        # Aquí se integraría con un servicio real de ASR como Whisper, Azure Speech, etc.
        # Por ahora, vamos a simular una transcripción
        
        output_path = generate_temp_filename(prefix=f"{job_id}_transcript_", suffix=f".{output_format}")
        
        # Simulación de transcripción
        sample_transcript = "Esta es una transcripción de ejemplo.\nEn un sistema de producción, este texto sería generado por un servicio de reconocimiento de voz."
        
        if output_format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(sample_transcript)
        
        elif output_format == 'srt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("1\n00:00:00,000 --> 00:00:05,000\nEsta es una transcripción de ejemplo.\n\n")
                f.write("2\n00:00:05,100 --> 00:00:10,000\nEn un sistema de producción, este texto sería generado por un servicio de reconocimiento de voz.\n")
        
        elif output_format == 'vtt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                f.write("00:00:00.000 --> 00:00:05.000\nEsta es una transcripción de ejemplo.\n\n")
                f.write("00:00:05.100 --> 00:00:10.000\nEn un sistema de producción, este texto sería generado por un servicio de reconocimiento de voz.\n")
        
        elif output_format == 'json':
            transcript_data = {
                "jobId": job_id,
                "language": language,
                "transcript": sample_transcript,
                "segments": [
                    {
                        "start": 0,
                        "end": 5,
                        "text": "Esta es una transcripción de ejemplo."
                    },
                    {
                        "start": 5.1,
                        "end": 10,
                        "text": "En un sistema de producción, este texto sería generado por un servicio de reconocimiento de voz."
                    }
                ]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
        
        # Almacenar el archivo de transcripción y obtener URL
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Transcripción completada y almacenada: {result_url}")
        
        # Notificar por webhook si es necesario
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error en transcripción: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        # Limpieza de archivos temporales
        for file_path in [audio_path, wav_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {file_path}: {str(e)}")
