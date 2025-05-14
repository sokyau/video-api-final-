"""Utilities module initialization."""

__all__ = [
    # error_utils
    'format_exception',
    'handle_service_error',
    'log_exception',
    
    # ffmpeg_utils
    'build_ffmpeg_command',
    'parse_ffmpeg_output',
    'validate_ffmpeg_result',
    'format_filter_complex',
    
    # queue_manager
    'QueueManager',
    'Task',
    'TaskStatus',
    'Worker',
    
    # file_utils
    'download_file',
    'generate_temp_filename',
    'is_valid_filename',
    'safe_delete_file',
    'get_file_extension',
    'verify_file_integrity'
]

# Use lazy loading to avoid circular imports
def __getattr__(name):
    if name in ['format_exception', 'handle_service_error', 'log_exception']:
        from .error_utils import format_exception, handle_service_error, log_exception
        return locals()[name]
    elif name in ['build_ffmpeg_command', 'parse_ffmpeg_output', 'validate_ffmpeg_result', 'format_filter_complex']:
        from .ffmpeg_utils import build_ffmpeg_command, parse_ffmpeg_output, validate_ffmpeg_result, format_filter_complex
        return locals()[name]
    elif name in ['QueueManager', 'Task', 'TaskStatus', 'Worker']:
        from .queue_manager import QueueManager, Task, TaskStatus, Worker
        if name == 'TaskStatus':
            return TaskStatus
        return locals()[name]
    elif name in ['download_file', 'generate_temp_filename', 'is_valid_filename', 'safe_delete_file', 'get_file_extension', 'verify_file_integrity']:
        from .file_utils import download_file, generate_temp_filename, is_valid_filename, safe_delete_file, get_file_extension, verify_file_integrity
        return locals()[name]
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
