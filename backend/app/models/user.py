"""User model for authentication"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Enum
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """User roles enum - limited to Admin and Viewer"""
    ADMIN = "admin"
    VIEWER = "viewer"


class User(BaseModel):
    """User model for authentication
    
    Fields:
    - email: User's email address (unique)
    - hashed_password: Bcrypt hashed password
    - full_name: User's full name
    - role: User role (admin or viewer)
    - is_active: Whether the user account is active
    """
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
