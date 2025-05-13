# List of exported symbols for * imports
__all__ = [
    'add_captions_to_video',
    'process_meme_overlay',
    'concatenate_videos_service',
    'overlay_image_on_video',
    'generate_thumbnail',
    'store_file',
    'get_file_url',
    'delete_file',
    'run_ffmpeg_command',
    'get_media_info',
    'notify_job_completed',
    'notify_job_failed',
    'process_queue',
    'enqueue_job',
    'cleanup_temp_files',
    'transcribe_audio',
    'enqueue_task',
    'get_task_status',
    'update_task_status',
    'TaskStatus',
    'extract_audio',
    'transcribe_media',
    'animated_text_service'
]

# Dictionary to store lazy-loaded modules and functions
_services = {}

def init_services():
    """Initialize and return all service functions to avoid circular imports."""
    global _services
    
    if not _services:
        # Import modules on demand
        from src.services.video_service import add_captions_to_video, process_meme_overlay, concatenate_videos_service
        from src.services.image_service import overlay_image_on_video, generate_thumbnail
        from src.services.storage_service import store_file, get_file_url, delete_file
        from src.services.ffmpeg_service import run_ffmpeg_command, get_media_info
        from src.services.webhook_service import notify_job_completed, notify_job_failed
        from src.services.cleanup_service import cleanup_temp_files
        from src.services.transcription_service import transcribe_audio
        from src.services.redis_queue_service import enqueue_task, get_task_status, update_task_status, TaskStatus
        from src.services.media_service import extract_audio, transcribe_media
        from src.services.animation_service import animated_text_service
        from src.services.queue_service import process_queue, enqueue_job
        
        # Build services dictionary
        _services = {
            'add_captions_to_video': add_captions_to_video,
            'process_meme_overlay': process_meme_overlay,
            'concatenate_videos_service': concatenate_videos_service,
            'overlay_image_on_video': overlay_image_on_video,
            'generate_thumbnail': generate_thumbnail,
            'store_file': store_file,
            'get_file_url': get_file_url,
            'delete_file': delete_file,
            'run_ffmpeg_command': run_ffmpeg_command,
            'get_media_info': get_media_info,
            'notify_job_completed': notify_job_completed,
            'notify_job_failed': notify_job_failed,
            'cleanup_temp_files': cleanup_temp_files,
            'transcribe_audio': transcribe_audio,
            'enqueue_task': enqueue_task,
            'get_task_status': get_task_status,
            'update_task_status': update_task_status,
            'TaskStatus': TaskStatus,
            'extract_audio': extract_audio,
            'transcribe_media': transcribe_media,
            'animated_text_service': animated_text_service,
            'process_queue': process_queue,
            'enqueue_job': enqueue_job
        }
    
    return _services

# Lazy getter functions for each service
def get_service(service_name):
    """Get a specific service function by name."""
    services = init_services()
    return services.get(service_name)

def get_video_service():
    """Get video service functions."""
    from src.services.video_service import add_captions_to_video, process_meme_overlay, concatenate_videos_service
    return {
        'add_captions_to_video': add_captions_to_video,
        'process_meme_overlay': process_meme_overlay,
        'concatenate_videos_service': concatenate_videos_service
    }

def get_media_service():
    """Get media service functions."""
    from src.services.media_service import extract_audio, transcribe_media
    return {
        'extract_audio': extract_audio,
        'transcribe_media': transcribe_media
    }

def get_animation_service():
    """Get animation service functions."""
    from src.services.animation_service import animated_text_service
    return {
        'animated_text_service': animated_text_service
    }
