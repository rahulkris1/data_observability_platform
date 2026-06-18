"""Authentication schemas"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


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
