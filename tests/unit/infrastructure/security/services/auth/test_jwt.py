"""Unit tests for JWT authentication service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer

from event_sourcing.dto.user import UserDTO
from event_sourcing.enums import Role
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.security import (
    BcryptHashingService,
    JWTAuthService,
)


class TestJWTAuthService:
    """Test cases for JWT authentication service."""

    @pytest.fixture
    def mock_event_store(self) -> MagicMock:
        """Provide a mock event store."""
        mock = MagicMock(spec=EventStore)
        mock.search_events = AsyncMock()
        mock.get_stream = AsyncMock()
        return mock

    @pytest.fixture
    def hashing_service(self) -> BcryptHashingService:
        """Provide a real hashing service."""
        return BcryptHashingService()

    @pytest.fixture
    def auth_service(
        self,
        mock_event_store: MagicMock,
        hashing_service: BcryptHashingService,
    ) -> JWTAuthService:
        """Provide JWT auth service with mocked dependencies."""
        return JWTAuthService(mock_event_store, hashing_service)

    @pytest.fixture
    def sample_user(self) -> UserDTO:
        """Provide a sample user for testing."""
        return UserDTO(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role=Role.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def test_init(self, auth_service: JWTAuthService) -> None:
        """Test service initialization."""
        assert auth_service.algorithm == "HS256"
        assert auth_service.access_token_expire_minutes == 30
        assert auth_service.secret_key is not None

    async def test_verify_password(
        self,
        auth_service: JWTAuthService,
        hashing_service: BcryptHashingService,
    ) -> None:
        """Test password verification."""
        password = "testpassword123"  # noqa: S105  # pragma: allowlist secret
        hashed = hashing_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrongpassword", hashed) is False

    def test_get_password_hash(
        self,
        auth_service: JWTAuthService,
        hashing_service: BcryptHashingService,
    ) -> None:
        """Test password hashing."""
        password = "testpassword123"  # noqa: S105  # pragma: allowlist secret
        hashed = auth_service.get_password_hash(password)

        assert hashed != password
        assert hashing_service.verify_password(password, hashed) is True

    def test_get_scopes_for_role_admin(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test getting scopes for admin role."""
        scopes = auth_service._get_scopes_for_role("admin")
        assert scopes == [
            "user:create",
            "user:read",
            "user:update",
            "user:delete",
        ]

    def test_get_scopes_for_role_user(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test getting scopes for user role."""
        scopes = auth_service._get_scopes_for_role("user")
        assert scopes == ["user:read", "user:update"]

    def test_get_scopes_for_role_unknown(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test getting scopes for unknown role."""
        scopes = auth_service._get_scopes_for_role("unknown")
        assert scopes == []

    def test_get_scopes_for_role_case_insensitive(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test getting scopes for role with different case."""
        # The enum system is case-sensitive, so "ADMIN" should return empty scopes
        scopes = auth_service._get_scopes_for_role("ADMIN")
        assert scopes == []

    def test_get_scopes_for_role_none(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test getting scopes for None role."""
        scopes = auth_service._get_scopes_for_role(None)
        assert scopes == []

    def test_create_access_token(self, auth_service: JWTAuthService) -> None:
        """Test access token creation."""
        data = {"sub": "testuser", "user_id": str(uuid4())}
        token = auth_service.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_role_admin(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test access token creation with admin role."""
        data = {"sub": "admin", "user_id": str(uuid4()), "role": "admin"}
        token = auth_service.create_access_token(data)

        # Decode token to check scopes
        payload = auth_service.verify_token(token)
        assert "scopes" in payload
        assert payload["scopes"] == [
            "user:create",
            "user:read",
            "user:update",
            "user:delete",
        ]
        assert payload["role"] == "admin"

    def test_create_access_token_with_role_user(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test access token creation with user role."""
        data = {"sub": "user", "user_id": str(uuid4()), "role": "user"}
        token = auth_service.create_access_token(data)

        # Decode token to check scopes
        payload = auth_service.verify_token(token)
        assert "scopes" in payload
        assert payload["scopes"] == ["user:read", "user:update"]
        assert payload["role"] == "user"

    def test_create_access_token_with_unknown_role(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test access token creation with unknown role."""
        data = {"sub": "unknown", "user_id": str(uuid4()), "role": "unknown"}
        token = auth_service.create_access_token(data)

        # Decode token to check scopes
        payload = auth_service.verify_token(token)
        assert "scopes" in payload
        assert payload["scopes"] == []

    def test_create_access_token_without_role(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test access token creation without role."""
        data = {"sub": "testuser", "user_id": str(uuid4())}
        token = auth_service.create_access_token(data)

        # Decode token to check scopes
        payload = auth_service.verify_token(token)
        assert "scopes" not in payload

    def test_verify_token_valid(self, auth_service: JWTAuthService) -> None:
        """Test valid token verification."""
        data = {"sub": "testuser", "user_id": str(uuid4())}
        token = auth_service.create_access_token(data)

        payload = auth_service.verify_token(token)
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == data["user_id"]
        assert "exp" in payload

    def test_verify_token_invalid(self, auth_service: JWTAuthService) -> None:
        """Test invalid token verification."""
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token("invalid_token")

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    def test_verify_token_missing_sub(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test token verification with missing subject."""
        # Create token without 'sub' field
        data = {"user_id": str(uuid4())}
        token = auth_service.create_access_token(data)

        # This should fail because we're checking for 'sub' in verify_token
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(token)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self,
        auth_service: JWTAuthService,
        mock_event_store: MagicMock,
        sample_user: UserDTO,
        hashing_service: BcryptHashingService,
    ) -> None:
        """Test successful user authentication."""

        from event_sourcing.dto.events.user import (
            UserCreatedDataV1,
            UserCreatedV1,
        )

        # Mock the event search to return a USER_CREATED event
        from event_sourcing.enums import HashingMethod

        # Generate a proper hash for "password123"
        password = "password123"  # noqa: S105  # pragma: allowlist secret
        password_hash = hashing_service.hash_password(password)

        user_created_event = UserCreatedV1(
            aggregate_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
            revision=1,
            data=UserCreatedDataV1(
                username=sample_user.username,
                email=sample_user.email,
                first_name=sample_user.first_name,
                last_name=sample_user.last_name,
                password_hash=password_hash,
                hashing_method=HashingMethod.BCRYPT,
                role=sample_user.role,
            ),
        )

        mock_event_store.search_events.return_value = [user_created_event]
        mock_event_store.get_stream.return_value = [user_created_event]

        result = await auth_service.authenticate_user(
            "testuser",
            "password123",  # pragma: allowlist secret
        )

        assert result is not None
        assert result.username == "testuser"
        mock_event_store.search_events.assert_called_once()
        mock_event_store.get_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(
        self, auth_service: JWTAuthService, mock_event_store: MagicMock
    ) -> None:
        """Test user authentication when user not found."""
        mock_event_store.search_events.return_value = []

        result = await auth_service.authenticate_user(
            "nonexistent",
            "password123",  # pragma: allowlist secret
        )

        assert result is None
        mock_event_store.search_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(
        self,
        auth_service: JWTAuthService,
        mock_event_store: MagicMock,
        sample_user: UserDTO,
    ) -> None:
        """Test user authentication with wrong password."""
        from event_sourcing.dto.events.user import (
            UserCreatedDataV1,
            UserCreatedV1,
        )

        # Mock the event search to return a USER_CREATED event
        from event_sourcing.enums import HashingMethod

        user_created_event = UserCreatedV1(
            aggregate_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
            revision=1,
            data=UserCreatedDataV1(
                username=sample_user.username,
                email=sample_user.email,
                first_name=sample_user.first_name,
                last_name=sample_user.last_name,
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8l2",  # "password123"
                hashing_method=HashingMethod.BCRYPT,
                role=sample_user.role,
            ),
        )

        mock_event_store.search_events.return_value = [user_created_event]
        mock_event_store.get_stream.return_value = [user_created_event]

        result = await auth_service.authenticate_user(
            "testuser",
            "wrongpassword",  # pragma: allowlist secret
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_deleted_user(
        self,
        auth_service: JWTAuthService,
        mock_event_store: MagicMock,
        sample_user: UserDTO,
        hashing_service: BcryptHashingService,
    ) -> None:
        """Test user authentication when user is deleted."""
        from event_sourcing.dto.events.user import (
            UserCreatedDataV1,
            UserCreatedV1,
            UserDeletedDataV1,
            UserDeletedV1,
        )
        from event_sourcing.enums import HashingMethod

        password = "password123"  # noqa: S105  # pragma: allowlist secret
        password_hash = hashing_service.hash_password(password)

        user_created_event = UserCreatedV1(
            aggregate_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
            revision=1,
            data=UserCreatedDataV1(
                username=sample_user.username,
                email=sample_user.email,
                first_name=sample_user.first_name,
                last_name=sample_user.last_name,
                password_hash=password_hash,
                hashing_method=HashingMethod.BCRYPT,
                role=sample_user.role,
            ),
        )

        user_deleted_event = UserDeletedV1(
            aggregate_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
            revision=2,
            data=UserDeletedDataV1(),
        )

        mock_event_store.search_events.return_value = [user_created_event]
        mock_event_store.get_stream.return_value = [
            user_created_event,
            user_deleted_event,
        ]

        result = await auth_service.authenticate_user(
            "testuser",
            "password123",  # pragma: allowlist secret
        )

        assert result is None
        mock_event_store.search_events.assert_called_once()
        mock_event_store.get_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_no_user_created_event(
        self,
        auth_service: JWTAuthService,
        mock_event_store: MagicMock,
        sample_user: UserDTO,
    ) -> None:
        """Test user authentication when USER_CREATED event is missing."""
        from event_sourcing.dto.events.user import (
            UserUpdatedDataV1,
            UserUpdatedV1,
        )

        # Mock an event that's not USER_CREATED
        user_updated_event = UserUpdatedV1(
            aggregate_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
            revision=1,
            data=UserUpdatedDataV1(
                username=sample_user.username,
                email=sample_user.email,
                first_name=sample_user.first_name,
                last_name=sample_user.last_name,
                role=sample_user.role,
            ),
        )

        mock_event_store.search_events.return_value = [user_updated_event]

        result = await auth_service.authenticate_user(
            "testuser",
            "password123",  # pragma: allowlist secret
        )

        assert result is None
        mock_event_store.search_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_exception_handling(
        self,
        auth_service: JWTAuthService,
        mock_event_store: MagicMock,
    ) -> None:
        """Test user authentication when an exception occurs."""
        mock_event_store.search_events.side_effect = Exception(
            "Database error"
        )

        result = await auth_service.authenticate_user(
            "testuser",
            "password123",  # pragma: allowlist secret
        )

        assert result is None
        mock_event_store.search_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        auth_service: JWTAuthService,
        mock_event_store: MagicMock,
        sample_user: UserDTO,
    ) -> None:
        """Test getting current user from valid token."""
        from event_sourcing.dto.events.user import (
            UserCreatedDataV1,
            UserCreatedV1,
        )

        # Mock the credentials dependency
        credentials = MagicMock()
        credentials.credentials = auth_service.create_access_token(
            {"sub": "testuser", "user_id": str(sample_user.id)}
        )

        # Mock the event stream to return a USER_CREATED event
        from event_sourcing.enums import HashingMethod

        user_created_event = UserCreatedV1(
            aggregate_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
            revision=1,
            data=UserCreatedDataV1(
                username=sample_user.username,
                email=sample_user.email,
                first_name=sample_user.first_name,
                last_name=sample_user.last_name,
                password_hash="hashed_password",  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=sample_user.role,
            ),
        )

        mock_event_store.get_stream.return_value = [user_created_event]

        result = await auth_service.get_current_user(credentials)

        assert result is not None
        assert result.username == "testuser"
        mock_event_store.get_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_missing_credentials(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test getting current user when credentials are missing."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user(None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_missing_username_in_token(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test getting current user when token is missing username."""
        credentials = MagicMock()
        # Create token without 'sub' field
        credentials.credentials = auth_service.create_access_token(
            {"user_id": str(uuid4())}
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_missing_user_id_in_token(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test getting current user when token is missing user_id."""
        credentials = MagicMock()
        # Create token without 'user_id' field
        credentials.credentials = auth_service.create_access_token(
            {"sub": "testuser"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(
        self, auth_service: JWTAuthService, mock_event_store: MagicMock
    ) -> None:
        """Test getting current user when user not found in database."""
        user_id = uuid4()
        credentials = MagicMock()
        credentials.credentials = auth_service.create_access_token(
            {"sub": "testuser", "user_id": str(user_id)}
        )

        mock_event_store.get_stream.return_value = []

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_deleted_user(
        self,
        auth_service: JWTAuthService,
        mock_event_store: MagicMock,
        sample_user: UserDTO,
    ) -> None:
        """Test getting current user when user is deleted."""
        from event_sourcing.dto.events.user import (
            UserCreatedDataV1,
            UserCreatedV1,
            UserDeletedDataV1,
            UserDeletedV1,
        )
        from event_sourcing.enums import HashingMethod

        credentials = MagicMock()
        credentials.credentials = auth_service.create_access_token(
            {"sub": "testuser", "user_id": str(sample_user.id)}
        )

        user_created_event = UserCreatedV1(
            aggregate_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
            revision=1,
            data=UserCreatedDataV1(
                username=sample_user.username,
                email=sample_user.email,
                first_name=sample_user.first_name,
                last_name=sample_user.last_name,
                password_hash="hashed_password",  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=sample_user.role,
            ),
        )

        user_deleted_event = UserDeletedV1(
            aggregate_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
            revision=2,
            data=UserDeletedDataV1(),
        )

        mock_event_store.get_stream.return_value = [
            user_created_event,
            user_deleted_event,
        ]

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)

    def test_has_create_user_permission(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test create user permission method."""
        result = auth_service.has_create_user_permission()
        assert isinstance(result, OAuth2PasswordBearer)

    def test_has_read_user_permission(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test read user permission method."""
        result = auth_service.has_read_user_permission()
        assert isinstance(result, OAuth2PasswordBearer)

    def test_has_update_user_permission(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test update user permission method."""
        result = auth_service.has_update_user_permission()
        assert isinstance(result, OAuth2PasswordBearer)

    def test_has_delete_user_permission(
        self, auth_service: JWTAuthService
    ) -> None:
        """Test delete user permission method."""
        result = auth_service.has_delete_user_permission()
        assert isinstance(result, OAuth2PasswordBearer)
