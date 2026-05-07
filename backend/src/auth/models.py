"""
Authentication models using Pydantic
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class ProfileCompletionStatus(BaseModel):
    """Profile completion tracking"""
    percentage: int = 0  # 0-100
    status: str = "incomplete"  # incomplete, needs_improvement, ready
    feedback: str = "No profile data provided yet"
    missing_sections: list[str] = []
    last_analyzed: Optional[datetime] = None


class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str


class UserProfile(BaseModel):
    """User profile data structure"""
    personal: dict = {}
    education: list = []
    work_experience: list = []
    skills: list = []
    projects: list = []
    certifications: list = []
    achievements: list = []


class UserInDB(BaseModel):
    """User as stored in database"""
    user_id: str  # MongoDB ObjectId as string
    username: str
    email: str
    full_name: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True
    
    # Profile data
    profile: UserProfile = Field(default_factory=UserProfile)
    profile_completion: ProfileCompletionStatus = Field(default_factory=ProfileCompletionStatus)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserResponse(BaseModel):
    """User data returned to client (no password)"""
    user_id: str
    username: str
    email: str
    full_name: str
    created_at: datetime
    is_active: bool
    profile_completion: ProfileCompletionStatus


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Data stored in JWT token"""
    user_id: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile"""
    profile_data: dict  # Can be full profile or partial update
    analyze: bool = True  # Whether to run LLM analysis after update
