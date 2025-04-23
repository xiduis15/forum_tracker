from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Performer(Base):
    __tablename__ = 'performers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    
    threads = relationship("Thread", back_populates="performer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Performer(id={self.id}, name='{self.name}', is_active={self.is_active})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "threads": [thread.to_dict() for thread in self.threads]
        }

class Thread(Base):
    __tablename__ = 'threads'
    
    id = Column(Integer, primary_key=True)
    performer_id = Column(Integer, ForeignKey('performers.id'), nullable=False)
    url = Column(String, nullable=False)
    forum_type = Column(String, nullable=False)
    last_post_id = Column(String, nullable=True)
    last_check = Column(DateTime, default=datetime.utcnow)
    
    performer = relationship("Performer", back_populates="threads")
    
    def __repr__(self):
        return f"<Thread(id={self.id}, url='{self.url}', forum_type='{self.forum_type}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "performer_id": self.performer_id,
            "url": self.url,
            "forum_type": self.forum_type,
            "last_post_id": self.last_post_id,
            "last_check": self.last_check.isoformat() if self.last_check else None
        }

class CallbackData(Base):
    __tablename__ = 'callback_data'
    
    id = Column(Integer, primary_key=True)
    callback_id = Column(String, nullable=False, unique=True, index=True)
    data = Column(String, nullable=False)  # JSON serialized data
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<CallbackData(id={self.id}, callback_id='{self.callback_id}')>"

def init_db(db_path='forum_tracker.db'):
    """Initialize the database and create tables"""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def get_session(db_path='forum_tracker.db'):
    """Get a new database session"""
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    return Session()