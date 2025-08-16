"""JWT-based authentication service."""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jwt.exceptions import PyJWTError

from event_sourcing.config.settings import settings
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.dto.user import UserDTO
from event_sourcing.infrastructure.event_store import PostgreSQLEventStore
from event_sourcing.infrastructure.security.hashing.base import (
    HashingServiceInterface,
)

from .base import AuthServiceInterface

logger = logging.getLogger(__name__)

# JWT security scheme
security = HTTPBearer()


class JWTAuthService(AuthServiceInterface):
    """JWT-based authentication service."""

    def __init__(
        self,
        event_store: Optional[PostgreSQLEventStore],
        hashing_service: HashingServiceInterface,
    ) -> None:
        """Initialize JWT auth service.

        :param event_store: Event store for user authentication.
        :param hashing_service: Service for password hashing.
        """
        self.event_store = event_store
        self.hashing_service = hashing_service
        self._factory: Optional[Any] = None

    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserDTO]:
        """Authenticate user with username and password.

        :param username: Username to authenticate.
        :param password: Plain text password.
        :return: User DTO if authentication successful, None otherwise.
        """
        try:
            # Get event store from factory if not provided
            if not self.event_store and self._factory:
                from event_sourcing.infrastructure.event_store import (
                    PostgreSQLEventStore,
                )

                session = await self._factory.session_manager.get_session()
                self.event_store = PostgreSQLEventStore(session)

            if not self.event_store:
                logger.error("No event store available for authentication")
                return None

            # Get user aggregate from event store
            user_aggregate = await self._get_user_aggregate(username)
            if not user_aggregate or not user_aggregate.exists():
                logger.warning(f"User not found: {username}")
                return None

            # Verify password
            if not self.hashing_service.verify_password(
                password, user_aggregate.password_hash or ""
            ):
                logger.warning(f"Invalid password for user: {username}")
                return None

            # Convert to DTO
            return UserDTO(
                id=user_aggregate.aggregate_id,
                username=user_aggregate.username or "",
                email=user_aggregate.email or "",
                first_name=user_aggregate.first_name,
                last_name=user_aggregate.last_name,
                role=user_aggregate.role,
                created_at=user_aggregate.created_at or datetime.utcnow(),
                updated_at=user_aggregate.updated_at or datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None

    async def get_current_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            security
        ),
    ) -> UserDTO:
        """Get current authenticated user from JWT token.

        :param credentials: HTTP authorization credentials.
        :return: Current authenticated user.
        :raises HTTPException: If token is invalid or user not found.
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = self.verify_token(credentials.credentials)
            username: Optional[str] = payload.get("sub")
            user_id: Optional[str] = payload.get("user_id")

            if username is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Get user aggregate from event store
            user_aggregate = await self._get_user_aggregate(username)
            if not user_aggregate or not user_aggregate.exists():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Convert to DTO
            return UserDTO(
                id=user_aggregate.aggregate_id,
                username=user_aggregate.username or "",
                email=user_aggregate.email or "",
                first_name=user_aggregate.first_name,
                last_name=user_aggregate.last_name,
                role=user_aggregate.role,
                created_at=user_aggregate.created_at or datetime.utcnow(),
                updated_at=user_aggregate.updated_at or datetime.utcnow(),
            )

        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def create_access_token(self, data: dict) -> str:
        """Create JWT access token.

        :param data: Data to encode in token.
        :return: JWT token string.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify JWT token and return payload.

        :param token: JWT token to verify.
        :return: Token payload.
        :raises PyJWTError: If token is invalid.
        """
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload

    def has_create_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for create user permission.

        :return: OAuth2 security scheme.
        """
        return OAuth2PasswordBearer(tokenUrl="v1/auth/login")

    def has_read_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for read user permission.

        :return: OAuth2 security scheme.
        """
        return OAuth2PasswordBearer(tokenUrl="v1/auth/login")

    def has_update_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for update user permission.

        :return: OAuth2 security scheme.
        """
        return OAuth2PasswordBearer(tokenUrl="v1/auth/login")

    def has_delete_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for delete user permission.

        :return: OAuth2 security scheme.
        """
        return OAuth2PasswordBearer(tokenUrl="v1/auth/login")

    async def _get_user_aggregate(
        self, username: str
    ) -> Optional[UserAggregate]:
        """Get user aggregate by username.

        :param username: Username to search for.
        :return: User aggregate if found, None otherwise.
        """
        try:
            # This is a simplified implementation
            # In a real system, you'd query the read model or event store
            # For now, we'll return None to indicate user not found
            logger.warning(
                f"User lookup not implemented for username: {username}"
            )
            return None
        except Exception as e:
            logger.error(f"Error getting user aggregate: {e}")
            return None
