import logging
import time
from functools import wraps
from typing import Any, Callable

# Configure the debug logger
debug_logger = logging.getLogger('forum_tracker.debug')
debug_logger.setLevel(logging.DEBUG)

# Create file handler
fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# Add handler to logger
debug_logger.addHandler(fh)

def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        debug_logger.debug(
            f"{func.__name__} executed in {end_time - start_time:.2f} seconds"
        )
        return result
    return wrapper

def log_data_flow(tag: str) -> Callable:
    """Decorator to log input/output data flow"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            debug_logger.debug(
                f"{tag} - {func.__name__} called with args: {args}, kwargs: {kwargs}"
            )
            result = func(*args, **kwargs)
            debug_logger.debug(
                f"{tag} - {func.__name__} returned: {result}"
            )
            return result
        return wrapper
    return decorator

def log_error(e: Exception, context: str = "") -> None:
    """Utility function to log errors with context"""
    debug_logger.error(f"Error in {context}: {str(e)}", exc_info=True)