"""Unit tests for UserCreatedEmailProjection."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from event_sourcing.application.projections.user.user_created_email import (
    UserCreatedEmailProjection,
)
from event_sourcing.dto.events.user.user_created import (
    UserCreatedDataV1,
    UserCreatedV1,
)
from event_sourcing.enums import EventType
from event_sourcing.infrastructure.providers.email import (
    EmailProviderInterface,
)


class TestUserCreatedEmailProjection:
    """Test cases for UserCreatedEmailProjection."""

    @pytest.fixture
    def email_provider_mock(self) -> MagicMock:
        """Provide a mock email provider."""
        mock = MagicMock(spec=EmailProviderInterface)
        mock.send_email = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def projection(
        self, email_provider_mock: MagicMock
    ) -> UserCreatedEmailProjection:
        """Provide a UserCreatedEmailProjection instance."""
        return UserCreatedEmailProjection(email_provider_mock)

    @pytest.fixture
    def user_created_event(self) -> UserCreatedV1:
        """Provide a sample USER_CREATED event."""
        return UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
            ),
        )

    @pytest.mark.asyncio
    async def test_init(self, email_provider_mock: MagicMock) -> None:
        """Test UserCreatedEmailProjection initialization."""
        projection = UserCreatedEmailProjection(email_provider_mock)

        assert projection.email_provider == email_provider_mock

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        projection: UserCreatedEmailProjection,
        user_created_event: UserCreatedV1,
    ) -> None:
        """Test successful event handling."""
        await projection.handle(user_created_event)

        # Verify email provider was called with correct parameters
        projection.email_provider.send_email.assert_awaited_once_with(
            to_email=user_created_event.data.email,
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name=user_created_event.data.first_name,
                last_name=user_created_event.data.last_name,
                username=user_created_event.data.username,
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_email_provider_error(
        self,
        projection: UserCreatedEmailProjection,
        user_created_event: UserCreatedV1,
    ) -> None:
        """Test handling when email provider fails."""
        error = Exception("Email service error")
        projection.email_provider.send_email.side_effect = error

        with pytest.raises(Exception, match="Email service error"):
            await projection.handle(user_created_event)

    @pytest.mark.asyncio
    async def test_handle_with_email_sending_failure(
        self,
        projection: UserCreatedEmailProjection,
        user_created_event: UserCreatedV1,
    ) -> None:
        """Test handling when email sending returns False."""
        projection.email_provider.send_email.return_value = False

        with pytest.raises(
            Exception,
            match="Welcome email sending failed for USER_CREATED event",
        ):
            await projection.handle(user_created_event)

    @pytest.mark.asyncio
    async def test_create_welcome_email_body_with_full_name(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with full name."""
        body = projection._create_welcome_email_body(
            first_name="John",
            last_name="Doe",
            username="johndoe",
        )

        assert "Dear John Doe," in body
        assert "johndoe" in body
        assert "John Doe" in body

    @pytest.mark.asyncio
    async def test_create_welcome_email_body_with_empty_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with empty names."""
        body = projection._create_welcome_email_body(
            first_name="",
            last_name="",
            username="usernameonly",
        )

        assert "Dear usernameonly," in body
        assert "usernameonly" in body

    @pytest.mark.asyncio
    async def test_create_welcome_email_body_with_none_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with None names."""
        # Note: Pydantic models don't allow None for these fields, so we'll test with empty strings instead
        body = projection._create_welcome_email_body(
            first_name="",  # Empty string instead of None
            last_name="",  # Empty string instead of None
            username="nonameuser",
        )

        assert "Dear nonameuser," in body
        assert "nonameuser" in body

    @pytest.mark.asyncio
    async def test_create_welcome_email_body_with_partial_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with partial names."""
        # Only first name
        body = projection._create_welcome_email_body(
            first_name="Alice",
            last_name="",
            username="aliceuser",
        )
        assert "Dear Alice," in body

        # Only last name
        body = projection._create_welcome_email_body(
            first_name="",
            last_name="Smith",
            username="smithuser",
        )
        assert "Dear Smith," in body

    @pytest.mark.asyncio
    async def test_create_welcome_email_body_with_special_characters(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with special characters in names."""
        body = projection._create_welcome_email_body(
            first_name="José",
            last_name="O'Connor",
            username="jose_user",
        )

        assert "Dear José O'Connor," in body
        assert "jose_user" in body

    @pytest.mark.asyncio
    async def test_create_welcome_email_body_with_long_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with long names."""
        long_first_name = "VeryLongFirstNameThatExceedsNormalLength"
        long_last_name = "VeryLongLastNameThatExceedsNormalLength"
        long_username = "very_long_username_that_exceeds_normal_length"

        body = projection._create_welcome_email_body(
            first_name=long_first_name,
            last_name=long_last_name,
            username=long_username,
        )

        assert f"Dear {long_first_name} {long_last_name}," in body
        assert long_username in body

    @pytest.mark.asyncio
    async def test_create_welcome_email_body_with_numbers_in_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with numbers in names."""
        body = projection._create_welcome_email_body(
            first_name="John2",
            last_name="Doe3",
            username="john2doe3",
        )

        assert "Dear John2 Doe3," in body
        assert "john2doe3" in body

    @pytest.mark.asyncio
    async def test_create_welcome_email_body_with_whitespace(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with whitespace in names."""
        body = projection._create_welcome_email_body(
            first_name="  John  ",
            last_name="  Doe  ",
            username="johndoe",
        )

        # The projection doesn't strip whitespace, so it preserves the original formatting
        assert "Dear John     Doe," in body
        assert "johndoe" in body

    @pytest.mark.asyncio
    async def test_handle_with_different_event_data(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with different event data values."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 6, 15, 14, 30, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="anotheruser",
                email="another@example.com",
                first_name="Another",
                last_name="Person",
                password_hash="different_hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email="another@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="Another",
                last_name="Person",
                username="anotheruser",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_minimal_event_data(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with minimal event data."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="minimaluser",
                email="minimal@example.com",
                first_name="",
                last_name="",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email="minimal@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="",
                last_name="",
                username="minimaluser",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_none_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with None first/last names."""
        # Note: Pydantic models don't allow None for these fields, so we'll test with empty strings instead
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="nonameuser",
                email="none@example.com",
                first_name="",  # Empty string instead of None
                last_name="",  # Empty string instead of None
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email="none@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="",
                last_name="",
                username="nonameuser",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_special_characters_in_email(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with special characters in email."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="specialuser",
                email="special+tag@example.com",
                first_name="Special",
                last_name="User",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email="special+tag@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="Special",
                last_name="User",
                username="specialuser",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_long_email(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with long email address."""
        long_email = "very_long_email_address_that_exceeds_normal_length@very_long_domain_name.com"
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="longemailuser",
                email=long_email,
                first_name="Long",
                last_name="Email",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email=long_email,
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="Long",
                last_name="Email",
                username="longemailuser",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_different_timestamp(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with different timestamp."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="yearenduser",
                email="yearend@example.com",
                first_name="Year",
                last_name="End",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email="yearend@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="Year",
                last_name="End",
                username="yearenduser",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_different_version(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with different version."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="2",
            revision=1,
            data=UserCreatedDataV1(
                username="version2user",
                email="version2@example.com",
                first_name="Version",
                last_name="Two",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email="version2@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="Version",
                last_name="Two",
                username="version2user",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_different_revision(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with different revision."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=999,
            data=UserCreatedDataV1(
                username="revision999user",
                email="revision999@example.com",
                first_name="Revision",
                last_name="NineNineNine",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email="revision999@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="Revision",
                last_name="NineNineNine",
                username="revision999user",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_with_different_event_id(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling with different event ID."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="differenteventuser",
                email="differentevent@example.com",
                first_name="Different",
                last_name="Event",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once_with(
            to_email="differentevent@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="Different",
                last_name="Event",
                username="differenteventuser",
            ),
            from_email="welcome@example.com",
        )

    @pytest.mark.asyncio
    async def test_handle_multiple_times(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test handling multiple events."""
        event1 = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="user1",
                email="user1@example.com",
                first_name="User",
                last_name="One",
                password_hash="hash1",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        event2 = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 13, 0, tzinfo=timezone.utc),
            version="1",
            revision=2,
            data=UserCreatedDataV1(
                username="user2",
                email="user2@example.com",
                first_name="User",
                last_name="Two",
                password_hash="hash2",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        await projection.handle(event1)
        await projection.handle(event2)

        # Verify both calls were made
        assert projection.email_provider.send_email.await_count == 2
        projection.email_provider.send_email.assert_any_call(
            to_email="user1@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="User",
                last_name="One",
                username="user1",
            ),
            from_email="welcome@example.com",
        )
        projection.email_provider.send_email.assert_any_call(
            to_email="user2@example.com",
            subject="Welcome to Our Platform!",
            body=projection._create_welcome_email_body(
                first_name="User",
                last_name="Two",
                username="user2",
            ),
            from_email="welcome@example.com",
        )
