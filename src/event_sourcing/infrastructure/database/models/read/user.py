from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from event_sourcing.enums import Role
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
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # User information
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[Role] = mapped_column(
        Enum(Role), nullable=False, default=Role.USER
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
