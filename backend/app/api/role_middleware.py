"""Role-based access control middleware"""
from fastapi import HTTPException, status, Depends
from typing import List

from app.api.auth_middleware import get_current_user, security
from fastapi.security import HTTPAuthorizationCredentials


class RoleChecker:
    """Dependency class for role-based access control"""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Check if user has required role
        
        Args:
            credentials: HTTP Bearer token credentials
            
        Returns:
            User payload if authorized
            
        Raises:
            HTTPException: If user doesn't have required role
        """
        user = await get_current_user(credentials)
        
        user_role = user.get("role")
        
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {', '.join(self.allowed_roles)}"
            )
        
        return user


# Pre-defined role checkers
require_admin = RoleChecker(allowed_roles=["admin"])
require_viewer = RoleChecker(allowed_roles=["admin", "viewer"])
