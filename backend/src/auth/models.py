"""Authentication models."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    username: str
    password: str


class UserInDB(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True
    scopes: list[str] = Field(default_factory=lambda: ["default"])

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    created_at: datetime
    is_active: bool
    scopes: list[str] = Field(default_factory=lambda: ["default"])


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[str] = None
