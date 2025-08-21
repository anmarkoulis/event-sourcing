import logging
from typing import List

from celery import Celery

from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.dto import EventDTO
from event_sourcing.enums import EventType

logger = logging.getLogger(__name__)


class CeleryEventHandler(EventHandler):
    """Celery-based event handler for async event processing"""

    def __init__(self, celery_app: Celery) -> None:
        """Initialize CeleryEventHandler with a Celery app instance.

        :param celery_app: The Celery application instance to use for task dispatching.
        """
        self.celery_app = celery_app

    async def dispatch(self, events: List[EventDTO]) -> None:
        """Dispatch events to Celery tasks"""
        logger.debug(f"Dispatching {len(events)} events to Celery tasks")

        for event in events:
            try:
                # Get task names for this event type
                task_names = self._get_task_names(event.event_type)

                # Convert event to dict for Celery
                event_dict = event.model_dump()

                # Send to all tasks for this event type
                for task_name in task_names:
                    logger.debug(
                        f"Dispatching event {event.id} to task {task_name}"
                    )

                    # Send task to Celery
                    self.celery_app.send_task(
                        task_name,
                        args=[event_dict],
                    )

                    logger.debug(
                        f"Successfully dispatched event {event.id} to task {task_name}"
                    )

            except Exception as e:
                logger.error(f"Error dispatching event {event.id}: {e}")
                raise

    def _get_task_names(self, event_type: EventType) -> List[str]:
        """Map event type to list of Celery task names"""
        match event_type:
            case EventType.USER_CREATED:
                return [
                    "process_user_created_task",
                    "process_user_created_email_task",
                ]
            case EventType.USER_UPDATED:
                return ["process_user_updated_task"]
            case EventType.USER_DELETED:
                return ["process_user_deleted_task"]
            case EventType.PASSWORD_CHANGED:
                return ["process_password_changed_task"]
            case _:
                return ["default_event_handler"]
