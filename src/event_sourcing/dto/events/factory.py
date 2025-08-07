import uuid
from datetime import datetime, timezone
from typing import Optional, TypeVar

from event_sourcing.dto.events.base import EventDTO
from event_sourcing.dto.events.user import (
    PasswordChangedDataV1,
    PasswordChangedV1,
    PasswordResetCompletedDataV1,
    PasswordResetCompletedV1,
    PasswordResetRequestedDataV1,
    PasswordResetRequestedV1,
    UserCreatedDataV1,
    UserCreatedV1,
    UserDeletedDataV1,
    UserDeletedV1,
    UsernameChangedDataV1,
    UsernameChangedV1,
    UserUpdatedDataV1,
    UserUpdatedV1,
)

T = TypeVar("T", bound=EventDTO)


class EventFactory:
    """Factory for creating versioned events"""

    @staticmethod
    def create_user_created(
        aggregate_id: uuid.UUID,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        password_hash: str,
        revision: int,
        timestamp: Optional[datetime] = None,
    ) -> UserCreatedV1:
        """Create a USER_CREATED event"""
        data = UserCreatedDataV1(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
        )

        return UserCreatedV1(
            aggregate_id=aggregate_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            revision=revision,
            data=data,
        )

    @staticmethod
    def create_user_updated(
        aggregate_id: uuid.UUID,
        username: Optional[str] = None,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        revision: int = 1,
        timestamp: Optional[datetime] = None,
    ) -> UserUpdatedV1:
        """Create a USER_UPDATED event"""
        data = UserUpdatedDataV1(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        return UserUpdatedV1(
            aggregate_id=aggregate_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            revision=revision,
            data=data,
        )

    @staticmethod
    def create_user_deleted(
        aggregate_id: uuid.UUID,
        revision: int,
        timestamp: Optional[datetime] = None,
    ) -> UserDeletedV1:
        """Create a USER_DELETED event"""
        data = UserDeletedDataV1()

        return UserDeletedV1(
            aggregate_id=aggregate_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            revision=revision,
            data=data,
        )

    @staticmethod
    def create_username_changed(
        aggregate_id: uuid.UUID,
        old_username: str,
        new_username: str,
        revision: int,
        timestamp: Optional[datetime] = None,
    ) -> UsernameChangedV1:
        """Create a USERNAME_CHANGED event"""
        data = UsernameChangedDataV1(
            old_username=old_username,
            new_username=new_username,
        )

        return UsernameChangedV1(
            aggregate_id=aggregate_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            revision=revision,
            data=data,
        )

    @staticmethod
    def create_password_changed(
        aggregate_id: uuid.UUID,
        password_hash: str,
        revision: int,
        timestamp: Optional[datetime] = None,
    ) -> PasswordChangedV1:
        """Create a PASSWORD_CHANGED event"""
        data = PasswordChangedDataV1(
            password_hash=password_hash,
        )

        return PasswordChangedV1(
            aggregate_id=aggregate_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            revision=revision,
            data=data,
        )

    @staticmethod
    def create_password_reset_requested(
        aggregate_id: uuid.UUID,
        revision: int,
        timestamp: Optional[datetime] = None,
    ) -> PasswordResetRequestedV1:
        """Create a PASSWORD_RESET_REQUESTED event"""
        data = PasswordResetRequestedDataV1()

        return PasswordResetRequestedV1(
            aggregate_id=aggregate_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            revision=revision,
            data=data,
        )

    @staticmethod
    def create_password_reset_completed(
        aggregate_id: uuid.UUID,
        password_hash: str,
        reset_token: str,
        revision: int,
        timestamp: Optional[datetime] = None,
    ) -> PasswordResetCompletedV1:
        """Create a PASSWORD_RESET_COMPLETED event"""
        data = PasswordResetCompletedDataV1(
            password_hash=password_hash,
            reset_token=reset_token,
        )

        return PasswordResetCompletedV1(
            aggregate_id=aggregate_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            revision=revision,
            data=data,
        )
