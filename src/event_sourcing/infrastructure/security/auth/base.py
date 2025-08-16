"""Authentication and authorization service interface."""

from abc import ABC, abstractmethod
from typing import Optional

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)

from event_sourcing.dto.user import UserDTO


class AuthServiceInterface(ABC):
    """Interface for authentication services."""

    @abstractmethod
    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserDTO]:
        """Authenticate user with username and password."""
        raise NotImplementedError()

    @abstractmethod
    async def get_current_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer()
        ),
    ) -> UserDTO:
        """Get current authenticated user from JWT token."""
        raise NotImplementedError()

    @abstractmethod
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token."""
        raise NotImplementedError()

    @abstractmethod
    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload."""
        raise NotImplementedError()

    @abstractmethod
    def has_create_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for create user permission."""
        raise NotImplementedError()

    @abstractmethod
    def has_read_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for read user permission."""
        raise NotImplementedError()

    @abstractmethod
    def has_update_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for update user permission."""
        raise NotImplementedError()

    @abstractmethod
    def has_delete_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for delete user permission."""
        raise NotImplementedError()
