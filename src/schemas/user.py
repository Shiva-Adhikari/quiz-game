# Standard library imports
import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(
        min_length=4, max_length=50,
        description='Username must be between 4 to 22 characters')
    password: str = Field(min_length=8, max_length=255)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 character long')
        if not re.search(r'[A-Z]', v):
            raise ValueError(
                'Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError(
                'Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError(
                'Password must contain at least one special character')
        return v


class UserLogin(BaseModel):
    username: str = Field(min_length=4, max_length=50)
    password: str = Field(min_length=8, max_length=255)


class UserResponse(BaseModel):
    id: int = Field(gt=0, description='Unique user identifier')
    email: EmailStr
    username: str = Field(min_length=4, max_length=22)
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # best for return to user/client


class LoginResponse(BaseModel):
    message: str
    user: UserResponse

    class Config:
        from_attributes = True  # best for return to user/client
