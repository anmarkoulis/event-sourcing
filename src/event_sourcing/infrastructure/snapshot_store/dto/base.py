"""Base snapshot DTO carrying serialized state and revision."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import Field

from event_sourcing.domain.aggregates.base import Aggregate
from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.enums import AggregateTypeEnum

T_Agg = TypeVar("T_Agg", bound=Aggregate)


class SnapshotDTO(ModelConfigBaseModel, Generic[T_Agg]):
    """Base snapshot DTO carrying serialized state and revision."""

    aggregate_id: uuid.UUID
    aggregate_type: AggregateTypeEnum
    data: dict[str, Any]
    revision: int = Field(ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None
