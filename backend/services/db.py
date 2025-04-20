from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models import Performer, Thread

class DatabaseService:
    """Service for database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    # Performer operations
    def get_all_performers(self) -> List[Performer]:
        """Get all performers from the database"""
        return self.session.query(Performer).all()
    
    def get_active_performers(self) -> List[Performer]:
        """Get all active performers from the database"""
        return self.session.query(Performer).filter(Performer.is_active == True).all()
    
    def get_performer(self, performer_id: int) -> Optional[Performer]:
        """Get a performer by ID"""
        return self.session.query(Performer).filter(Performer.id == performer_id).first()
    
    def create_performer(self, name: str, is_active: bool = True) -> Tuple[bool, Optional[Performer], str]:
        """Create a new performer"""
        try:
            performer = Performer(name=name, is_active=is_active)
            self.session.add(performer)
            self.session.commit()
            return True, performer, ""
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, None, str(e)
    
    def update_performer(self, performer_id: int, name: Optional[str] = None, 
                        is_active: Optional[bool] = None) -> Tuple[bool, Optional[Performer], str]:
        """Update a performer"""
        try:
            performer = self.get_performer(performer_id)
            if not performer:
                return False, None, f"Performer with ID {performer_id} not found"
            
            if name is not None:
                performer.name = name
            if is_active is not None:
                performer.is_active = is_active
            
            self.session.commit()
            return True, performer, ""
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, None, str(e)
    
    def delete_performer(self, performer_id: int) -> Tuple[bool, str]:
        """Delete a performer"""
        try:
            performer = self.get_performer(performer_id)
            if not performer:
                return False, f"Performer with ID {performer_id} not found"
            
            self.session.delete(performer)
            self.session.commit()
            return True, ""
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, str(e)
    
    # Thread operations
    def get_all_threads(self) -> List[Thread]:
        """Get all threads from the database"""
        return self.session.query(Thread).all()
    
    def get_thread(self, thread_id: int) -> Optional[Thread]:
        """Get a thread by ID"""
        return self.session.query(Thread).filter(Thread.id == thread_id).first()
    
    def get_threads_by_performer(self, performer_id: int) -> List[Thread]:
        """Get all threads for a performer"""
        return self.session.query(Thread).filter(Thread.performer_id == performer_id).all()
    
    def create_thread(self, performer_id: int, url: str, forum_type: str) -> Tuple[bool, Optional[Thread], str]:
        """Create a new thread"""
        try:
            # Check if performer exists
            performer = self.get_performer(performer_id)
            if not performer:
                return False, None, f"Performer with ID {performer_id} not found"
            
            thread = Thread(
                performer_id=performer_id,
                url=url,
                forum_type=forum_type,
                last_check=datetime.utcnow()
            )
            self.session.add(thread)
            self.session.commit()
            return True, thread, ""
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, None, str(e)
    
    def update_thread(self, thread_id: int, url: Optional[str] = None, 
                     forum_type: Optional[str] = None, 
                     last_post_id: Optional[str] = None) -> Tuple[bool, Optional[Thread], str]:
        """Update a thread"""
        try:
            thread = self.get_thread(thread_id)
            if not thread:
                return False, None, f"Thread with ID {thread_id} not found"
            
            if url is not None:
                thread.url = url
            if forum_type is not None:
                thread.forum_type = forum_type
            if last_post_id is not None:
                thread.last_post_id = last_post_id
            
            thread.last_check = datetime.utcnow()
            self.session.commit()
            return True, thread, ""
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, None, str(e)
    
    def delete_thread(self, thread_id: int) -> Tuple[bool, str]:
        """Delete a thread"""
        try:
            thread = self.get_thread(thread_id)
            if not thread:
                return False, f"Thread with ID {thread_id} not found"
            
            self.session.delete(thread)
            self.session.commit()
            return True, ""
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, str(e)
