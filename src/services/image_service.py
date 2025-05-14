# src/services/image_service.py
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
    
    logger.info(f"Job {job_id}: Starting image overlay on video {video_url}")
    
    video_path = None
    image_path = None
    output_path = None
    
    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video downloaded: {video_path}")
        
        image_path = download_file(image_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Image downloaded: {image_path}")
        
        video_info = get_media_info(video_path)
        video_width = int(video_info.get('width', 0))
        video_height = int(video_info.get('height', 0))
        
        if video_width <= 0 or video_height <= 0:
            raise ProcessingError("Could not get video information")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_overlay_", suffix=".mp4")
        
        # Calculate position for the overlay
        overlay_x, overlay_y = calculate_overlay_position(position, scale, video_width, video_height)
        
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
            raise ProcessingError("The video with image is not valid")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Video with image processed and stored: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error processing image overlay: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [video_path, image_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Temporary file removed: {file_path}")
                except Exception as e:
                    logger.warning(f"Error removing temporary file {file_path}: {str(e)}")

def calculate_overlay_position(position, scale, video_width, video_height):
    """
    Calculate the x, y position for overlay based on different formats.
    Supports:
    - Predefined positions: 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center'
    - Percentage format: 'x=50%,y=30%'
    - Pixel format: 'x=100,y=200'
    """
    # Default margins
    margin = 10
    
    # Predefined positions
    if position == 'bottom_right':
        return f"W-w*{scale}-{margin}", f"H-h*{scale}-{margin}"
    elif position == 'bottom_left':
        return f"{margin}", f"H-h*{scale}-{margin}"
    elif position == 'top_right':
        return f"W-w*{scale}-{margin}", f"{margin}"
    elif position == 'top_left':
        return f"{margin}", f"{margin}"
    elif position == 'center':
        return f"(W-w*{scale})/2", f"(H-h*{scale})/2"
    
    # Custom position formats
    if isinstance(position, str) and ',' in position:
        parts = position.split(',')
        if len(parts) >= 2:
            x_part = parts[0].strip()
            y_part = parts[1].strip()
            
            # Process X coordinate
            if x_part.startswith('x='):
                x_value = x_part[2:].strip()
                if x_value.endswith('%'):
                    # Percentage calculation
                    try:
                        x_percent = float(x_value.rstrip('%')) / 100
                        overlay_x = f"(W-w*{scale})*{x_percent}"
                    except ValueError:
                        overlay_x = f"{margin}"  # Default if invalid
                else:
                    # Direct pixel value
                    try:
                        _ = float(x_value)  # Validate it's a number
                        overlay_x = x_value
                    except ValueError:
                        overlay_x = f"{margin}"  # Default if invalid
            else:
                overlay_x = f"{margin}"  # Default
            
            # Process Y coordinate
            if y_part.startswith('y='):
                y_value = y_part[2:].strip()
                if y_value.endswith('%'):
                    # Percentage calculation
                    try:
                        y_percent = float(y_value.rstrip('%')) / 100
                        overlay_y = f"H*{y_percent}"
                    except ValueError:
                        overlay_y = f"{margin}"  # Default if invalid
                else:
                    # Direct pixel value
                    try:
                        _ = float(y_value)  # Validate it's a number
                        overlay_y = y_value
                    except ValueError:
                        overlay_y = f"{margin}"  # Default if invalid
            else:
                overlay_y = f"{margin}"  # Default
                
            return overlay_x, overlay_y
    
    # Default position (top left) if format is not recognized
    logger.warning(f"Unrecognized position format: {position}, using default (top left)")
    return f"{margin}", f"{margin}"

def generate_thumbnail(video_url, time=0, width=640, height=360, quality=90,
                      job_id=None, webhook_url=None):
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Generating thumbnail for {video_url} at time {time}s")
    
    video_path = None
    output_path = None
    
    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video downloaded: {video_path}")
        
        video_info = get_media_info(video_path)
        video_duration = float(video_info.get('duration', 0))
        
        if video_duration <= 0:
            raise ProcessingError("Could not get video duration")
        
        if time > video_duration:
            time = video_duration / 2
            logger.warning(f"Job {job_id}: Time adjusted to {time}s (half of video duration)")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_thumbnail_", suffix=".jpg")
        
        command = [
            'ffmpeg',
            '-ss', str(time),
            '-i', video_path,
            '-vframes', '1',
            '-vf', f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            '-q:v', str(min(31, 31 - (quality / 3.45))),  # Convert quality (0-100) to FFmpeg quality factor (2-31)
            output_path
        ]
        
        run_ffmpeg_command(command)
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise ProcessingError("Could not generate thumbnail")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Thumbnail generated and stored: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error generating thumbnail: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [video_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Temporary file removed: {file_path}")
                except Exception as e:
                    logger.warning(f"Error removing temporary file {file_path}: {str(e)}")

def process_meme_overlay(video_url, meme_url, position='bottom_right', scale=0.3, 
                        job_id=None, webhook_url=None):
    """
    Add a meme overlay to a video.
    
    Args:
        video_url: URL of the video file
        meme_url: URL of the meme image to overlay
        position: Position of the overlay - can be:
                 - Predefined: 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center'
                 - Custom percentage: 'x=50%,y=30%'
                 - Custom pixels: 'x=100,y=200'
        scale: Scale factor for the overlay (0.1 to 1.0)
        job_id: Optional job ID
        webhook_url: Optional webhook URL for notification
        
    Returns:
        URL of the processed video
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Starting meme overlay processing for video {video_url}")
    
    video_path = None
    meme_path = None
    output_path = None
    
    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video downloaded: {video_path}")
        
        meme_path = download_file(meme_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Meme downloaded: {meme_path}")
        
        video_info = get_media_info(video_path)
        video_width = int(video_info.get('width', 0))
        video_height = int(video_info.get('height', 0))
        
        if video_width <= 0 or video_height <= 0:
            raise ProcessingError("Could not get video information")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_memed_", suffix=".mp4")
        
        # Calculate position using the helper function
        overlay_x, overlay_y = calculate_overlay_position(position, scale, video_width, video_height)
        
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
            raise ProcessingError("The meme overlay output file is not valid")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Video with meme processed and stored: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error processing meme overlay: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [video_path, meme_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Temporary file removed: {file_path}")
                except Exception as e:
                    logger.warning(f"Error removing temporary file {file_path}: {str(e)}")
