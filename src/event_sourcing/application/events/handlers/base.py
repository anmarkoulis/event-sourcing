from abc import ABC, abstractmethod
from typing import List

from event_sourcing.dto.event import EventDTO


class EventHandler(ABC):
    """Base interface for event handlers"""

    @abstractmethod
    async def dispatch(self, events: List[EventDTO]) -> None:
        """Dispatch events to appropriate handlers"""
