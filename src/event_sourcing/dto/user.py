from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.enums import Role


class UserDTO(ModelConfigBaseModel):
    """User DTO for API responses"""

    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: Role = Field(default=Role.USER, description="User role")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# API Request/Response Models
class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(
        ..., min_length=1, description="Password cannot be empty"
    )


class CreateUserResponse(BaseModel):
    message: str = Field(..., description="Success message")
    user_id: str = Field(..., description="Created user ID")


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UpdateUserResponse(BaseModel):
    message: str = Field(..., description="Success message")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    message: str = Field(..., description="Success message")


class DeleteUserResponse(BaseModel):
    message: str = Field(..., description="Success message")


class GetUserResponse(BaseModel):
    user: UserDTO = Field(..., description="User data")


class GetUserHistoryResponse(BaseModel):
    user_id: str = Field(..., description="User ID")
    timestamp: datetime = Field(..., description="Point in time for the state")
    user: Optional[UserDTO] = Field(
        None, description="User state at the specified time"
    )


class ListUsersResponse(BaseModel):
    next: Optional[str] = Field(None, description="Next page URL")
    previous: Optional[str] = Field(None, description="Previous page URL")
    count: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    results: List[UserDTO] = Field(..., description="List of users")


# Read Model DTOs
class UserReadModelData(BaseModel):
    """Data model for read model operations"""

    aggregate_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[Role] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
