from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.schemas.base import BaseSchema


class UserResponse(BaseSchema):
    """User response schema without password."""
    id: UUID
    email: EmailStr
    full_name: str
    role: Literal["student", "teacher"]
    class_level: int | None = None
    created_at: datetime


class AuthTokenResponse(BaseSchema):
    """Authentication token response with user data."""
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int
    user: UserResponse


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=200)
    role: Literal["student", "teacher"]
    class_level: int | None = Field(default=10)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "student@example.com",
            "password": "StrongPassword123!",
            "full_name": "Asha Sharma",
            "role": "student",
            "class_level": 10
        }
    })


class LogoutResponse(BaseModel):
    """Logout response."""
    message: str = "Logged out successfully"


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: UUID  # subject is the user_id
    exp: int  # expiration time
    iat: int  # issued at
    role: Literal["student", "teacher"]
