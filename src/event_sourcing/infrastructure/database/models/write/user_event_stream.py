from sqlalchemy import Index

from event_sourcing.infrastructure.database.models.write.event_stream import (
    EventStream,
)


class UserEventStream(EventStream):
    """Concrete implementation of EventStream for User aggregate events"""

    __tablename__ = "user_event_stream"

    # Indexes for efficient querying
    __table_args__ = (
        # Composite index for aggregate queries
        Index(
            "idx_user_event_stream_aggregate_events",
            "aggregate_id",
            "timestamp",
        ),
        # Index for time-based queries
        Index("idx_user_event_stream_timestamp", "timestamp"),
        # Index for event type queries
        Index("idx_user_event_stream_event_type", "event_type"),
        # Index for source queries
        Index("idx_user_event_stream_source", "source"),
    )

    def __repr__(self) -> str:
        return f"<UserEventStream(id={self.event_id}, aggregate_id={self.aggregate_id}, event_type={self.event_type})>"
