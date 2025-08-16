import logging
import uuid
from datetime import datetime
from typing import List, Optional

from event_sourcing.domain.aggregates.base import Aggregate
from event_sourcing.dto import EventDTO, EventFactory
from event_sourcing.enums import EventType, HashingMethod, Role

logger = logging.getLogger(__name__)


class UserAggregate(Aggregate):
    """User domain aggregate - encapsulates user business logic"""

    last_applied_revision: int

    def __init__(self, aggregate_id: uuid.UUID):
        super().__init__(aggregate_id)

        # Track events for business logic validation
        self.events: List[EventDTO] = []
        # Ensure mypy sees this attribute on this class
        self.last_applied_revision: int = 0

        # User-specific attributes
        self.username: Optional[str] = None
        self.email: Optional[str] = None
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.password_hash: Optional[str] = None
        self.hashing_method: Optional[HashingMethod] = None
        self.role: Optional[Role] = None
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        self.deleted_at: Optional[datetime] = None

    def _get_next_revision(self) -> int:
        """Get the next revision number for this aggregate"""
        return self.last_applied_revision + 1

    def exists(self) -> bool:
        """Check if the user aggregate exists (has been created)."""
        return self.username is not None

    def create_user(
        self,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        password_hash: str,
        hashing_method: HashingMethod,
        role: Role = Role.USER,
    ) -> List[EventDTO]:
        """Create a new user"""
        # Business rule: Cannot create user if already exists
        logger.info(f"Creating user: {username}")
        logger.info(f"User: {self.username}")
        if self.username is not None:
            logger.info(f"User already exists: {self.username}")
            from event_sourcing.domain.exceptions import UserAlreadyExists

            raise UserAlreadyExists(username)

        # Business rule: Username must be unique (in real app, check against DB)
        if not username or len(username) < 3:
            logger.info(f"Username must be at least 3 characters: {username}")
            from event_sourcing.domain.exceptions import UsernameTooShort

            raise UsernameTooShort(username)

        # Business rule: Email must be valid format
        if not email or "@" not in email:
            logger.info(f"Invalid email format: {email}")
            from event_sourcing.domain.exceptions import InvalidEmailFormat

            raise InvalidEmailFormat(email)

        # Business rule: Password must be provided
        if not password_hash:
            logger.info(f"Password is required: {password_hash}")
            from event_sourcing.domain.exceptions import PasswordRequired

            raise PasswordRequired()

        # Create the event
        logger.info(f"Creating USER_CREATED event for user: {username}")
        event = EventFactory.create_user_created(
            aggregate_id=self.aggregate_id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            hashing_method=hashing_method,
            role=role,
            revision=self._get_next_revision(),
        )
        logger.info(f"Event: {event}")
        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Created user: {username}")
        return [event]

    def update_user(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[EventDTO]:
        """Update user information"""
        # Business rule: User must exist to be updated
        if not self.exists():
            from event_sourcing.domain.exceptions import UserNotFound

            raise UserNotFound(f"User {self.aggregate_id} not found")

        # Business rule: Cannot update deleted user
        if self.deleted_at is not None:
            from event_sourcing.domain.exceptions import (
                CannotUpdateDeletedUser,
            )

            raise CannotUpdateDeletedUser(str(self.aggregate_id))

        # Business rule: Must provide at least one field to update
        if not any([first_name, last_name, email]):
            from event_sourcing.domain.exceptions import NoFieldsToUpdate

            raise NoFieldsToUpdate()

        # Business rule: Email must be valid if provided
        if email and "@" not in email:
            from event_sourcing.domain.exceptions import InvalidEmailFormat

            raise InvalidEmailFormat(email)

        # Create the event
        event = EventFactory.create_user_updated(
            aggregate_id=self.aggregate_id,
            revision=self._get_next_revision(),
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Updated user: {self.username}")
        return [event]

    # Removed: change_username (username is immutable in this simplified model)

    def change_password(
        self, new_password_hash: str, hashing_method: HashingMethod
    ) -> List[EventDTO]:
        """Change user's password"""
        # Business rule: User must exist to change password
        if not self.exists():
            from event_sourcing.domain.exceptions import UserNotFound

            raise UserNotFound(f"User {self.aggregate_id} not found")

        # Business rule: Cannot change password if user is deleted
        if self.deleted_at is not None:
            from event_sourcing.domain.exceptions import (
                CannotChangePasswordForDeletedUser,
            )

            raise CannotChangePasswordForDeletedUser(str(self.aggregate_id))

        # Business rule: New password must be provided
        if not new_password_hash:
            from event_sourcing.domain.exceptions import NewPasswordRequired

            raise NewPasswordRequired()

        # Business rule: New password must be different from current password
        if new_password_hash == self.password_hash:
            from event_sourcing.domain.exceptions import (
                PasswordMustBeDifferent,
            )

            raise PasswordMustBeDifferent()

        # Create the event
        event = EventFactory.create_password_changed(
            aggregate_id=self.aggregate_id,
            password_hash=new_password_hash,
            hashing_method=hashing_method,
            revision=self._get_next_revision(),
        )

        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Changed password for user: {self.username}")
        return [event]

    # Removed: request_password_reset

    # Removed: complete_password_reset

    def delete_user(self) -> List[EventDTO]:
        """Delete user"""
        # Business rule: User must exist to be deleted
        if not self.exists():
            from event_sourcing.domain.exceptions import UserNotFound

            raise UserNotFound(f"User {self.aggregate_id} not found")

        # Business rule: Cannot delete already deleted user
        if self.deleted_at is not None:
            from event_sourcing.domain.exceptions import UserAlreadyDeleted

            raise UserAlreadyDeleted(str(self.aggregate_id))

        # Create the event
        event = EventFactory.create_user_deleted(
            aggregate_id=self.aggregate_id,
            revision=self._get_next_revision(),
        )

        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Deleted user: {self.username}")
        return [event]

    def apply(self, event: EventDTO) -> None:
        """Apply a domain event to the user aggregate state"""
        logger.info(f"Applying event: {event}")
        # Track the event for business logic validation
        self.events.append(event)
        # Maintain last applied revision
        if event.revision is not None:
            self.last_applied_revision = max(
                self.last_applied_revision, int(event.revision)
            )

        if event.event_type == EventType.USER_CREATED:
            self._apply_created_event(event)
        elif event.event_type == EventType.USER_UPDATED:
            self._apply_updated_event(event)
        elif event.event_type == EventType.PASSWORD_CHANGED:
            self._apply_password_changed_event(event)
        elif event.event_type == EventType.USER_DELETED:
            self._apply_deleted_event(event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")

    def _apply_created_event(self, event: EventDTO) -> None:
        """Apply user created event"""
        data = event.data
        self.username = data.username
        self.email = data.email
        self.first_name = data.first_name
        self.last_name = data.last_name
        self.password_hash = data.password_hash
        self.hashing_method = data.hashing_method
        self.role = data.role
        self.created_at = event.timestamp
        self.updated_at = event.timestamp

    def _apply_updated_event(self, event: EventDTO) -> None:
        """Apply user updated event"""
        data = event.data
        # Update only provided fields
        if data.first_name is not None:
            self.first_name = data.first_name
        if data.last_name is not None:
            self.last_name = data.last_name
        if data.email is not None:
            self.email = data.email
        self.updated_at = event.timestamp

    # Removed: _apply_username_changed_event

    def _apply_password_changed_event(self, event: EventDTO) -> None:
        """Apply password changed event"""
        data = event.data
        self.password_hash = data.password_hash
        self.hashing_method = data.hashing_method
        self.updated_at = event.timestamp

    # Removed: _apply_password_reset_requested_event

    # Removed: _apply_password_reset_completed_event

    def _apply_deleted_event(self, event: EventDTO) -> None:
        """Apply user deleted event"""
        self.deleted_at = event.timestamp
        self.updated_at = event.timestamp

    @classmethod
    def from_snapshot(
        cls, aggregate_id: uuid.UUID, data: dict, revision: int
    ) -> "UserAggregate":
        user = cls(aggregate_id)
        user.username = data.get("username")
        user.email = data.get("email")
        user.first_name = data.get("first_name")
        user.last_name = data.get("last_name")
        user.password_hash = data.get("password_hash")
        user.hashing_method = data.get("hashing_method")
        user.role = data.get("role")
        user.created_at = cls._parse_iso_datetime(data.get("created_at"))
        user.updated_at = cls._parse_iso_datetime(data.get("updated_at"))
        user.deleted_at = cls._parse_iso_datetime(data.get("deleted_at"))
        user.last_applied_revision = int(revision)
        return user

    def to_snapshot(self) -> tuple[dict, int]:
        data = {
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "password_hash": self.password_hash,
            "hashing_method": self.hashing_method,
            "role": self.role,
            "created_at": self._iso_datetime(self.created_at),
            "updated_at": self._iso_datetime(self.updated_at),
            "deleted_at": self._iso_datetime(self.deleted_at),
        }
        return data, int(self.last_applied_revision)

    @staticmethod
    def _iso_datetime(value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO 8601 string for JSONB storage."""
        if value is None:
            return None
        return value.isoformat()

    @staticmethod
    def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 string back to datetime."""
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
