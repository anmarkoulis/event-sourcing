from sqlalchemy import Column, Index, String

from event_sourcing.infrastructure.database.base import BaseModel


class Client(BaseModel):
    """Database model for client read model (denormalized data)"""

    # Client identification
    aggregate_id = Column(String(255), unique=True, nullable=False, index=True)

    # Basic client information
    name = Column(String(500), nullable=True, index=True)
    parent_id = Column(String(255), nullable=True, index=True)
    status = Column(String(100), nullable=True, index=True)

    # Timestamps (inherited from BaseModel)
    # created_at and updated_at are already included via BaseModel

    # Indexes for efficient querying
    __table_args__ = (
        # Composite index for status queries
        Index("idx_client_status", "status"),
        # Index for parent-child relationships
        Index("idx_client_parent", "parent_id"),
        # Index for name searches
        Index("idx_client_name", "name"),
    )

    def __repr__(self):
        return f"<Client(aggregate_id={self.aggregate_id}, name={self.name}, status={self.status})>"
