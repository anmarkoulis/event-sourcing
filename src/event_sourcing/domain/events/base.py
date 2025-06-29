import uuid
from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel


class DomainEvent(BaseModel):
    """Base domain event for all business events"""

    event_id: str
    aggregate_id: str
    aggregate_type: str  # "client", "project", etc.
    event_type: str  # "Created", "Updated", "Deleted"
    timestamp: datetime
    version: str
    data: Dict[str, Any]  # Generic event data
    metadata: Dict[str, Any]  # User, source, etc.
    validation_info: Optional[Dict[str, Any]] = None  # Validation metadata

    # Class attributes for subclasses to define
    AGGREGATE_TYPE: ClassVar[Optional[str]] = None
    EVENT_TYPE: ClassVar[Optional[str]] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DomainEvent":
        """Create a new domain event"""
        if cls.AGGREGATE_TYPE is None or cls.EVENT_TYPE is None:
            raise ValueError(
                f"Class {cls.__name__} must define AGGREGATE_TYPE and EVENT_TYPE"
            )

        return cls(
            event_id=str(uuid.uuid4()),
            aggregate_id=aggregate_id,
            aggregate_type=cls.AGGREGATE_TYPE,
            event_type=cls.EVENT_TYPE,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            data=data,
            metadata=metadata or {},
            validation_info={},
        )
