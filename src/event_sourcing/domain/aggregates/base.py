from abc import ABC, abstractmethod

from event_sourcing.dto.event import EventDTO


class Aggregate(ABC):
    """Base aggregate interface"""

    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id

    @abstractmethod
    def apply(self, event: EventDTO) -> None:
        """Apply event to aggregate state"""
