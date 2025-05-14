from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import logging
from src.services.cleanup_service import cleanup_temp_files

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def init_scheduler(app):
    """Initialize the scheduler to run cleanup jobs"""
    try:
        # Add the cleanup job - run every 6 hours
        scheduler.add_job(
            func=cleanup_temp_files,
            trigger=IntervalTrigger(hours=6),
            id='cleanup_job',
            name='Clean temporary files',
            replace_existing=True
        )
        
        # Add initial cleanup job to run at startup after a short delay
        scheduler.add_job(
            func=cleanup_temp_files,
            trigger=IntervalTrigger(seconds=60),  # Run 1 minute after startup
            id='initial_cleanup',
            name='Initial temp files cleanup',
            replace_existing=True,
            max_instances=1
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started - cleanup job will run every 6 hours")
        
        # Register shutdown handler
        atexit.register(lambda: scheduler.shutdown())
        
    except Exception as e:
        logger.exception(f"Error initializing scheduler: {str(e)}")
