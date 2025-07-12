from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID

from event_sourcing.enums import EventSourceEnum
from event_sourcing.infrastructure.database.base import BaseModel


class Event(BaseModel):
    """Database model for storing domain events"""

    # Event identification
    event_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    aggregate_id = Column(String(255), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)

    # Event data and metadata
    timestamp = Column(DateTime, nullable=False, index=True)
    version = Column(String(50), nullable=False)
    data = Column(JSONB, nullable=False)  # Event payload
    event_metadata = Column(JSONB, nullable=True)  # User, source, etc.
    validation_info = Column(JSONB, nullable=True)  # Validation metadata

    # Additional fields for tracking
    source: EventSourceEnum = Column(
        SQLEnum(EventSourceEnum), nullable=False, index=True
    )  # "salesforce", "backfill", etc.
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes for efficient querying
    __table_args__ = (
        # Composite index for aggregate queries
        Index(
            "idx_aggregate_events",
            "aggregate_id",
            "aggregate_type",
            "timestamp",
        ),
        # Index for time-based queries
        Index("idx_event_timestamp", "timestamp"),
        # Index for event type queries
        Index("idx_event_type", "event_type"),
        # Index for source queries
        Index("idx_event_source", "source"),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.event_id}, aggregate_id={self.aggregate_id}, event_type={self.event_type})>"
