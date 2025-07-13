from enum import Enum


class EventSourceEnum(str, Enum):
    """Enum for event sources"""

    SALESFORCE = "SALESFORCE"


class EventType(str, Enum):
    """Enum for event types (ALL_CAPS for DB consistency)"""

    # Domain Events
    CLIENT_CREATED = "CLIENT_CREATED"
    CLIENT_UPDATED = "CLIENT_UPDATED"
    CLIENT_DELETED = "CLIENT_DELETED"

    # Projection Events
    PROJECTION_CREATED = "PROJECTION_CREATED"
    PROJECTION_UPDATED = "PROJECTION_UPDATED"

    # Snapshot Events
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"
    SNAPSHOT_UPDATED = "SNAPSHOT_UPDATED"
    SNAPSHOT_DELETED = "SNAPSHOT_DELETED"

    # System Events
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SYSTEM_WARNING = "SYSTEM_WARNING"
