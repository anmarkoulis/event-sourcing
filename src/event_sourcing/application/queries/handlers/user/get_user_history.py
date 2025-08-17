import logging
from typing import List, Optional

from event_sourcing.application.queries.handlers.base import QueryHandler
from event_sourcing.application.queries.user import GetUserHistoryQuery
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.dto import EventDTO
from event_sourcing.dto.user import UserDTO
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class GetUserHistoryQueryHandler(
    QueryHandler[GetUserHistoryQuery, Optional[UserDTO]]
):
    """Handler for getting user state at a specific point in time"""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def handle(self, query: GetUserHistoryQuery) -> Optional[UserDTO]:
        """Handle get user state at specific time query"""
        try:
            # Get events up to the specified timestamp
            events: List[EventDTO] = await self.event_store.get_stream(
                query.user_id,
                AggregateTypeEnum.USER,
                end_time=query.timestamp,
            )

            if not events:
                logger.debug(
                    f"No events found for user {query.user_id} up to {query.timestamp}"
                )
                return None

            # Reconstruct the user aggregate from events
            user_aggregate = UserAggregate(query.user_id)
            for event in events:
                user_aggregate.apply(event)

            # Convert aggregate state to UserDTO
            user_dto = UserDTO(
                id=user_aggregate.aggregate_id,
                username=user_aggregate.username or "",
                email=user_aggregate.email or "",
                first_name=user_aggregate.first_name,
                last_name=user_aggregate.last_name,
                created_at=user_aggregate.created_at
                or user_aggregate.updated_at,
                updated_at=user_aggregate.updated_at
                or user_aggregate.created_at,
            )

            logger.debug(
                f"Reconstructed user state at {query.timestamp}: {user_dto}"
            )
            return user_dto

        except Exception as e:
            logger.error(
                f"Error getting user state at {query.timestamp} for {query.user_id}: {e}"
            )
            return None
