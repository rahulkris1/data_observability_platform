"""Authentication schemas"""
from pydantic import BaseModel, EmailStr, model_validator
from datetime import datetime
from typing import Optional


class LoginRequest(BaseModel):
    """Login request schema - supports both email and username"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str
    
    @model_validator(mode='after')
    def check_email_or_username(self):
        """Ensure at least one of email or username is provided"""
        if not self.email and not self.username:
            raise ValueError('Either email or username must be provided')
        return self
    
    class Config:
        # Allow extra fields for OAuth2 form compatibility
        extra = "allow"


class RegisterRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr
    password: str
    full_name: str
    username: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response schema"""
    access_token: str
    token_type: str = "bearer"
    user_email: str
    user_role: str
    expires_at: datetime


class TokenVerificationResponse(BaseModel):
    """Token verification response"""
    valid: bool
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    message: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
