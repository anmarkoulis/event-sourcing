from typing import Any, ClassVar, Dict, Optional, cast

from .base import DomainEvent


class ClientCreatedEvent(DomainEvent):
    """Client created event"""

    AGGREGATE_TYPE: ClassVar[str] = "client"
    EVENT_TYPE: ClassVar[str] = "Created"

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ClientCreatedEvent":
        """Create a client created event"""
        return cast(
            "ClientCreatedEvent",
            super().create(
                aggregate_id=aggregate_id, data=data, metadata=metadata
            ),
        )


class ClientUpdatedEvent(DomainEvent):
    """Client updated event"""

    AGGREGATE_TYPE: ClassVar[str] = "client"
    EVENT_TYPE: ClassVar[str] = "Updated"

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ClientUpdatedEvent":
        """Create a client updated event"""
        return cast(
            "ClientUpdatedEvent",
            super().create(
                aggregate_id=aggregate_id, data=data, metadata=metadata
            ),
        )


class ClientDeletedEvent(DomainEvent):
    """Client deleted event"""

    AGGREGATE_TYPE: ClassVar[str] = "client"
    EVENT_TYPE: ClassVar[str] = "Deleted"

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ClientDeletedEvent":
        """Create a client deleted event"""
        return cast(
            "ClientDeletedEvent",
            super().create(
                aggregate_id=aggregate_id, data=data, metadata=metadata
            ),
        )
