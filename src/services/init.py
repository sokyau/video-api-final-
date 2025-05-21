"""
Services module initialization.
All imports are within __all__ to avoid circular imports.
"""

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
    'animated_text_service',
    'add_audio_to_video'
]

def __getattr__(name):
    """Lazy import strategy to avoid circular imports"""
    if name in __all__:
        if name in ['add_captions_to_video', 'process_meme_overlay', 'concatenate_videos_service', 'add_audio_to_video']:
            from .video_service import add_captions_to_video, process_meme_overlay, concatenate_videos_service, add_audio_to_video
            return locals()[name]
        elif name in ['overlay_image_on_video', 'generate_thumbnail']:
            from .image_service import overlay_image_on_video, generate_thumbnail
            return locals()[name]
        elif name in ['store_file', 'get_file_url', 'delete_file']:
            from .storage_service import store_file, get_file_url, delete_file
            return locals()[name]
        elif name in ['run_ffmpeg_command', 'get_media_info']:
            from .ffmpeg_service import run_ffmpeg_command, get_media_info
            return locals()[name]
        elif name in ['notify_job_completed', 'notify_job_failed']:
            from .webhook_service import notify_job_completed, notify_job_failed
            return locals()[name]
        elif name == 'cleanup_temp_files':
            from .cleanup_service import cleanup_temp_files
            return cleanup_temp_files
        elif name == 'transcribe_audio':
            from .transcription_service import transcribe_audio
            return transcribe_audio
        elif name in ['enqueue_task', 'get_task_status', 'update_task_status', 'TaskStatus']:
            from .redis_queue_service import enqueue_task, get_task_status, update_task_status, TaskStatus
            if name == 'TaskStatus':
                return TaskStatus
            return locals()[name]
        elif name in ['extract_audio', 'transcribe_media']:
            from .media_service import extract_audio, transcribe_media
            return locals()[name]
        elif name == 'animated_text_service':
            from .animation_service import animated_text_service
            return animated_text_service
        elif name in ['process_queue', 'enqueue_job']:
            from .queue_service import process_queue, enqueue_job
            return locals()[name]
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
