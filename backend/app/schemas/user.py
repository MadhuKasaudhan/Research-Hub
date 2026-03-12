"""User Pydantic schemas for request/response validation."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: str = Field(
        ..., min_length=5, max_length=255, description="User email address"
    )
    password: str = Field(
        ..., min_length=8, max_length=128, description="User password"
    )
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")


class UserLogin(BaseModel):
    """Schema for user login."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserWithToken(BaseModel):
    """Schema for registration response with token."""

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
