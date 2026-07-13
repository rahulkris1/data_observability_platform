"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth_schema import (
    LoginRequest,
    AuthResponse,
    TokenVerificationResponse,
    UserResponse
)
from app.api.auth_middleware import get_current_user, security
from app.core.exception_handler import build_success_response


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/login")
async def login(
    login_request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login endpoint - authenticate user and return JWT token
    
    Args:
        login_request: Email and password
        db: Database session
        
    Returns:
        AuthResponse with JWT token and user info
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(
        email=login_request.email,
        password=login_request.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token
    access_token, expires_at = auth_service.create_token_for_user(user)
    
    response_data = AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user_email=user.email,
        user_role=user.role.value,
        expires_at=expires_at
    )
    
    return build_success_response(
        data=response_data.dict(),
        message="Login successful"
    )


@router.post("/verify", response_model=TokenVerificationResponse)
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify JWT token endpoint
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        TokenVerificationResponse with validation status
    """
    try:
        user = await get_current_user(credentials)
        
        return TokenVerificationResponse(
            valid=True,
            user_email=user.get("sub"),
            user_role=user.get("role"),
            message="Token is valid"
        )
    except HTTPException:
        return TokenVerificationResponse(
            valid=False,
            message="Token is invalid or expired"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information
    
    Args:
        credentials: HTTP Bearer token
        db: Database session
        
    Returns:
        UserResponse with user details
    """
    user_payload = await get_current_user(credentials)
    auth_service = AuthService(db)
    
    user = auth_service.get_user_by_email(user_payload.get("sub"))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at
    )
