import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar

from event_sourcing.domain.aggregates.base import Aggregate
from event_sourcing.enums import AggregateTypeEnum

A_co = TypeVar("A_co", bound=Aggregate, covariant=True)


@dataclass(frozen=True)
class SnapshotDTO(Generic[A_co]):
    """Transport object for snapshots.

    Carries serialized aggregate state and the last applied revision.
    """

    aggregate_id: uuid.UUID
    aggregate_type: AggregateTypeEnum
    data: dict[str, Any]
    revision: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
