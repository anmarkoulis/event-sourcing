import logging
from typing import Dict

from event_sourcing.application.projections.client_projection import (
    ClientProjection,
)
from event_sourcing.domain.events.base import DomainEvent

logger = logging.getLogger(__name__)


class ProjectionManager:
    """Manages projections and routes events to appropriate Celery tasks"""

    def __init__(self, client_projection: ClientProjection):
        self.client_projection = client_projection

        # Event routing map - maps to Celery task names
        self._event_handlers: Dict[str, str] = {
            "client.Created": "process_client_created_projection",
            "client.Updated": "process_client_updated_projection",
            "client.Deleted": "process_client_deleted_projection",
        }

    async def handle_event(self, event: DomainEvent) -> None:
        """Route event to appropriate Celery task for async processing"""
        event_key = f"{event.aggregate_type}.{event.event_type}"

        task_name = self._event_handlers.get(event_key)
        if task_name:
            logger.info(
                f"Triggering Celery task {task_name} for event {event_key}"
            )

            # Trigger Celery task asynchronously using dynamic import
            try:
                from event_sourcing.application.tasks.process_projection import (
                    process_projection_task,
                )

                task = process_projection_task.delay(
                    task_name=task_name,
                    event_data=event.dict(),
                    projection_type="client",
                )
                logger.info(
                    f"Celery task {task_name} triggered with task_id: {task.id}"
                )
            except Exception as e:
                logger.error(f"Error triggering Celery task {task_name}: {e}")
                # Don't fail the event processing if task triggering fails
        else:
            logger.warning(
                f"No projection handler found for event: {event_key}"
            )

    async def handle_events(self, events: list[DomainEvent]) -> None:
        """Handle multiple events by triggering Celery tasks"""
        for event in events:
            await self.handle_event(event)
