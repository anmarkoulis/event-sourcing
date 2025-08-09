import uuid
from abc import ABC, abstractmethod
from typing import Dict, Tuple

from event_sourcing.dto import EventDTO


class Aggregate(ABC):
    """Base aggregate interface"""

    def __init__(self, aggregate_id: uuid.UUID):
        self.aggregate_id = aggregate_id
        # Track last applied revision for correct next revision computation
        self.last_applied_revision: int = 0

    @abstractmethod
    def apply(self, event: EventDTO) -> None:
        """Apply event to aggregate state"""

    @classmethod
    @abstractmethod
    def from_snapshot(
        cls, aggregate_id: uuid.UUID, data: Dict[str, object], revision: int
    ) -> "Aggregate":
        """Construct aggregate from snapshot data and revision."""

    @abstractmethod
    def to_snapshot(self) -> Tuple[Dict[str, object], int]:
        """Return (data, revision) for snapshot persistence."""
