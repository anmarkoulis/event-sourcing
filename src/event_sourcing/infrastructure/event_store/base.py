import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from event_sourcing.dto.event import EventDTO

logger = logging.getLogger(__name__)


class EventStore(ABC):
    """Abstract event store interface"""

    @abstractmethod
    async def get_stream(
        self,
        aggregate_id: uuid.UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventDTO]:
        """Get events for an aggregate in chronological order with optional time filtering"""

    @abstractmethod
    async def append_to_stream(
        self, aggregate_id: uuid.UUID, events: List[EventDTO]
    ) -> None:
        """Append events to the stream for an aggregate"""
