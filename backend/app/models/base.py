"""Base model class with common fields for all ORM models"""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base as SQLAlchemyBase


class BaseModel(SQLAlchemyBase):
    """Base model with common fields for all database models
    
    Provides:
    - id: Primary key
    - created_at: Timestamp of creation
    - updated_at: Timestamp of last update
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name
        
        Converts CamelCase to snake_case and adds 's' for plural
        Example: DataSource -> data_sources
        """
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return f"{name}s"
    
    def __repr__(self) -> str:
        """String representation of the model"""
        return f"<{self.__class__.__name__}(id={self.id})>"
