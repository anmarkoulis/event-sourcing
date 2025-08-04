import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from event_sourcing.dto import EventDTO
from event_sourcing.enums import AggregateTypeEnum

logger = logging.getLogger(__name__)


class EventStore(ABC):
    """Abstract event store interface"""

    @abstractmethod
    async def get_stream(
        self,
        aggregate_id: uuid.UUID,
        aggregate_type: AggregateTypeEnum,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventDTO]:
        """Get events for an aggregate in chronological order with optional time filtering"""

    @abstractmethod
    async def append_to_stream(
        self,
        aggregate_id: uuid.UUID,
        aggregate_type: AggregateTypeEnum,
        events: List[EventDTO],
    ) -> None:
        """Append events to the stream for an aggregate"""

    @abstractmethod
    async def search_events(
        self,
        aggregate_type: AggregateTypeEnum,
        query_params: dict,
    ) -> List[EventDTO]:
        """Search events by aggregate type and query parameters"""
