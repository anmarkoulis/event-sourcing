import logging
import uuid
from datetime import datetime
from typing import List, Optional

from event_sourcing.domain.aggregates.base import Aggregate
from event_sourcing.dto.event import EventDTO
from event_sourcing.enums import EventSourceEnum, EventType

logger = logging.getLogger(__name__)


class UserAggregate(Aggregate):
    """User domain aggregate - encapsulates user business logic"""

    def __init__(self, aggregate_id: uuid.UUID):
        super().__init__(aggregate_id)

        # Track events for business logic validation
        self.events: List[EventDTO] = []

        # User-specific attributes
        self.username: Optional[str] = None
        self.email: Optional[str] = None
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.password_hash: Optional[str] = None
        self.status: Optional[str] = None
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        self.deleted_at: Optional[datetime] = None

    def create_user(
        self,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        password_hash: str,
    ) -> List[EventDTO]:
        """Create a new user"""
        # Business rule: Cannot create user if already exists
        logger.info(f"Creating user: {username}")
        logger.info(f"User: {self.username}")
        if self.username is not None:
            logger.info(f"User already exists: {self.username}")
            raise ValueError("User already exists")

        # Business rule: Username must be unique (in real app, check against DB)
        if not username or len(username) < 3:
            logger.info(f"Username must be at least 3 characters: {username}")
            raise ValueError("Username must be at least 3 characters")

        # Business rule: Email must be valid format
        if not email or "@" not in email:
            logger.info(f"Invalid email format: {email}")
            raise ValueError("Invalid email format")

        # Business rule: Password must be provided
        if not password_hash:
            logger.info(f"Password is required: {password_hash}")
            raise ValueError("Password is required")

        # Create the event
        logger.info(f"Creating USER_CREATED event for user: {username}")
        event = EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=self.aggregate_id,
            event_type=EventType.USER_CREATED,
            timestamp=datetime.utcnow(),
            version="1",
            data={
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "password_hash": password_hash,
                "status": "active",
            },
            event_metadata={},
            source=EventSourceEnum.API,
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
        # Business rule: Cannot update deleted user
        if self.deleted_at is not None:
            raise ValueError("Cannot update deleted user")

        # Business rule: Must provide at least one field to update
        if not any([first_name, last_name, email]):
            raise ValueError("Must provide at least one field to update")

        # Business rule: Email must be valid if provided
        if email and "@" not in email:
            raise ValueError("Invalid email format")

        # Create the event
        event = EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=self.aggregate_id,
            event_type=EventType.USER_UPDATED,
            timestamp=datetime.utcnow(),
            version="1",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
            },
            event_metadata={},
            source=EventSourceEnum.API,
        )

        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Updated user: {self.username}")
        return [event]

    def change_username(self, new_username: str) -> List[EventDTO]:
        """Change user's username"""
        # Business rule: Cannot change username if user is deleted
        if self.deleted_at is not None:
            raise ValueError("Cannot change username for deleted user")

        # Business rule: Username must be different
        if new_username == self.username:
            raise ValueError(
                "New username must be different from current username"
            )

        # Business rule: Username must be valid
        if not new_username or len(new_username) < 3:
            raise ValueError("Username must be at least 3 characters")

        # Create the event
        event = EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=self.aggregate_id,
            event_type=EventType.USERNAME_CHANGED,
            timestamp=datetime.utcnow(),
            version="1",
            data={"old_username": self.username, "new_username": new_username},
            event_metadata={},
            source=EventSourceEnum.API,
        )

        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Changed username from {self.username} to {new_username}")
        return [event]

    def change_password(self, new_password_hash: str) -> List[EventDTO]:
        """Change user's password"""
        # Business rule: Cannot change password if user is deleted
        if self.deleted_at is not None:
            raise ValueError("Cannot change password for deleted user")

        # Business rule: Password must be provided
        if not new_password_hash:
            raise ValueError("Password is required")

        # Create the event
        event = EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=self.aggregate_id,
            event_type=EventType.PASSWORD_CHANGED,
            timestamp=datetime.utcnow(),
            version="1",
            data={"new_password_hash": new_password_hash},
            event_metadata={},
            source=EventSourceEnum.API,
        )

        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Changed password for user: {self.username}")
        return [event]

    def request_password_reset(self) -> List[EventDTO]:
        """Request password reset"""
        # Business rule: Cannot request reset if user is deleted
        if self.deleted_at is not None:
            raise ValueError("Cannot request password reset for deleted user")

        # Create the event
        event = EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=self.aggregate_id,
            event_type=EventType.PASSWORD_RESET_REQUESTED,
            timestamp=datetime.utcnow(),
            version="1",
            data={
                "email": self.email,
                "reset_token": str(
                    uuid.uuid4()
                ),  # In real app, generate secure token
            },
            event_metadata={},
            source=EventSourceEnum.API,
        )

        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Requested password reset for user: {self.username}")
        return [event]

    def complete_password_reset(
        self, new_password_hash: str, reset_token: str
    ) -> List[EventDTO]:
        """Complete password reset"""
        # Business rule: Cannot reset if user is deleted
        if self.deleted_at is not None:
            raise ValueError("Cannot reset password for deleted user")

        # Business rule: Password must be provided
        if not new_password_hash:
            raise ValueError("Password is required")

        # Business rule: Reset token must be provided
        if not reset_token:
            raise ValueError("Reset token is required")

        # Create the event
        event = EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=self.aggregate_id,
            event_type=EventType.PASSWORD_RESET_COMPLETED,
            timestamp=datetime.utcnow(),
            version="1",
            data={
                "new_password_hash": new_password_hash,
                "reset_token": reset_token,
            },
            event_metadata={},
            source=EventSourceEnum.API,
        )

        # Apply the event to the aggregate
        self.apply(event)

        logger.info(f"Completed password reset for user: {self.username}")
        return [event]

    def delete_user(self) -> List[EventDTO]:
        """Delete user"""
        # Business rule: Cannot delete already deleted user
        if self.deleted_at is not None:
            raise ValueError("User is already deleted")

        # Create the event
        event = EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=self.aggregate_id,
            event_type=EventType.USER_DELETED,
            timestamp=datetime.utcnow(),
            version="1",
            data={
                "deleted_by": "system",  # In real app, get from auth context
                "reason": "User requested deletion",
            },
            event_metadata={},
            source=EventSourceEnum.API,
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

        if event.event_type == EventType.USER_CREATED:
            self._apply_created_event(event)
        elif event.event_type == EventType.USER_UPDATED:
            self._apply_updated_event(event)
        elif event.event_type == EventType.USERNAME_CHANGED:
            self._apply_username_changed_event(event)
        elif event.event_type == EventType.PASSWORD_CHANGED:
            self._apply_password_changed_event(event)
        elif event.event_type == EventType.PASSWORD_RESET_REQUESTED:
            self._apply_password_reset_requested_event(event)
        elif event.event_type == EventType.PASSWORD_RESET_COMPLETED:
            self._apply_password_reset_completed_event(event)
        elif event.event_type == EventType.USER_DELETED:
            self._apply_deleted_event(event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")

    def _apply_created_event(self, event: EventDTO) -> None:
        """Apply user created event"""
        data = event.data
        self.username = data.get("username")
        self.email = data.get("email")
        self.first_name = data.get("first_name")
        self.last_name = data.get("last_name")
        self.password_hash = data.get("password_hash")
        self.status = data.get("status")
        self.created_at = event.timestamp
        self.updated_at = event.timestamp

    def _apply_updated_event(self, event: EventDTO) -> None:
        """Apply user updated event"""
        data = event.data
        # Update only provided fields
        if "first_name" in data:
            self.first_name = data["first_name"]
        if "last_name" in data:
            self.last_name = data["last_name"]
        if "email" in data:
            self.email = data["email"]
        self.updated_at = event.timestamp

    def _apply_username_changed_event(self, event: EventDTO) -> None:
        """Apply username changed event"""
        data = event.data
        self.username = data.get("new_username")
        self.updated_at = event.timestamp

    def _apply_password_changed_event(self, event: EventDTO) -> None:
        """Apply password changed event"""
        data = event.data
        self.password_hash = data.get("new_password_hash")
        self.updated_at = event.timestamp

    def _apply_password_reset_requested_event(self, event: EventDTO) -> None:
        """Apply password reset requested event"""
        # In real app, you might store the reset token temporarily
        self.updated_at = event.timestamp

    def _apply_password_reset_completed_event(self, event: EventDTO) -> None:
        """Apply password reset completed event"""
        data = event.data
        self.password_hash = data.get("new_password_hash")
        self.updated_at = event.timestamp

    def _apply_deleted_event(self, event: EventDTO) -> None:
        """Apply user deleted event"""
        self.deleted_at = event.timestamp
        self.status = "deleted"
        self.updated_at = event.timestamp
