from ..models import get_session
from .db import DatabaseService

def get_db_service(db_path='forum_tracker.db'):
    """Get a database service instance"""
    session = get_session(db_path)
    return DatabaseService(session)
