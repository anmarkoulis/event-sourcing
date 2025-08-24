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
from event_sourcing.enums import EventType, HashingMethod, Role
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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
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
        projection.email_provider.send_email.assert_awaited_once()

        # Get the call arguments to verify the body content
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == user_created_event.data.email
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"

        # Verify the email body contains expected content
        body = call_args.kwargs["body"]
        assert "Dear Test User," in body
        assert "testuser" in body
        assert "Test User" in body

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
    async def test_handle_with_full_name(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with full name through public interface."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="johndoe",
                email="john@example.com",
                first_name="John",
                last_name="Doe",
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        # Verify the email body contains expected content
        call_args = projection.email_provider.send_email.call_args
        body = call_args.kwargs["body"]
        assert "Dear John Doe," in body
        assert "johndoe" in body
        assert "John Doe" in body

    @pytest.mark.asyncio
    async def test_handle_with_empty_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with empty names through public interface."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="usernameonly",
                email="user@example.com",
                first_name="",
                last_name="",
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        # Verify the email body contains expected content
        call_args = projection.email_provider.send_email.call_args
        body = call_args.kwargs["body"]
        assert "Dear usernameonly," in body
        assert "usernameonly" in body

    @pytest.mark.asyncio
    async def test_handle_with_partial_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with partial names through public interface."""
        # Only first name
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="aliceuser",
                email="alice@example.com",
                first_name="Alice",
                last_name="",
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        # Verify the email body contains expected content
        call_args = projection.email_provider.send_email.call_args
        body = call_args.kwargs["body"]
        assert "Dear Alice," in body
        assert "aliceuser" in body
        assert "Alice" in body

        # Only last name
        event2 = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="bobuser",
                email="bob@example.com",
                first_name="",
                last_name="Smith",
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event2)

        # Verify the email body contains expected content
        call_args = projection.email_provider.send_email.call_args
        body = call_args.kwargs["body"]
        assert "Dear Smith," in body
        assert "bobuser" in body
        assert "Smith" in body

    @pytest.mark.asyncio
    async def test_handle_with_special_characters(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with special characters in names."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="jose_user",
                email="jose@example.com",
                first_name="José",
                last_name="O'Connor",
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        # Verify the email body contains expected content
        call_args = projection.email_provider.send_email.call_args
        body = call_args.kwargs["body"]
        assert "Dear José O'Connor," in body
        assert "jose_user" in body

    @pytest.mark.asyncio
    async def test_handle_with_long_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with long names."""
        long_first_name = "VeryLongFirstNameThatExceedsNormalLength"
        long_last_name = "VeryLongLastNameThatExceedsNormalLength"
        long_username = "very_long_username_that_exceeds_normal_length"

        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username=long_username,
                email="long@example.com",
                first_name=long_first_name,
                last_name=long_last_name,
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        # Verify the email body contains expected content
        call_args = projection.email_provider.send_email.call_args
        body = call_args.kwargs["body"]
        assert f"Dear {long_first_name} {long_last_name}," in body
        assert long_username in body

    @pytest.mark.asyncio
    async def test_handle_with_numbers_in_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with numbers in names."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="john2doe3",
                email="numbers@example.com",
                first_name="John2",
                last_name="Doe3",
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        # Verify the email body contains expected content
        call_args = projection.email_provider.send_email.call_args
        body = call_args.kwargs["body"]
        assert "Dear John2 Doe3," in body
        assert "john2doe3" in body

    @pytest.mark.asyncio
    async def test_handle_with_whitespace(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test welcome email body creation with whitespace in names."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="johndoe",
                email="whitespace@example.com",
                first_name="  John  ",
                last_name="  Doe  ",
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        # Verify the email body contains expected content
        call_args = projection.email_provider.send_email.call_args
        body = call_args.kwargs["body"]
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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "another@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert "Dear Another Person," in body
        assert "anotheruser" in body
        assert "Another Person" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "minimal@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert "Dear minimaluser," in body  # Empty names fall back to username
        assert "minimaluser" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "none@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert "Dear nonameuser," in body  # Empty names fall back to username
        assert "nonameuser" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "special+tag@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert "Dear Special User," in body
        assert "specialuser" in body
        assert "Special User" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == long_email
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert "Dear Long Email," in body
        assert "longemailuser" in body
        assert "Long Email" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "yearend@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert "Dear Year End," in body
        assert "yearenduser" in body
        assert "Year End" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "version2@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert "Dear Version Two," in body  # Uses actual first + last name
        assert "version2user" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "revision999@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert (
            "Dear Revision NineNineNine," in body
        )  # Uses actual first + last name
        assert "revision999user" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event)

        projection.email_provider.send_email.assert_awaited_once()
        call_args = projection.email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "differentevent@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        body = call_args.kwargs["body"]
        assert "Dear Different Event," in body  # Uses actual first + last name
        assert "differenteventuser" in body

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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
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
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        await projection.handle(event1)
        await projection.handle(event2)

        # Verify both calls were made
        assert projection.email_provider.send_email.await_count == 2

        # Get all calls to send_email
        calls = projection.email_provider.send_email.call_args_list

        # Verify first call
        first_call = calls[0]
        assert first_call.kwargs["to_email"] == "user1@example.com"
        assert first_call.kwargs["subject"] == "Welcome to Our Platform!"
        assert first_call.kwargs["from_email"] == "welcome@example.com"
        first_body = first_call.kwargs["body"]
        assert "Dear User One," in first_body
        assert "user1" in first_body

        # Verify second call
        second_call = calls[1]
        assert second_call.kwargs["to_email"] == "user2@example.com"
        assert second_call.kwargs["subject"] == "Welcome to Our Platform!"
        assert second_call.kwargs["from_email"] == "welcome@example.com"
        second_body = second_call.kwargs["body"]
        assert "Dear User Two," in second_body
        assert "user2" in second_body
