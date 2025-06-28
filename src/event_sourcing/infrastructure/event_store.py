import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from event_sourcing.domain.events.base import DomainEvent
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
    async def save_event(self, event: DomainEvent) -> None:
        """Save event to store"""

    @abstractmethod
    async def get_events(
        self,
        aggregate_id: str,
        aggregate_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[DomainEvent]:
        """Get events for aggregate with optional time filtering"""


class PostgreSQLEventStore(EventStore):
    """PostgreSQL implementation of event store"""

    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager

    async def save_event(self, event: DomainEvent) -> None:
        """Save event with validation metadata"""
        logger.info(f"Saving event {event.event_id} to PostgreSQL")

        # Create database model from domain event
        event_model = EventModel(
            event_id=event.event_id,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            event_type=event.event_type,
            timestamp=event.timestamp,
            version=event.version,
            data=event.data,
            event_metadata=event.metadata,
            validation_info=event.validation_info,
            source=event.metadata.get("source") if event.metadata else None,
            processed_at=datetime.utcnow(),
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            session.add(event_model)
            await session.commit()
            logger.info(f"Event {event.event_id} saved successfully")

    async def get_events(
        self,
        aggregate_id: str,
        aggregate_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[DomainEvent]:
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

            # Convert to domain events
            domain_events = []
            for event_model in event_models:
                domain_event = DomainEvent(
                    event_id=event_model.event_id,
                    aggregate_id=event_model.aggregate_id,
                    aggregate_type=event_model.aggregate_type,
                    event_type=event_model.event_type,
                    timestamp=event_model.timestamp,
                    version=event_model.version,
                    data=event_model.data,
                    metadata=event_model.event_metadata or {},
                    validation_info=event_model.validation_info,
                )
                domain_events.append(domain_event)

            logger.info(
                f"Retrieved {len(domain_events)} events for {aggregate_type} {aggregate_id}"
            )
            return domain_events

    async def get_events_by_type(
        self, event_type: str, limit: int = 100
    ) -> List[DomainEvent]:
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

            domain_events = []
            for event_model in event_models:
                domain_event = DomainEvent(
                    event_id=event_model.event_id,
                    aggregate_id=event_model.aggregate_id,
                    aggregate_type=event_model.aggregate_type,
                    event_type=event_model.event_type,
                    timestamp=event_model.timestamp,
                    version=event_model.version,
                    data=event_model.data,
                    metadata=event_model.event_metadata or {},
                    validation_info=event_model.validation_info,
                )
                domain_events.append(domain_event)

            return domain_events

    async def get_events_by_source(
        self, source: str, limit: int = 100
    ) -> List[DomainEvent]:
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

            domain_events = []
            for event_model in event_models:
                domain_event = DomainEvent(
                    event_id=event_model.event_id,
                    aggregate_id=event_model.aggregate_id,
                    aggregate_type=event_model.aggregate_type,
                    event_type=event_model.event_type,
                    timestamp=event_model.timestamp,
                    version=event_model.version,
                    data=event_model.data,
                    metadata=event_model.event_metadata or {},
                    validation_info=event_model.validation_info,
                )
                domain_events.append(domain_event)

            return domain_events
