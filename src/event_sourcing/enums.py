from enum import Enum


class EventType(str, Enum):
    """Enum for event types (ALL_CAPS for DB consistency)"""

    # Domain Events
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    PASSWORD_CHANGED = (
        "PASSWORD_CHANGED"  # pragma: allowlist secret # noqa: S105
    )
    # Removed USERNAME_CHANGED, PASSWORD_RESET_* in simplified model


class AggregateTypeEnum(str, Enum):
    """Enum for aggregate types"""

    USER = "User"
