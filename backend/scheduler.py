from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .models import Performer, Thread
from .services import get_db_service
from .services.notification import get_notification_service
from .scrapers import get_scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for scheduling scraping tasks"""
    
    def __init__(self, check_interval_seconds=7200):  # Default 2 hours
        self.scheduler = BackgroundScheduler()
        self.check_interval_seconds = check_interval_seconds
        self.db_service = get_db_service()
        self.notification_service = get_notification_service()
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            # Schedule the check task
            self.scheduler.add_job(
                self.check_all_threads,
                trigger=IntervalTrigger(seconds=self.check_interval_seconds),
                id='check_all_threads',
                name='Check all threads for new posts',
                replace_existing=True
            )
            
            # Schedule the cleanup task for expired callbacks
            self.scheduler.add_job(
                self.cleanup_expired_callbacks,
                trigger=IntervalTrigger(seconds=86400),  # Une fois par jour
                id='cleanup_expired_callbacks',
                name='Clean up expired callback data',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info(f"Scheduler started with check interval of {self.check_interval_seconds} seconds")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def check_all_threads(self):
        """Check all threads of active performers for new posts"""
        logger.info("Starting check for all threads")
        
        # Get all active performers
        performers = self.db_service.get_active_performers()
        
        for performer in performers:
            logger.info(f"Checking threads for performer: {performer.name}")
            
            # Get all threads for this performer
            threads = self.db_service.get_threads_by_performer(performer.id)
            
            for thread in threads:
                self.check_thread(thread)

    def cleanup_expired_callbacks(self):
        """Clean up expired callback data from the database"""
        logger.info("Starting cleanup of expired callback data")
        
        try:
            # Get database service
            db_service = self.db_service
            
            # Clean up expired callbacks
            deleted, error = db_service.cleanup_expired_callbacks()
            
            if error:
                logger.error(f"Error cleaning up expired callbacks: {error}")
            else:
                logger.info(f"Cleaned up {deleted} expired callback records")
        except Exception as e:
            logger.error(f"Error in cleanup_expired_callbacks: {e}")
    
    def check_thread(self, thread: Thread) -> List[Dict[str, Any]]:
        """
        Check a thread for new posts
        
        Args:
            thread: Thread object to check
            
        Returns:
            List of new posts as dictionaries
        """
        logger.info(f"Checking thread: {thread.url}")
        
        try:
            # Get the appropriate scraper
            scraper = get_scraper(thread.forum_type, thread.url, thread.last_post_id)
            
            # Check for new posts
            new_posts = scraper.check_for_new_posts()
            
            if new_posts:
                logger.info(f"Found {len(new_posts)} new posts for thread {thread.url}")
                
                # Update the thread with the latest post ID
                latest_post_id = new_posts[0].post_id if new_posts else None
                if latest_post_id:
                    success, updated_thread, error = self.db_service.update_thread(
                        thread.id, 
                        last_post_id=latest_post_id
                    )
                    if not success:
                        logger.error(f"Failed to update thread {thread.id}: {error}")
                
                # Convert posts to dictionaries for return
                post_dicts = [post.to_dict() for post in new_posts]
                
                # For now, just log the download links
                for post in new_posts:
                    if post.download_links:
                        logger.info(f"Post {post.post_id} has {len(post.download_links)} download links:")
                        for link in post.download_links:
                            logger.info(f"  - {link}")
                
                # Send notification if there are new posts
                # Get performer name for notification
                performer = self.db_service.get_performer(thread.performer_id)
                if performer and post_dicts:
                    # Send notification
                    self.notification_service.notify_new_posts(
                        performer_name=performer.name,
                        thread_url=thread.url,
                        posts=post_dicts
                    )
                    logger.info(f"Notification sent for {len(post_dicts)} new posts from {performer.name}")
                
                return post_dicts
            else:
                logger.info(f"No new posts found for thread {thread.url}")
                return []
                
        except Exception as e:
            logger.error(f"Error checking thread {thread.url}: {e}")
            return []

    def run_single_check(self, thread_id=None, performer_id=None):
        """
        Run a single check for a specific thread or all threads of a performer
        
        Args:
            thread_id: Optional ID of thread to check
            performer_id: Optional ID of performer to check all threads for
        
        Returns:
            List of new posts as dictionaries
        """
        all_new_posts = []
        
        try:
            if thread_id:
                # Check specific thread
                thread = self.db_service.get_thread(thread_id)
                if thread:
                    new_posts = self.check_thread(thread)
                    all_new_posts.extend(new_posts)
                else:
                    logger.error(f"Thread with ID {thread_id} not found")
            elif performer_id:
                # Check all threads of a performer
                performer = self.db_service.get_performer(performer_id)
                if performer:
                    threads = self.db_service.get_threads_by_performer(performer_id)
                    for thread in threads:
                        new_posts = self.check_thread(thread)
                        all_new_posts.extend(new_posts)
                else:
                    logger.error(f"Performer with ID {performer_id} not found")
            else:
                # Check all threads of all active performers
                performers = self.db_service.get_active_performers()
                for performer in performers:
                    threads = self.db_service.get_threads_by_performer(performer.id)
                    for thread in threads:
                        thread_posts = self.check_thread(thread)
                        all_new_posts.extend(thread_posts)
                        # Log the posts we're adding
                        logger.info(f"Thread {thread.id} returned {len(thread_posts)} posts. Total now: {len(all_new_posts)}")
                
            logger.info(f"Found a total of {len(all_new_posts)} new posts")
            return all_new_posts
        except Exception as e:
            logger.error(f"Error in run_single_check: {e}")
            return []