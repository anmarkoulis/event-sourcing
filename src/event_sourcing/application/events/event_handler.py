import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from event_sourcing.dto.event import EventWriteDTO

logger = logging.getLogger(__name__)


class EventHandlerInterface(ABC):
    """Abstract interface for event dispatching"""

    @abstractmethod
    async def dispatch(
        self,
        event: EventWriteDTO,
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
        logger.info("Initialized CeleryEventHandler with task registry")

    async def dispatch(
        self,
        event: EventWriteDTO,
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

        # Convert EventWriteDTO to dict for Celery serialization
        event_dict = event.model_dump()

        # Convert UUID to string for Celery serialization
        if event_dict.get("event_id") and hasattr(
            event_dict["event_id"], "__str__"
        ):
            event_dict["event_id"] = str(event_dict["event_id"])

        # Check if this is a projection job
        if event.event_metadata and event.event_metadata.get("projection_job"):
            # Handle projection job
            await self._dispatch_projection_job(event, delay, queue)
        else:
            # Handle regular CRM event
            await self._dispatch_crm_event(event, delay, queue)

    async def _dispatch_projection_job(
        self,
        event: EventWriteDTO,
        delay: Optional[int] = None,
        queue: Optional[str] = None,
    ) -> None:
        """Dispatch projection job to Celery"""
        task_name = event.event_metadata.get("task_name")
        if not task_name:
            raise ValueError("Projection job missing task_name in metadata")

        # Get the projection task
        task = self.task_registry.get("process_projection")
        if not task:
            raise ValueError("No process_projection task registered")

        # Prepare task arguments for projection
        task_kwargs = {
            "task_name": task_name,
            "event_data": event.data.get("event_data", {}),
            "projection_type": event.data.get("projection_type", "unknown"),
        }

        # Execute projection task
        try:
            if delay:
                task_result = task.apply_async(
                    kwargs=task_kwargs, countdown=delay, queue=queue
                )
            else:
                task_result = task.apply_async(kwargs=task_kwargs, queue=queue)

            logger.info(
                f"Projection task {task_name} dispatched with task_id: {task_result.id}"
            )

        except Exception as e:
            logger.error(f"Error dispatching projection task {task_name}: {e}")
            raise

    async def _dispatch_crm_event(
        self,
        event: EventWriteDTO,
        delay: Optional[int] = None,
        queue: Optional[str] = None,
    ) -> None:
        """Dispatch CRM event to Celery"""
        # Get the appropriate task based on event type
        task_name = self._get_task_name(event.event_type)
        task = self.task_registry.get(task_name)

        if not task:
            raise ValueError(
                f"No task registered for event type: {event.event_type}"
            )

        # Prepare task arguments for CRM event
        task_kwargs = {
            "command_id": str(event.event_id) if event.event_id else "",
            "raw_event": event.model_dump(),
            "provider": event.source.value.lower(),
            "entity_type": event.aggregate_type,
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

    def _get_task_name(self, event_type: str) -> str:
        """
        Get the Celery task name based on event type

        :param event_type: The type of event
        :return: The task name to use
        """
        # Map event types to task names
        task_mapping = {
            "created": "process_crm_event",
            "updated": "process_crm_event",
            "deleted": "process_crm_event",
            "upserted": "process_crm_event",
        }

        return task_mapping.get(event_type.lower(), "process_crm_event")


class MockEventHandler(EventHandlerInterface):
    """Mock implementation for testing"""

    def __init__(self) -> None:
        self.dispatched_events: list[Dict[str, Any]] = []

    async def dispatch(
        self,
        event: EventWriteDTO,
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
