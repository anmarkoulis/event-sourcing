import logging
from typing import List

from event_sourcing.application.queries.handlers.base import QueryHandler
from event_sourcing.application.queries.user import GetUserHistoryQuery
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class GetUserHistoryQueryHandler(
    QueryHandler[GetUserHistoryQuery, List[EventDTO]]
):
    """Handler for getting user event history"""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def handle(self, query: GetUserHistoryQuery) -> List[EventDTO]:
        """Handle get user history query"""
        try:
            events: List[EventDTO] = await self.event_store.get_stream(
                query.user_id,
                start_time=query.start_time,
                end_time=query.end_time,
            )
            return events
        except Exception as e:
            logger.error(f"Error getting user history {query.user_id}: {e}")
            return []
