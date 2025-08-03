import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.config.celery_app import app
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.provider import get_infrastructure_factory

logger = logging.getLogger(__name__)


@app.task(name="process_password_reset_requested_task")
def process_password_reset_requested_task(event: Dict[str, Any]) -> None:
    """Celery task for processing PASSWORD_RESET_REQUESTED events"""
    try:
        event_dto = EventDTO(**event)

        # Get infrastructure factory using the same function as FastAPI
        factory = get_infrastructure_factory()

        # Get projection
        projection = factory.create_password_reset_requested_projection()

        # Process the event
        async_to_sync(projection.handle)(event_dto)

        logger.info(
            f"Successfully processed PASSWORD_RESET_REQUESTED event for user {event_dto.aggregate_id}"
        )

    except Exception as e:
        logger.error(f"Error processing PASSWORD_RESET_REQUESTED event: {e}")
        raise
