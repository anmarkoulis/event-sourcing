import logging
from typing import Dict, List

from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.dto.event import EventDTO

logger = logging.getLogger(__name__)


class CeleryEventHandler(EventHandler):
    """Celery implementation of event handler"""

    def __init__(self, task_registry: Dict[str, List[str]]):
        self.task_registry = task_registry

    async def dispatch(self, events: List[EventDTO]) -> None:
        """Dispatch events to Celery tasks"""
        for event in events:
            event_type = event.event_type.value

            if event_type in self.task_registry:
                task_names = self.task_registry[event_type]

                for task_name in task_names:
                    try:
                        # Use send_task to avoid imports and make it more flexible
                        from event_sourcing.config.celery_app import app

                        app.send_task(
                            task_name, kwargs={"event": event.model_dump()}
                        )

                        logger.info(
                            f"Dispatching event {event.event_id} to task {task_name}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Error dispatching event {event.event_id} to task {task_name}: {e}"
                        )
            else:
                logger.warning(
                    f"No tasks registered for event type: {event_type}"
                )
