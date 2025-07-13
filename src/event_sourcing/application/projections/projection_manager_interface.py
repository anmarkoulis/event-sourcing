import logging
from abc import ABC, abstractmethod
from typing import Dict

from event_sourcing.application.events.event_handler import (
    EventHandlerInterface,
)
from event_sourcing.dto.event import EventDTO
from event_sourcing.enums import EventType

logger = logging.getLogger(__name__)


class ProjectionManagerInterface(ABC):
    """Abstract interface for projection managers"""

    @abstractmethod
    async def handle_event(self, event: EventDTO) -> None:
        """Handle a domain event by triggering appropriate projections"""

    @abstractmethod
    async def handle_events(self, events: list[EventDTO]) -> None:
        """Handle multiple domain events"""

    @abstractmethod
    def register_projection_handler(
        self, event_key: str, task_name: str
    ) -> None:
        """Register a projection handler for a specific event type"""


class GenericProjectionManager(ProjectionManagerInterface):
    """
    Generic projection manager that uses the event handler to dispatch projection jobs.

    This follows the standard CQRS pattern where:
    1. Domain events are stored in the event store
    2. Events trigger async processing via the event handler
    3. Celery tasks handle the actual projection logic
    """

    def __init__(self, event_handler: EventHandlerInterface):
        """
        Initialize generic projection manager

        :param event_handler: The event handler to use for dispatching projection jobs
        """
        self.event_handler = event_handler
        self.projection_handlers: Dict[str, str] = {}
        logger.info("Initialized GenericProjectionManager")

    def register_projection_handler(
        self, event_key: str, task_name: str
    ) -> None:
        """
        Register a projection handler for a specific event type

        :param event_key: Event key in format "aggregate_type.event_type" (e.g., "client.Created")
        :param task_name: Celery task name to execute for this event type
        """
        self.projection_handlers[event_key] = task_name
        logger.info(
            f"Registered projection handler: {event_key} -> {task_name}"
        )

    async def handle_event(self, event: EventDTO) -> None:
        """
        Handle a domain event by creating a projection job and dispatching it via the event handler

        :param event: The domain event to handle
        """
        event_key = f"{event.aggregate_type}.{event.event_type.value}"
        task_name = self.projection_handlers.get(event_key)

        if task_name:
            logger.info(f"Handling projection for event: {event_key}")

            # Create projection job as EventDTO with projection event type
            projection_job = EventDTO(
                event_id=event.event_id,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                event_type=EventType.PROJECTION_CREATED,  # Use projection event type
                timestamp=event.timestamp,
                version=event.version,
                data={
                    "task_name": task_name,
                    "event_data": event.model_dump(),
                    "projection_type": event.aggregate_type,
                },
                event_metadata={
                    "projection_job": True,
                    "original_event_id": str(event.event_id),
                    "task_name": task_name,
                },
                validation_info=event.validation_info,
                source=event.source,
                processed_at=event.processed_at,
            )

            # Dispatch projection job via event handler (this will trigger Celery task)
            try:
                await self.event_handler.dispatch(projection_job)
                logger.info(
                    f"Successfully dispatched projection job for event: {event_key}"
                )
            except Exception as e:
                logger.error(
                    f"Error dispatching projection job for event {event_key}: {e}"
                )
                # Don't fail the event processing if projection fails
                # Projections can be retried later
        else:
            logger.warning(
                f"No projection handler registered for event: {event_key}"
            )

    async def handle_events(self, events: list[EventDTO]) -> None:
        """
        Handle multiple domain events

        :param events: List of domain events to handle
        """
        for event in events:
            await self.handle_event(event)

    def get_registered_handlers(self) -> Dict[str, str]:
        """Get all registered projection handlers"""
        return self.projection_handlers.copy()


class MockProjectionManager(ProjectionManagerInterface):
    """Mock projection manager for testing"""

    def __init__(self) -> None:
        self.handled_events: list[EventDTO] = []
        self.registered_handlers: Dict[str, str] = {}

    async def handle_event(self, event: EventDTO) -> None:
        """Mock handle event - just store the event"""
        self.handled_events.append(event)
        logger.info(
            f"Mock projection manager handled event: {event.event_type}"
        )

    async def handle_events(self, events: list[EventDTO]) -> None:
        """Mock handle events"""
        for event in events:
            await self.handle_event(event)

    def register_projection_handler(
        self, event_key: str, task_name: str
    ) -> None:
        """Mock register projection handler"""
        self.registered_handlers[event_key] = task_name
        logger.info(
            f"Mock registered projection handler: {event_key} -> {task_name}"
        )
