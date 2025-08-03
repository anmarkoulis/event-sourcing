from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from event_sourcing.enums import EventSourceEnum, EventType
from event_sourcing.infrastructure.database.base import TimestampedModel


class EventStream(TimestampedModel):
    """Base abstract model for event streams - should not be created directly"""

    __abstract__ = True

    # Event identification
    event_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    aggregate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType), nullable=False, index=True
    )

    # Event data and metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    data = Column(JSONB, nullable=False)  # Event payload
    event_metadata = Column(JSONB, nullable=True)  # User, source, etc.
    validation_info = Column(JSONB, nullable=True)  # Validation metadata

    # Additional fields for tracking
    source: Mapped[EventSourceEnum] = mapped_column(
        SQLEnum(EventSourceEnum), nullable=False, index=True
    )
    processed_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<EventStream(id={self.event_id}, aggregate_id={self.aggregate_id}, event_type={self.event_type})>"
