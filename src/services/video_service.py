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

def add_captions_to_video(video_url, subtitles_url, font='Arial', font_size=24, 
                          font_color='white', background=True, position='bottom',
                          job_id=None, webhook_url=None):
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando procesamiento de video con subtítulos")
    
    video_path = None
    subtitles_path = None
    output_path = None
    
    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video descargado: {video_path}")
        
        subtitles_path = download_file(subtitles_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Subtítulos descargados: {subtitles_path}")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_captioned_", suffix=".mp4")
        
        background_filter = ''
        if background:
            background_filter = ':force_style=\'BackColor=&H80000000,BorderStyle=4\''
        
        subtitle_filter = f"subtitles={subtitles_path}:fontsdir=.:force_style='FontName={font},FontSize={font_size},PrimaryColour=&H{font_color}{background_filter}'"
        
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', subtitle_filter,
            '-c:a', 'copy',
            output_path
        ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de video con subtítulos no es válido")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Video con subtítulos procesado y almacenado: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error procesando video con subtítulos: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [video_path, subtitles_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {file_path}: {str(e)}")

def process_meme_overlay(video_url, meme_url, position='bottom_right', scale=0.3, 
                        job_id=None, webhook_url=None):
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando procesamiento de meme overlay en video {video_url}")
    
    video_path = None
    meme_path = None
    output_path = None
    
    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video descargado: {video_path}")
        
        meme_path = download_file(meme_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Meme descargado: {meme_path}")
        
        video_info = get_media_info(video_path)
        video_width = int(video_info.get('width', 0))
        video_height = int(video_info.get('height', 0))
        
        if video_width <= 0 or video_height <= 0:
            raise ProcessingError("No se pudo obtener información del video")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_memed_", suffix=".mp4")
        
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
        
        filter_complex = f"[0:v][1:v] overlay={overlay_x}:{overlay_y}:enable='between(t,0,999999)'[out]"
        
        command = [
            'ffmpeg',
            '-i', video_path,
            '-i', meme_path,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-map', '0:a?',
            '-c:a', 'copy',
            output_path
        ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de video con meme no es válido")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Video con meme procesado y almacenado: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error procesando meme overlay: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [video_path, meme_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {file_path}: {str(e)}")

def concatenate_videos_service(video_urls, job_id=None, webhook_url=None):
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando concatenación de {len(video_urls)} videos")
    
    video_paths = []
    concat_file = None
    output_path = None
    
    try:
        for i, video_url in enumerate(video_urls):
            video_path = download_file(video_url, settings.TEMP_DIR, prefix=f"concat_{i}_")
            video_paths.append(video_path)
            logger.info(f"Job {job_id}: Video {i+1} descargado: {video_path}")
        
        concat_file = os.path.join(settings.TEMP_DIR, f"{job_id}_concat_list.txt")
        with open(concat_file, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{video_path}'\n")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_concatenated_", suffix=".mp4")
        
        command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de video concatenado no es válido")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Videos concatenados y almacenados: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error concatenando videos: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for video_path in video_paths:
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {video_path}: {str(e)}")
        
        if concat_file and os.path.exists(concat_file):
            try:
                os.remove(concat_file)
            except Exception as e:
                logger.warning(f"Error eliminando archivo temporal {concat_file}: {str(e)}")
        
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception as e:
                logger.warning(f"Error eliminando archivo temporal {output_path}: {str(e)}")

def add_audio_to_video(video_url, audio_url, replace_audio=True, audio_volume=1.0, 
                     job_id=None, webhook_url=None):
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando adición de audio a video {video_url}")
    
    video_path = None
    audio_path = None
    output_path = None
    
    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video descargado: {video_path}")
        
        audio_path = download_file(audio_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Audio descargado: {audio_path}")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_audio_video_", suffix=".mp4")
        
        if replace_audio:
            command = [
                'ffmpeg',
                '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_path
            ]
        else:
            command = [
                'ffmpeg',
                '-y',
                '-i', video_path,
                '-i', audio_path,
                '-filter_complex', f"[0:a]volume=1.0[a1];[1:a]volume={audio_volume}[a2];[a1][a2]amix=inputs=2:duration=longest[aout]",
                '-map', '0:v',
                '-map', '[aout]',
                '-c:v', 'copy',
                output_path
            ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de salida no es válido")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Video con audio procesado y almacenado: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error añadiendo audio: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [video_path, audio_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {file_path}: {str(e)}")
