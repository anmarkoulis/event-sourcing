"""Authentication-related DTOs."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request DTO."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response DTO."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105


class TokenData(BaseModel):
    """Token payload data."""

    username: str
    user_id: str
