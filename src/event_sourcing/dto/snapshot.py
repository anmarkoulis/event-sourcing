"""Snapshot DTO package."""

from event_sourcing.infrastructure.snapshot_store.dto.base import SnapshotDTO
from event_sourcing.infrastructure.snapshot_store.dto.user import (
    UserSnapshotDTO,
)

__all__ = ["SnapshotDTO", "UserSnapshotDTO"]
