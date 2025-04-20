from .base import BaseScraper, Post
from .planetsuzy import PlanetSuzyScraper

# Factory pattern to get appropriate scraper based on forum type
def get_scraper(forum_type: str, thread_url: str, last_post_id=None) -> BaseScraper:
    """
    Returns the appropriate scraper based on the forum type
    
    Args:
        forum_type: Type of forum (e.g., 'planetsuzy')
        thread_url: URL of the thread to scrape
        last_post_id: ID of the last seen post
        
    Returns:
        An instance of a BaseScraper subclass
        
    Raises:
        ValueError: If forum_type is not supported
    """
    if forum_type == 'planetsuzy':
        return PlanetSuzyScraper(thread_url, last_post_id)
    else:
        raise ValueError(f"Unsupported forum type: {forum_type}")

# Auto-detect forum type from URL
def detect_forum_type(url: str) -> str:
    """
    Detects the forum type from the URL
    
    Args:
        url: URL of the thread
        
    Returns:
        Forum type as a string
        
    Raises:
        ValueError: If forum type cannot be detected
    """
    if 'planetsuzy' in url:
        return 'planetsuzy'
    else:
        raise ValueError(f"Could not detect forum type from URL: {url}")
