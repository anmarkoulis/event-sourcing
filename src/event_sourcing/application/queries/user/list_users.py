from typing import Optional

from pydantic import BaseModel, Field


class ListUsersQuery(BaseModel):
    """Query to list users with pagination and filtering"""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(
        10, ge=1, le=100, description="Number of items per page"
    )
    username: Optional[str] = Field(
        None, description="Filter by username (partial match)"
    )
    email: Optional[str] = Field(
        None, description="Filter by email (partial match)"
    )
    status: Optional[str] = Field(None, description="Filter by status")
