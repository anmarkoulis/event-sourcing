import uuid
from datetime import datetime, timezone
from typing import Optional, TypeVar

from event_sourcing.dto.events.base import EventDTO
from event_sourcing.dto.events.user import (
    PasswordChangedDataV1,
    PasswordChangedV1,
    UserCreatedDataV1,
    UserCreatedV1,
    UserDeletedDataV1,
    UserDeletedV1,
    UserUpdatedDataV1,
    UserUpdatedV1,
)
from event_sourcing.enums import Role
from event_sourcing.infrastructure.enums import HashingMethod

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
        hashing_method: HashingMethod,
        role: Role = Role.USER,
        revision: int = 1,
        timestamp: Optional[datetime] = None,
    ) -> UserCreatedV1:
        """Create a USER_CREATED event"""
        data = UserCreatedDataV1(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            hashing_method=hashing_method,
            role=role,
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

    # Username change removed in simplified model

    @staticmethod
    def create_password_changed(
        aggregate_id: uuid.UUID,
        password_hash: str,
        hashing_method: HashingMethod,
        revision: int,
        timestamp: Optional[datetime] = None,
    ) -> PasswordChangedV1:
        """Create a PASSWORD_CHANGED event"""
        data = PasswordChangedDataV1(
            password_hash=password_hash,
            hashing_method=hashing_method,
        )

        return PasswordChangedV1(
            aggregate_id=aggregate_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            revision=revision,
            data=data,
        )

    # Password reset request removed in simplified model

    # Password reset completion removed in simplified model
