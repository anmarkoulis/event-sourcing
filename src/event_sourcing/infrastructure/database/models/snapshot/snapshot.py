from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import JSONB

from event_sourcing.infrastructure.database.base import BaseModel
from event_sourcing.infrastructure.database.mixins import (
    CreatedAtMixin,
    UpdatedAtMixin,
    UUIDIdMixin,
)


class Snapshot(BaseModel, UUIDIdMixin, CreatedAtMixin, UpdatedAtMixin):
    """Abstract base snapshot table with id, revision, and data."""

    __abstract__ = True

    revision = Column(Integer, nullable=False)
    data = Column(JSONB, nullable=False)
