import logging
from typing import List

from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.config.celery_app import app
from event_sourcing.dto import EventDTO
from event_sourcing.enums import EventType

logger = logging.getLogger(__name__)


class CeleryEventHandler(EventHandler):
    """Celery-based event handler for async event processing"""

    async def dispatch(self, events: List[EventDTO]) -> None:
        """Dispatch events to Celery tasks"""
        logger.info(f"Dispatching {len(events)} events to Celery tasks")

        for event in events:
            try:
                # Get task names for this event type
                task_names = self._get_task_names(event.event_type)

                # Convert event to dict for Celery
                event_dict = event.model_dump()

                # Send to all tasks for this event type
                for task_name in task_names:
                    logger.info(
                        f"Dispatching event {event.id} to task {task_name}"
                    )

                    # Send task to Celery
                    app.send_task(
                        task_name,
                        args=[event_dict],
                    )

                    logger.info(
                        f"Successfully dispatched event {event.id} to task {task_name}"
                    )

            except Exception as e:
                logger.error(f"Error dispatching event {event.id}: {e}")
                raise

    def _get_task_names(self, event_type: EventType) -> List[str]:
        """Map event type to list of Celery task names"""
        task_mappings = {
            EventType.USER_CREATED: [
                "process_user_created_task",
                "process_user_created_email_task",
            ],
            EventType.USER_UPDATED: ["process_user_updated_task"],
            EventType.USER_DELETED: ["process_user_deleted_task"],
            EventType.USERNAME_CHANGED: ["process_username_changed_task"],
            EventType.PASSWORD_CHANGED: ["process_password_changed_task"],
            EventType.PASSWORD_RESET_REQUESTED: [
                "process_password_reset_requested_task"
            ],
            EventType.PASSWORD_RESET_COMPLETED: [
                "process_password_reset_completed_task"
            ],
        }

        return task_mappings.get(event_type, ["default_event_handler"])
