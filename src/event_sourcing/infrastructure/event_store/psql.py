import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto import EventDTO
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.database.models.write.user_event_stream import (
    UserEventStream,
)
from event_sourcing.infrastructure.event_store.deserializer import (
    deserialize_event_data,
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
        aggregate_type: AggregateTypeEnum,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventDTO]:
        """Get events for an aggregate in chronological order with optional time filtering"""
        logger.info(
            f"Getting events for aggregate {aggregate_id} of type {aggregate_type}"
        )

        # For now, we only support User aggregate type
        if aggregate_type != AggregateTypeEnum.USER:
            raise ValueError(f"Unsupported aggregate type: {aggregate_type}")

        query = select(UserEventStream).where(
            UserEventStream.id == aggregate_id
        )

        # Add time filters if provided
        if start_time:
            query = query.where(UserEventStream.timestamp >= start_time)
            logger.info(f"Filtering events from {start_time}")

        if end_time:
            query = query.where(UserEventStream.timestamp <= end_time)
            logger.info(f"Filtering events until {end_time}")

        query = query.order_by(UserEventStream.revision.asc())

        result = await self.session.execute(query)
        event_models = result.scalars().all()

        # Convert to DTOs
        event_dtos = []
        for event_model in event_models:
            # Deserialize the data from dictionary to typed data model
            deserialized_data = deserialize_event_data(
                event_model.event_type, event_model.data
            )

            event_dto = EventDTO(
                event_id=event_model.event_id,
                aggregate_id=event_model.id,  # id is now the aggregate_id
                event_type=event_model.event_type,
                timestamp=event_model.timestamp,
                version=event_model.version,
                revision=event_model.revision,
                data=deserialized_data,
            )
            event_dtos.append(event_dto)

        logger.info(
            f"Retrieved {len(event_dtos)} events for aggregate {aggregate_id}"
        )
        return event_dtos

    async def append_to_stream(
        self,
        aggregate_id: uuid.UUID,
        aggregate_type: AggregateTypeEnum,
        events: List[EventDTO],
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Append events to the stream for an aggregate (no commit - handled by UoW)"""
        logger.info(
            f"Appending {len(events)} events to aggregate stream {aggregate_id} of type {aggregate_type}"
        )

        # For now, we only support User aggregate type
        if aggregate_type != AggregateTypeEnum.USER:
            raise ValueError(f"Unsupported aggregate type: {aggregate_type}")

        # Use provided session or the one from constructor
        target_session = session or self.session

        for event in events:
            event_model = UserEventStream(
                event_id=event.event_id,
                id=event.aggregate_id,  # Use aggregate_id as the id
                event_type=event.event_type,
                timestamp=event.timestamp,
                version=event.version,
                revision=event.revision,
                data=event.data.model_dump(),  # Convert Pydantic model to dict
            )
            target_session.add(event_model)

        logger.info(
            f"Events added to session for aggregate stream {aggregate_id}"
        )

    async def search_events(
        self,
        aggregate_type: AggregateTypeEnum,
        query_params: dict,
    ) -> List[EventDTO]:
        """Search events by aggregate type and query parameters"""
        logger.info(
            f"Searching events for aggregate type {aggregate_type} with params: {query_params}"
        )

        # For now, we only support User aggregate type
        if aggregate_type != AggregateTypeEnum.USER:
            raise ValueError(f"Unsupported aggregate type: {aggregate_type}")

        query = select(UserEventStream)

        # Add filters based on query parameters
        if "username" in query_params:
            # Search for USER_CREATED events with specific username
            query = query.where(
                UserEventStream.event_type == "USER_CREATED",
                UserEventStream.data.contains(
                    {"username": query_params["username"]}
                ),
            )

        if "email" in query_params:
            # Search for USER_CREATED events with specific email
            query = query.where(
                UserEventStream.event_type == "USER_CREATED",
                UserEventStream.data.contains(
                    {"email": query_params["email"]}
                ),
            )

        # Order by revision (sequence number)
        query = query.order_by(UserEventStream.revision.asc())

        result = await self.session.execute(query)
        event_models = result.scalars().all()

        # Convert to DTOs
        event_dtos = []
        for event_model in event_models:
            # Deserialize the data from dictionary to typed data model
            deserialized_data = deserialize_event_data(
                event_model.event_type, event_model.data
            )

            event_dto = EventDTO(
                event_id=event_model.event_id,
                aggregate_id=event_model.id,  # id is now the aggregate_id
                event_type=event_model.event_type,
                timestamp=event_model.timestamp,
                version=event_model.version,
                revision=event_model.revision,
                data=deserialized_data,
            )
            event_dtos.append(event_dto)

        logger.info(f"Found {len(event_dtos)} events matching search criteria")
        return event_dtos
