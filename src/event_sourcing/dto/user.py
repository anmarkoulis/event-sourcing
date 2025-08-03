from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from event_sourcing.dto.base import ModelConfigBaseModel


class UserDTO(ModelConfigBaseModel):
    """User DTO for API responses"""

    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    status: str = Field(..., description="User status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# API Request/Response Models
class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str  # Will be hashed before storing


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class ChangeUsernameRequest(BaseModel):
    new_username: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class CompletePasswordResetRequest(BaseModel):
    new_password: str
    reset_token: str


# Read Model DTOs
class UserReadModelData(BaseModel):
    """Data model for read model operations"""

    aggregate_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password_hash: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
