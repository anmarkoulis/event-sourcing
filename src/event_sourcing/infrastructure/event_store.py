import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import select

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.database.models.event import (
    Event as EventModel,
)
from event_sourcing.infrastructure.database.session import (
    AsyncDBContextManager,
    DatabaseManager,
)

logger = logging.getLogger(__name__)


class EventStore(ABC):
    """Abstract event store interface"""

    @abstractmethod
    async def save_event(self, event: EventDTO) -> None:
        """Save event to store"""

    @abstractmethod
    async def get_events(
        self,
        aggregate_id: uuid.UUID,
        aggregate_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventDTO]:
        """Get events for aggregate with optional time filtering"""

    @abstractmethod
    async def get_events_by_external_id_and_source(
        self, external_id: str, source: str
    ) -> List[EventDTO]:
        """Get events by external_id and source (for finding existing aggregates)"""


class PostgreSQLEventStore(EventStore):
    """PostgreSQL implementation of event store with automatic projection triggering"""

    def __init__(
        self,
        database_manager: DatabaseManager,
        projection_manager: Optional[Any] = None,
    ):
        self.database_manager = database_manager
        self.projection_manager = projection_manager

    async def save_event(self, event: EventDTO) -> None:
        """Save event with validation metadata and trigger projections"""
        logger.info(f"Saving event {event.event_id} to PostgreSQL")

        # Create database model from event DTO
        event_model = EventModel(
            event_id=event.event_id,
            aggregate_id=event.aggregate_id,
            external_id=event.external_id,
            aggregate_type=event.aggregate_type,
            event_type=event.event_type,
            timestamp=event.timestamp,
            version=event.version,
            data=event.data,
            event_metadata=event.event_metadata,
            validation_info=event.validation_info,
            source=event.source,
            processed_at=event.processed_at or datetime.utcnow(),
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            session.add(event_model)
            await session.commit()
            logger.info(f"Event {event.event_id} saved successfully")

        # Trigger projections automatically (event-driven)
        if self.projection_manager:
            try:
                await self.projection_manager.handle_event(event)
                logger.info(
                    f"Projections triggered for event {event.event_id}"
                )
            except Exception as e:
                logger.error(
                    f"Error triggering projections for event {event.event_id}: {e}"
                )
                # Don't fail the event save if projections fail
                # Projections can be retried later

    async def get_events(
        self,
        aggregate_id: uuid.UUID,
        aggregate_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventDTO]:
        """Get events with optional time filtering"""
        logger.info(f"Retrieving events for {aggregate_type} {aggregate_id}")

        # Build query
        query = (
            select(EventModel)
            .where(
                EventModel.aggregate_id == aggregate_id,
                EventModel.aggregate_type == aggregate_type,
            )
            .order_by(EventModel.timestamp.asc())
        )

        # Add time filters if provided
        if start_time:
            query = query.where(EventModel.timestamp >= start_time)

        if end_time:
            query = query.where(EventModel.timestamp <= end_time)

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(query)
            event_models = result.scalars().all()

            # Convert to event DTOs
            event_dtos = []
            for event_model in event_models:
                event_dto = EventDTO(
                    event_id=event_model.event_id,
                    aggregate_id=event_model.aggregate_id,
                    external_id=event_model.external_id,
                    aggregate_type=event_model.aggregate_type,
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
                f"Retrieved {len(event_dtos)} events for {aggregate_type} {aggregate_id}"
            )
            return event_dtos

    async def get_events_by_external_id_and_source(
        self, external_id: str, source: str
    ) -> List[EventDTO]:
        """Get events by external_id and source (for finding existing aggregates)"""
        logger.info(
            f"Retrieving events for external_id: {external_id}, source: {source}"
        )

        query = (
            select(EventModel)
            .where(
                EventModel.external_id == external_id,
                EventModel.source == source,
            )
            .order_by(EventModel.timestamp.asc())
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(query)
            event_models = result.scalars().all()

            # Convert to event DTOs
            event_dtos = []
            for event_model in event_models:
                event_dto = EventDTO(
                    event_id=event_model.event_id,
                    aggregate_id=event_model.aggregate_id,
                    external_id=event_model.external_id,
                    aggregate_type=event_model.aggregate_type,
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
                f"Retrieved {len(event_dtos)} events for external_id: {external_id}, source: {source}"
            )
            return event_dtos

    async def get_events_by_type(
        self, event_type: str, limit: int = 100
    ) -> List[EventDTO]:
        """Get events by type (useful for debugging and monitoring)"""
        logger.info(f"Retrieving {limit} events of type {event_type}")

        query = (
            select(EventModel)
            .where(EventModel.event_type == event_type)
            .order_by(EventModel.timestamp.desc())
            .limit(limit)
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(query)
            event_models = result.scalars().all()

            event_dtos = []
            for event_model in event_models:
                event_dto = EventDTO(
                    event_id=event_model.event_id,
                    aggregate_id=event_model.aggregate_id,
                    external_id=event_model.external_id,
                    aggregate_type=event_model.aggregate_type,
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

            return event_dtos

    async def get_events_by_source(
        self, source: str, limit: int = 100
    ) -> List[EventDTO]:
        """Get events by source (e.g., 'salesforce', 'backfill')"""
        logger.info(f"Retrieving {limit} events from source {source}")

        query = (
            select(EventModel)
            .where(EventModel.source == source)
            .order_by(EventModel.timestamp.desc())
            .limit(limit)
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(query)
            event_models = result.scalars().all()

            event_dtos = []
            for event_model in event_models:
                event_dto = EventDTO(
                    event_id=event_model.event_id,
                    aggregate_id=event_model.aggregate_id,
                    external_id=event_model.external_id,
                    aggregate_type=event_model.aggregate_type,
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

            return event_dtos
