import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from event_sourcing.dto.event import EventDTO
from event_sourcing.enums import EventType

logger = logging.getLogger(__name__)


class EventHandlerInterface(ABC):
    """Abstract interface for event dispatching"""

    @abstractmethod
    async def dispatch(
        self,
        event: EventDTO,
        delay: Optional[int] = None,
        queue: Optional[str] = None,
    ) -> None:
        """
        Dispatch an event for processing

        :param event: The event to dispatch
        :param delay: Optional delay in seconds before processing
        :param queue: Optional queue name for processing
        """


class CeleryEventHandler(EventHandlerInterface):
    """Concrete implementation using Celery for event dispatching"""

    def __init__(self, task_registry: Dict[str, Any]):
        """
        Initialize Celery event handler

        :param task_registry: Dictionary mapping event types to Celery tasks
        """
        self.task_registry = task_registry
        # Simple mapping: event_type -> task_name
        self.event_type_to_task = {
            EventType.CLIENT_CREATED: "process_crm_event",
            EventType.CLIENT_UPDATED: "process_crm_event",
            EventType.CLIENT_DELETED: "process_crm_event",
            EventType.PROJECTION_CREATED: "process_projection",
            EventType.PROJECTION_UPDATED: "process_projection",
            EventType.SNAPSHOT_CREATED: "publish_snapshot",
            EventType.SNAPSHOT_UPDATED: "publish_snapshot",
            EventType.SNAPSHOT_DELETED: "publish_snapshot",
            EventType.SYSTEM_ERROR: "process_system_error",
            EventType.SYSTEM_WARNING: "process_system_warning",
        }
        logger.info("Initialized CeleryEventHandler with task registry")

    async def dispatch(
        self,
        event: EventDTO,
        delay: Optional[int] = None,
        queue: Optional[str] = None,
    ) -> None:
        """
        Dispatch event using Celery

        :param event: The event to dispatch
        :param delay: Optional delay in seconds before processing
        :param queue: Optional queue name for processing
        """
        logger.info(f"Dispatching event {event.event_id} via Celery")

        # Get task name based on event type
        task_name = self.event_type_to_task.get(event.event_type)
        if not task_name:
            logger.warning(
                f"No task mapping found for event type: {event.event_type}"
            )
            return

        # Get the task from registry
        task = self.task_registry.get(task_name)
        if not task:
            logger.error(f"No task registered for task name: {task_name}")
            return

        # Prepare task arguments
        task_kwargs = {
            "event_data": event.model_dump(),
        }

        # Execute task with optional delay and queue
        try:
            if delay:
                task_result = task.apply_async(
                    kwargs=task_kwargs, countdown=delay, queue=queue
                )
            else:
                task_result = task.apply_async(kwargs=task_kwargs, queue=queue)

            logger.info(
                f"Celery task {task_name} dispatched with task_id: {task_result.id}"
            )

        except Exception as e:
            logger.error(f"Error dispatching Celery task {task_name}: {e}")
            raise


class MockEventHandler(EventHandlerInterface):
    """Mock implementation for testing"""

    def __init__(self) -> None:
        self.dispatched_events: list[Dict[str, Any]] = []

    async def dispatch(
        self,
        event: EventDTO,
        delay: Optional[int] = None,
        queue: Optional[str] = None,
    ) -> None:
        """
        Mock dispatch that just stores the event

        :param event: The event to dispatch
        :param delay: Optional delay (ignored in mock)
        :param queue: Optional queue (ignored in mock)
        """
        logger.info(f"Mock dispatching event {event.event_id}")
        self.dispatched_events.append(
            {"event": event, "delay": delay, "queue": queue}
        )
