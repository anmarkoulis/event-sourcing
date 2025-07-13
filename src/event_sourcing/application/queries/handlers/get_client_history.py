import logging
from typing import List

from event_sourcing.application.queries.client import GetClientHistoryQuery
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class GetClientHistoryQueryHandler:
    """Handler for getting client event history"""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def handle(self, query: GetClientHistoryQuery) -> List[EventDTO]:
        """Handle get client history query"""
        logger.info(f"Getting history for client: {query.client_id}")

        # Get events from event store
        events: List[EventDTO] = await self.event_store.get_events(
            query.client_id, "client"
        )

        # Filter events if needed
        filtered_events: List[EventDTO] = []

        for event in events:
            # Add any filtering logic here if needed
            filtered_events.append(event)

        logger.info(
            f"Retrieved {len(filtered_events)} events for client {query.client_id}"
        )
        return filtered_events
