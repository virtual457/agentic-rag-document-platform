"""
Authentication module
"""
from .models import UserRegister, UserLogin, UserInDB, UserResponse, Token, TokenData
from .security import verify_password, get_password_hash, create_access_token, decode_access_token
from .database import mongodb
from .manager import user_auth_manager
from .dependencies import get_current_user, get_current_active_user, get_current_user_optional

__all__ = [
    # Models
    "UserRegister",
    "UserLogin",
    "UserInDB",
    "UserResponse",
    "Token",
    "TokenData",
    
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token",
    
    # Database
    "mongodb",
    
    # Manager
    "user_auth_manager",
    
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_user_optional",
]
