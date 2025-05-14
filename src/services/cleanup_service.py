# src/services/cleanup_service.py
import os
import logging
import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from ..config import settings

logger = logging.getLogger(__name__)

class CleanupService:
    def __init__(self):
        self.running = False
        self.scheduler = BackgroundScheduler()
        self.temp_file_max_age = 86400  # 24 hours

    def start(self):
        if self.running:
            logger.warning("Cleanup service is already running")
            return

        self.running = True
        
        # Schedule cleanup job every 6 hours
        self.scheduler.add_job(
            self._cleanup_temp_files,
            'interval',
            hours=6,
            id='cleanup_temp_files',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        
        logger.info("Cleanup service started with 6-hour interval")

    def stop(self):
        if not self.running:
            logger.warning("Cleanup service is not running")
            return

        self.running = False
        
        # Shutdown the scheduler
        self.scheduler.shutdown()
        
        logger.info("Cleanup service stopped")

    def _cleanup_temp_files(self):
        """Clean up old temporary files"""
        start_time = time.time()
        logger.info("Starting cleanup of temporary files")
        
        # Calculate the cutoff date for files to delete
        cutoff_time = time.time() - self.temp_file_max_age
        cutoff_datetime = datetime.datetime.fromtimestamp(cutoff_time)
        
        deleted_count = 0
        total_size = 0
        
        # Walk through the temp directory and its subdirectories
        for root, _, files in os.walk(settings.TEMP_DIR):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                try:
                    # Get the file's last modification time
                    file_mtime = os.path.getmtime(file_path)
                    
                    # If the file is older than the cutoff, delete it
                    if file_mtime < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        total_size += file_size
                        logger.debug(f"Temporary file deleted: {file_path}")
                        
                except Exception as e:
                    logger.warning(f"Error processing temporary file {file_path}: {str(e)}")
        
        duration = time.time() - start_time
        logger.info(f"Cleanup completed in {duration:.2f}s: {deleted_count} files deleted, "
                   f"{total_size / (1024*1024):.2f} MB freed")
        
        return {
            "deleted_count": deleted_count,
            "total_size_bytes": total_size,
            "duration_seconds": duration,
            "cutoff_datetime": cutoff_datetime.isoformat()
        }

# Singleton instance of the cleanup service
cleanup_service = CleanupService()

def cleanup_temp_files():
    """
    Utility function to run temporary file cleanup on demand.
    """
    return cleanup_service._cleanup_temp_files()

def init_cleanup_service():
    """
    Initialize and start the cleanup service.
    Should be called during application startup.
    """
    cleanup_service.start()
    return cleanup_service
