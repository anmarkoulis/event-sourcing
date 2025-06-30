import logging
from typing import List

from event_sourcing.application.queries.base import GetClientHistoryQuery
from event_sourcing.domain.events.base import DomainEvent
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class GetClientHistoryQueryHandler:
    """Handler for getting client event history"""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def handle(self, query: GetClientHistoryQuery) -> List[DomainEvent]:
        """Handle get client history query"""
        logger.info(f"Getting client history: {query.client_id}")

        # Get events from event store
        events: List[DomainEvent] = await self.event_store.get_events(
            aggregate_id=query.client_id,
            aggregate_type="client",
        )

        # Filter by date range if specified
        if query.from_date or query.to_date:
            filtered_events: List[DomainEvent] = []
            for event in events:
                # Include event if it's within the date range
                if query.from_date and event.timestamp < query.from_date:
                    continue
                if query.to_date and event.timestamp > query.to_date:
                    continue
                filtered_events.append(event)
            events = filtered_events

        logger.info(
            f"Found {len(events)} events for client: {query.client_id}"
        )
        return events
