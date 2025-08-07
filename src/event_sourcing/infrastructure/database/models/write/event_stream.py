from typing import Any, Type

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
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

    # Aggregate identification
    aggregate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # Event type
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType), nullable=False
    )

    # Event data and metadata
    timestamp = Column(DateTime(timezone=True), nullable=False)
    version = Column(String(50), nullable=False)  # Schema version
    revision = Column(Integer, nullable=False)  # Sequence number
    data = Column(JSONB, nullable=False)  # Event payload

    def __init_subclass__(cls: Type["EventStream"], **kwargs: Any) -> None:
        """Set up unique constraint name for each subclass"""
        super().__init_subclass__(**kwargs)

        # Create unique constraint name based on table name
        table_name = cls.__tablename__
        constraint_name = f"uq_{table_name}_aggregate_revision"

        # Add composite index for aggregate_id + timestamp queries
        index_name = f"idx_{table_name}_aggregate_timestamp"

        cls.__table_args__ = (
            UniqueConstraint("aggregate_id", "revision", name=constraint_name),
            Index(index_name, "aggregate_id", "timestamp"),
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, aggregate_id={self.aggregate_id}, event_type={self.event_type})>"
