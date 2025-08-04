from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from event_sourcing.enums import EventType
from event_sourcing.infrastructure.database.base import BaseModel
from event_sourcing.infrastructure.database.mixins import (
    CreatedAtMixin,
    UpdatedAtMixin,
    UUIDIdMixin,
)


class EventStream(BaseModel, UUIDIdMixin, CreatedAtMixin, UpdatedAtMixin):
    """Base abstract model for event streams - should not be created directly"""

    __abstract__ = True

    # Event identification
    event_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    # Note: aggregate_id is now the same as the model's id field
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType), nullable=False, index=True
    )

    # Event data and metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    version = Column(String(50), nullable=False)  # Schema version
    revision = Column(Integer, nullable=False, index=True)  # Sequence number
    data = Column(JSONB, nullable=False)  # Event payload

    # Unique constraint to ensure event ordering consistency
    __table_args__ = (
        UniqueConstraint(
            "id", "revision", name="uq_event_stream_aggregate_revision"
        ),
    )

    def __repr__(self) -> str:
        return f"<EventStream(id={self.id}, event_id={self.event_id}, event_type={self.event_type})>"
