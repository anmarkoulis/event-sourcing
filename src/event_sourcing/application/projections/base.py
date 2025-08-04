from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from event_sourcing.dto import EventDTO

# Type variable for projections
ProjectionType = TypeVar("ProjectionType")


class Projection(ABC, Generic[ProjectionType]):
    """Base interface for projections"""

    @abstractmethod
    async def handle(self, event: EventDTO) -> None:
        """Handle an event"""
