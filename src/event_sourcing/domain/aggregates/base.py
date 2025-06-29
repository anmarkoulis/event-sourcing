from abc import ABC, abstractmethod

from event_sourcing.domain.events.base import DomainEvent


class BaseAggregate(ABC):
    """Base aggregate - pure business logic only"""

    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id

    @abstractmethod
    def apply(self, event: DomainEvent) -> None:
        """Apply a domain event to the aggregate state"""
