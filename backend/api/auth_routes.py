"""
Authentication API routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta

from src.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    user_auth_manager,
    create_access_token,
    get_current_active_user,
    UserInDB
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    
    - **username**: 3-50 characters, unique
    - **email**: Valid email, unique
    - **password**: Minimum 6 characters
    - **full_name**: User's full name
    
    Returns JWT token for immediate login
    """
    try:
        # Create user (returns user with MongoDB ObjectId)
        user = user_auth_manager.create_user(user_data)
        
        # Generate token with user_id (not username)
        access_token = create_access_token(data={"sub": user.user_id})
        
        # Get user response (without password)
        user_response = user_auth_manager.get_user_response(user.user_id)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login with username and password
    
    Returns JWT token on success
    """
    # Authenticate user
    user = user_auth_manager.authenticate_user(
        credentials.username,
        credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token with user_id (not username)
    access_token = create_access_token(data={"sub": user.user_id})
    
    # Get user response
    user_response = user_auth_manager.get_user_response(user.user_id)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current authenticated user's information
    
    Requires valid JWT token in Authorization header
    """
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )


@router.post("/logout")
async def logout(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Logout (client should delete token)
    
    Note: JWT tokens can't be invalidated server-side.
    Client must delete the token from storage.
    """
    return {
        "message": "Logout successful",
        "username": current_user.username,
        "user_id": current_user.user_id
    }
