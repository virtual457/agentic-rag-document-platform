"""
FastAPI dependencies for authentication
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from .manager import user_auth_manager
from .security import decode_access_token
from .models import UserInDB

# OAuth2 scheme (extracts token from Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    FastAPI dependency to get current authenticated user
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: UserInDB = Depends(get_current_user)):
            return {"message": f"Hello {user.username}"}
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        Authenticated user object
        
    Raises:
        HTTPException: 401 if token invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token to get user_id
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception
    
    # Get user from database by ID
    user = user_auth_manager.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Ensure user account is active
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: UserInDB = Depends(get_current_active_user)):
            return {"message": f"Hello active user {user.username}"}
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return current_user


# Optional auth - returns None if not authenticated (for public + private routes)
async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[UserInDB]:
    """
    Get current user if authenticated, None otherwise
    Useful for routes that work differently for logged-in users
    """
    if not token:
        return None
    
    try:
        user_id = decode_access_token(token)
        if user_id:
            return user_auth_manager.get_user_by_id(user_id)
    except:
        pass
    
    return None
