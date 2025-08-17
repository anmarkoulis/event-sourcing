"""JWT-based authentication service implementation."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)

from event_sourcing.config.settings import settings
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.dto.user import UserDTO
from event_sourcing.enums import AggregateTypeEnum, Role
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.security.services.auth.base import (
    AuthServiceInterface,
)
from event_sourcing.infrastructure.security.services.hashing.base import (
    HashingServiceInterface,
)

logger = logging.getLogger(__name__)

# JWT token security
security = HTTPBearer(auto_error=False)


class JWTAuthService(AuthServiceInterface):
    """JWT-based authentication and authorization service."""

    def __init__(
        self, event_store: EventStore, hashing_service: HashingServiceInterface
    ):
        """Initialize JWT auth service.

        :param event_store: Event store for user data access.
        :param hashing_service: Password hashing service.
        """
        self.event_store = event_store
        self.hashing_service = hashing_service
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify password against hash.

        :param plain_password: Plain text password.
        :param hashed_password: Hashed password.
        :return: True if password matches hash.
        """
        return bool(
            self.hashing_service.verify_password(
                plain_password, hashed_password
            )
        )

    def get_password_hash(self, password: str) -> str:
        """Hash password using bcrypt.

        :param password: Plain text password.
        :return: Hashed password.
        """
        return str(self.hashing_service.hash_password(password))

    def create_access_token(self, data: dict) -> str:
        """Create JWT access token with scopes.

        :param data: Token payload data.
        :return: JWT token string.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.access_token_expire_minutes
        )
        to_encode.update({"exp": expire})

        # Add scopes based on user role
        if "role" in data:
            logger.debug(f"Creating JWT with role: {data['role']}")
            scopes = self._get_scopes_for_role(data["role"])
            logger.debug(f"Generated scopes: {scopes}")
            to_encode["scopes"] = scopes
        else:
            logger.warning("No role found in JWT data")

        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm
        )
        return encoded_jwt

    def _get_scopes_for_role(self, role: str) -> list[str]:
        """Get scopes for a given role.

        :param role: User role.
        :return: List of permission scopes.
        """
        try:
            # Convert string to Role enum for type-safe comparison
            role_enum = Role(role) if role else None

            if role_enum == Role.ADMIN:
                return [
                    "user:create",
                    "user:read",
                    "user:update",
                    "user:delete",
                ]
            elif role_enum == Role.USER:
                return ["user:read", "user:update"]
            else:
                logger.warning(
                    f"Unknown role '{role}', returning empty scopes"
                )
                return []
        except ValueError:
            logger.warning(
                f"Invalid role value '{role}', returning empty scopes"
            )
            return []

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify JWT token and return payload.

        :param token: JWT token string.
        :return: Token payload data.
        :raises HTTPException: If token is invalid.
        """
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            # Type the payload as dict[str, Any] since JWT payloads are dictionaries
            payload_dict: dict[str, Any] = payload
            username: str | None = payload_dict.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return payload_dict
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserDTO]:
        """Authenticate user with username and password.

        :param username: Username to authenticate.
        :param password: Plain text password.
        :return: User DTO if authentication successful, None otherwise.
        """
        try:
            # Get event store from factory if not available
            event_store = self.event_store
            if event_store is None and hasattr(self, "_factory"):
                # Use the same pattern as command handlers
                from event_sourcing.infrastructure.event_store.psql import (
                    PostgreSQLEventStore,
                )

                # Get a fresh session from the factory
                session = await self._factory.session_manager.get_session()
                event_store = PostgreSQLEventStore(session)

                # Store the session so we can close it later
                self._current_session = session

            # Find user by username by searching events
            user_events = await event_store.search_events(
                aggregate_type=AggregateTypeEnum.USER,
                query_params={"username": username},
            )

            if not user_events:
                logger.warning(f"User not found: {username}")
                return None

            # Find the USER_CREATED event to get the user ID
            user_created_event = None
            for event in user_events:
                if event.event_type == "USER_CREATED":
                    user_created_event = event
                    break

            if not user_created_event:
                logger.warning(
                    f"USER_CREATED event not found for user: {username}"
                )
                return None

            # Replay events to get current user state
            user_aggregate = UserAggregate(user_created_event.aggregate_id)

            # Get all events for this user
            all_events = await event_store.get_stream(
                user_created_event.aggregate_id, AggregateTypeEnum.USER
            )

            # Apply all events to rebuild the aggregate state
            for event in all_events:
                user_aggregate.apply(event)

            # Check if user exists and is not deleted
            if not user_aggregate.exists() or user_aggregate.deleted_at:
                logger.warning(f"User {username} does not exist or is deleted")
                return None

            # Verify password
            if not self.verify_password(
                password, user_aggregate.password_hash
            ):
                logger.warning(f"Invalid password for user: {username}")
                return None

            # Convert to UserDTO
            user_dto = UserDTO(
                id=user_aggregate.aggregate_id,
                username=user_aggregate.username,
                email=user_aggregate.email,
                first_name=user_aggregate.first_name,
                last_name=user_aggregate.last_name,
                role=user_aggregate.role,
                created_at=user_aggregate.created_at,
                updated_at=user_aggregate.updated_at,
            )

            logger.debug(f"User authenticated successfully: {username}")
            return user_dto

        except Exception as e:
            logger.error(
                f"Error during authentication for user {username}: {e}"
            )
            return None
        finally:
            # Clean up the session if we created one
            if hasattr(self, "_current_session") and self._current_session:
                await self._current_session.close()
                self._current_session = None

    async def get_current_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            security
        ),
    ) -> UserDTO:
        """Get current authenticated user from JWT token.

        :param credentials: HTTP authorization credentials.
        :return: Current user DTO.
        :raises HTTPException: If token is invalid or user not found.
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        payload = self.verify_token(token)
        username: str | None = payload.get("sub")
        user_id: str | None = payload.get("user_id")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Get user from event store by replaying events
            user_aggregate = UserAggregate(uuid.UUID(user_id))

            # Get event store from factory if not available
            event_store = self.event_store
            if event_store is None and hasattr(self, "_factory"):
                # Use the same pattern as command handlers
                from event_sourcing.infrastructure.event_store.psql import (
                    PostgreSQLEventStore,
                )

                # Get a fresh session from the factory
                session = await self._factory.session_manager.get_session()
                event_store = PostgreSQLEventStore(session)

                # Store the session so we can close it later
                self._current_session_get_user = session

            # Get all events for this user
            all_events = await event_store.get_stream(
                uuid.UUID(user_id), AggregateTypeEnum.USER
            )

            # Apply all events to rebuild the aggregate state
            for event in all_events:
                user_aggregate.apply(event)

            # Check if user exists and is not deleted
            if not user_aggregate.exists() or user_aggregate.deleted_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Convert to UserDTO
            user_dto = UserDTO(
                id=user_aggregate.aggregate_id,
                username=user_aggregate.username,
                email=user_aggregate.email,
                first_name=user_aggregate.first_name,
                last_name=user_aggregate.last_name,
                role=user_aggregate.role,
                created_at=user_aggregate.created_at,
                updated_at=user_aggregate.updated_at,
            )

            return user_dto
        finally:
            # Clean up the session if we created one
            if (
                hasattr(self, "_current_session_get_user")
                and self._current_session_get_user
            ):
                await self._current_session_get_user.close()
                self._current_session_get_user = None

    def has_create_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for create user permission."""
        return OAuth2PasswordBearer(tokenUrl="v1/auth/login")

    def has_read_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for read user permission."""
        return OAuth2PasswordBearer(tokenUrl="v1/auth/login")

    def has_update_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for update user permission."""
        return OAuth2PasswordBearer(tokenUrl="v1/auth/login")

    def has_delete_user_permission(self) -> OAuth2PasswordBearer:
        """Get OAuth2 security scheme for delete user permission."""
        return OAuth2PasswordBearer(tokenUrl="v1/auth/login")
