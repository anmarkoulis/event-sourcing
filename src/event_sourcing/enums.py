from enum import Enum


class EventType(str, Enum):
    """Enum for event types (ALL_CAPS for DB consistency)"""

    # Domain Events
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USERNAME_CHANGED = "USERNAME_CHANGED"
    PASSWORD_CHANGED = (
        "PASSWORD_CHANGED"  # pragma: allowlist secret # noqa: S105
    )
    PASSWORD_RESET_REQUESTED = (
        "PASSWORD_RESET_REQUESTED"  # pragma: allowlist secret # noqa: S105
    )
    PASSWORD_RESET_COMPLETED = (
        "PASSWORD_RESET_COMPLETED"  # pragma: allowlist secret # noqa: S105
    )


class AggregateTypeEnum(str, Enum):
    """Enum for aggregate types"""

    USER = "User"
