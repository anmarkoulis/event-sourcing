"""Authentication DTOs."""

from pydantic import BaseModel

from event_sourcing.dto.user import UserDTO


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    token_type: str
    user: UserDTO
