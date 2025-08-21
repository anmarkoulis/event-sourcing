import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto import EventDTO
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.exceptions import UnsupportedAggregateTypeError
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
        start_revision: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventDTO]:
        """Get events for an aggregate in chronological order with optional time filtering"""
        logger.debug(
            f"Getting events for aggregate {aggregate_id} of type {aggregate_type}"
        )

        # For now, we only support User aggregate type
        if aggregate_type != AggregateTypeEnum.USER:
            raise UnsupportedAggregateTypeError(str(aggregate_type))

        query = select(UserEventStream).where(
            UserEventStream.aggregate_id == aggregate_id
        )

        # Add revision/time filters if provided
        if start_revision is not None:
            query = query.where(UserEventStream.revision > start_revision)
            logger.debug(f"Filtering events with revision > {start_revision}")

        # Add time filters if provided
        if start_time:
            query = query.where(UserEventStream.timestamp >= start_time)
            logger.debug(f"Filtering events from {start_time}")

        if end_time:
            query = query.where(UserEventStream.timestamp <= end_time)
            logger.debug(f"Filtering events until {end_time}")

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
                id=event_model.id,  # id is now the event_id
                aggregate_id=event_model.aggregate_id,
                event_type=event_model.event_type,
                timestamp=event_model.timestamp,
                version=event_model.version,
                revision=event_model.revision,
                data=deserialized_data,
            )
            event_dtos.append(event_dto)

        logger.debug(
            f"Retrieved {len(event_dtos)} events for aggregate {aggregate_id}"
        )
        return event_dtos

    async def append_to_stream(
        self,
        aggregate_id: uuid.UUID,
        aggregate_type: AggregateTypeEnum,
        events: List[EventDTO],
    ) -> None:
        """Append events to the stream for an aggregate (no commit - handled by UoW)"""
        logger.debug(
            f"Appending {len(events)} events to aggregate stream {aggregate_id} of type {aggregate_type}"
        )

        # For now, we only support User aggregate type
        if aggregate_type != AggregateTypeEnum.USER:
            raise UnsupportedAggregateTypeError(str(aggregate_type))

        # Track event IDs to prevent duplicates within this call
        event_ids_in_this_call = set()

        for event in events:
            if event.id in event_ids_in_this_call:
                logger.warning(
                    f"Duplicate event ID detected in same call: {event.id}"
                )
                continue

            event_ids_in_this_call.add(event.id)
            logger.debug(
                f"Adding event to session: ID={event.id}, Type={event.event_type}, Revision={event.revision}, Object ID={id(event)}"
            )
            event_model = UserEventStream(
                id=event.id,  # event.id is the event_id
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                version=event.version,
                revision=event.revision,
                data=event.data.model_dump(),  # Convert Pydantic model to dict
            )
            self.session.add(event_model)
            logger.debug(f"Event model added to session: {event_model}")

        logger.debug(
            f"Events added to session for aggregate stream {aggregate_id}"
        )

    async def search_events(
        self,
        aggregate_type: AggregateTypeEnum,
        query_params: dict,
    ) -> List[EventDTO]:
        """Search events by aggregate type and query parameters"""
        logger.debug(
            f"Searching events for aggregate type {aggregate_type} with params: {query_params}"
        )

        # For now, we only support User aggregate type
        if aggregate_type != AggregateTypeEnum.USER:
            raise UnsupportedAggregateTypeError(str(aggregate_type))

        # Build query based on parameters
        query = select(UserEventStream)

        # Add filters based on query_params
        if "start_time" in query_params:
            query = query.where(
                UserEventStream.timestamp >= query_params["start_time"]
            )

        if "end_time" in query_params:
            query = query.where(
                UserEventStream.timestamp <= query_params["end_time"]
            )

        if "event_type" in query_params:
            query = query.where(
                UserEventStream.event_type == query_params["event_type"]
            )

        if "aggregate_id" in query_params:
            query = query.where(
                UserEventStream.aggregate_id == query_params["aggregate_id"]
            )

        # Add filters for username and email by searching in the JSON data field
        if "username" in query_params:
            username = query_params["username"]
            # Search for USER_CREATED events with this username
            query = query.where(
                UserEventStream.event_type == "USER_CREATED"
            ).where(UserEventStream.data["username"].astext == username)

        if "email" in query_params:
            email = query_params["email"]
            # Search for USER_CREATED events with this email
            query = query.where(
                UserEventStream.event_type == "USER_CREATED"
            ).where(UserEventStream.data["email"].astext == email)

        # Add ordering
        query = query.order_by(UserEventStream.timestamp.desc())

        # Add limit if specified
        if "limit" in query_params:
            query = query.limit(query_params["limit"])

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
                id=event_model.id,  # id is now the event_id
                aggregate_id=event_model.aggregate_id,
                event_type=event_model.event_type,
                timestamp=event_model.timestamp,
                version=event_model.version,
                revision=event_model.revision,
                data=deserialized_data,
            )
            event_dtos.append(event_dto)

        logger.debug(f"Event DTOs: {event_dtos}")
        logger.debug(
            f"Found {len(event_dtos)} events matching search criteria"
        )
        return event_dtos
