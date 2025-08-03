from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

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
