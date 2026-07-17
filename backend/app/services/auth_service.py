"""Authentication service for user login and token management"""
from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_token_for_user(self, user: User) -> tuple[str, str]:
        """Create JWT access token for a user
        
        Args:
            user: User object
            
        Returns:
            Tuple of (access_token, expires_at_iso_string)
        """
        token_data = {
            "sub": user.email,
            "role": user.role.value,
            "user_id": user.id
        }
        
        access_token, expires_at = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return access_token, expires_at.isoformat()
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify a JWT token and return payload
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload dict if valid, None otherwise
        """
        return decode_access_token(token)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, email: str, password: str, full_name: str, role: str = "viewer") -> User:
        """Create a new user (for testing/setup purposes)
        
        Args:
            email: User's email address
            password: Plain text password
            full_name: User's full name
            role: User role (admin or viewer)
            
        Returns:
            Created User object
        """
        from app.models.user import UserRole
        
        hashed_password = get_password_hash(password)
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole(role),
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def register_user(self, email: str, password: str, full_name: str, username: Optional[str] = None) -> User:
        """Register a new user
        
        Args:
            email: User's email address
            password: Plain text password
            full_name: User's full name
            username: Optional username
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If user with email already exists
        """
        # Check if user exists
        existing_user = self.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create the user with viewer role by default
        return self.create_user(email=email, password=password, full_name=full_name, role="viewer")
