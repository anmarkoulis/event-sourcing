import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.database.models.write.user_event_stream import (
    UserEventStream,
)

from .base import EventStore

logger = logging.getLogger(__name__)


class PostgreSQLEventStore(EventStore):
    """PostgreSQL implementation of event store"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stream(
        self,
        aggregate_id: uuid.UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventDTO]:
        """Get events for an aggregate in chronological order with optional time filtering"""
        logger.info(f"Getting events for aggregate {aggregate_id}")

        query = select(UserEventStream).where(
            UserEventStream.aggregate_id == aggregate_id
        )

        # Add time filters if provided
        if start_time:
            query = query.where(UserEventStream.timestamp >= start_time)
            logger.info(f"Filtering events from {start_time}")

        if end_time:
            query = query.where(UserEventStream.timestamp <= end_time)
            logger.info(f"Filtering events until {end_time}")

        query = query.order_by(UserEventStream.timestamp.asc())

        result = await self.session.execute(query)
        event_models = result.scalars().all()

        # Convert to DTOs
        event_dtos = []
        for event_model in event_models:
            event_dto = EventDTO(
                event_id=event_model.event_id,
                aggregate_id=event_model.aggregate_id,
                event_type=event_model.event_type,
                timestamp=event_model.timestamp,
                version=event_model.version,
                data=event_model.data,
                event_metadata=event_model.event_metadata,
                validation_info=event_model.validation_info,
                source=event_model.source,
                processed_at=event_model.processed_at,
            )
            event_dtos.append(event_dto)

        logger.info(
            f"Retrieved {len(event_dtos)} events for aggregate {aggregate_id}"
        )
        return event_dtos

    async def append_to_stream(
        self,
        aggregate_id: uuid.UUID,
        events: List[EventDTO],
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Append events to the stream for an aggregate (no commit - handled by UoW)"""
        logger.info(
            f"Appending {len(events)} events to aggregate stream {aggregate_id}"
        )

        # Use provided session or the one from constructor
        target_session = session or self.session

        for event in events:
            event_model = UserEventStream(
                event_id=event.event_id,
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                version=event.version,
                data=event.data,
                event_metadata=event.event_metadata,
                validation_info=event.validation_info,
                source=event.source,
                processed_at=event.processed_at or datetime.utcnow(),
            )
            target_session.add(event_model)

        logger.info(
            f"Events added to session for aggregate stream {aggregate_id}"
        )
