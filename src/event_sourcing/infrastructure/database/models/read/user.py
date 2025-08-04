from sqlalchemy import Column, String, Text

from event_sourcing.infrastructure.database.base import BaseModel
from event_sourcing.infrastructure.database.mixins import (
    CreatedAtMixin,
    DeletedAtMixin,
    UpdatedAtMixin,
    UUIDIdMixin,
)


class User(
    UUIDIdMixin, BaseModel, CreatedAtMixin, UpdatedAtMixin, DeletedAtMixin
):
    """Database model for user read model"""

    # User identification (id is now the aggregate_id)
    username = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)

    # User information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    password_hash = Column(Text, nullable=False)  # Hashed password
    status = Column(String(50), nullable=False, default="active")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
