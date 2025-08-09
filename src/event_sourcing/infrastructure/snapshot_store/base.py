import uuid
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from event_sourcing.domain.aggregates.base import Aggregate
from event_sourcing.dto.snapshot import SnapshotDTO
from event_sourcing.enums import AggregateTypeEnum

T_Agg = TypeVar("T_Agg", bound=Aggregate)


class SnapshotStore(ABC, Generic[T_Agg]):
    """Abstract snapshot store.

    Implementations can use any backend (e.g., Postgres, Redis)."""

    @abstractmethod
    async def get(
        self, aggregate_id: uuid.UUID, aggregate_type: AggregateTypeEnum
    ) -> Optional[SnapshotDTO[T_Agg]]:
        """Return the latest snapshot DTO for the aggregate, if present."""

    @abstractmethod
    async def set(self, dto: SnapshotDTO[T_Agg]) -> None:
        """Store or update the snapshot using a DTO."""
