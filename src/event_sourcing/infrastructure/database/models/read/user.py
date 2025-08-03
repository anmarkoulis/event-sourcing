from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from event_sourcing.infrastructure.database.base import TimestampedModel


class User(TimestampedModel):
    """Database model for user read model"""

    # User identification
    aggregate_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    username = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)

    # User information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    password_hash = Column(Text, nullable=False)  # Hashed password
    status = Column(String(50), nullable=False, default="active")

    # Additional timestamps
    created_at_user = Column(DateTime(timezone=True), nullable=False)
    updated_at_user = Column(DateTime(timezone=True), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User(aggregate_id={self.aggregate_id}, username={self.username}, email={self.email})>"
