"""User-specific snapshot DTO."""

from pydantic import Field

from event_sourcing.enums import AggregateTypeEnum

from .base import SnapshotDTO


class UserSnapshotDTO(SnapshotDTO):
    """User-specific snapshot DTO (kept for clarity/typing)."""

    aggregate_type: AggregateTypeEnum = Field(default=AggregateTypeEnum.USER)
