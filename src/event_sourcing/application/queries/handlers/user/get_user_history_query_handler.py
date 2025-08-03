import logging
from typing import Any, Dict, List

from event_sourcing.application.queries.user import GetUserHistoryQuery
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class GetUserHistoryQueryHandler:
    """Handler for getting user event history"""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def handle(self, query: GetUserHistoryQuery) -> List[Dict[str, Any]]:
        """Handle get user history query"""
        try:
            events = await self.event_store.get_stream(
                query.user_id, from_date=query.from_date, to_date=query.to_date
            )

            # Convert events to dictionaries for API response
            event_list = []
            for event in events:
                event_list.append(
                    {
                        "event_id": str(event.event_id),
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "data": event.data,
                        "metadata": event.metadata,
                    }
                )

            return event_list
        except Exception as e:
            logger.error(f"Error getting user history {query.user_id}: {e}")
            return []
