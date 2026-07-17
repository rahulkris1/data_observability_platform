"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    TokenVerificationResponse,
    UserResponse
)
from app.api.auth_middleware import get_current_user, security
from app.core.exception_handler import build_success_response


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    register_request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user
    
    Args:
        register_request: User registration data
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user already exists
    """
    auth_service = AuthService(db)
    
    # Check if user already exists
    try:
        user = auth_service.register_user(
            email=register_request.email,
            password=register_request.password,
            full_name=register_request.full_name,
            username=register_request.username
        )
        
        return build_success_response(
            data={"email": user.email, "full_name": user.full_name},
            message="User registered successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/login")
async def login(
    login_request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login endpoint - authenticate user and return JWT token
    
    Supports both JSON body and form data.
    Accepts either email or username field.
    
    Args:
        login_request: Login credentials (email/username + password)
        db: Database session
        
    Returns:
        AuthResponse with JWT token and user info
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    
    # Use email if provided, otherwise use username
    email = login_request.email if login_request.email else login_request.username
    
    try:
        user = auth_service.authenticate_user(
            email=email,
            password=login_request.password
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
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
