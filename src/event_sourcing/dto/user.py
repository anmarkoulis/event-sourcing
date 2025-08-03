from datetime import datetime
from typing import Any, Dict, List, Optional
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


class CreateUserResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Success message")
    user_id: str = Field(..., description="Created user ID")


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UpdateUserResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Success message")


class ChangeUsernameRequest(BaseModel):
    new_username: str


class ChangeUsernameResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Success message")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Success message")


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class RequestPasswordResetResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Success message")


class CompletePasswordResetRequest(BaseModel):
    new_password: str
    reset_token: str


class CompletePasswordResetResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Success message")


class DeleteUserResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Success message")


class GetUserResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    user: UserDTO = Field(..., description="User data")


class GetUserHistoryResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    user_id: str = Field(..., description="User ID")
    count: int = Field(..., description="Number of events")
    events: List[Dict[str, Any]] = Field(..., description="Event history")


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
