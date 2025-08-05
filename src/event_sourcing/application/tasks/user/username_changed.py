import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.config.celery_app import app
from event_sourcing.infrastructure.event_store.deserializer import (
    deserialize_event,
)
from event_sourcing.infrastructure.provider import get_infrastructure_factory

logger = logging.getLogger(__name__)


@app.task(name="process_username_changed_task")
def process_username_changed_task(event: Dict[str, Any]) -> None:
    """Celery task for processing USERNAME_CHANGED events"""
    try:
        logger.info(
            f"Starting Celery task for USERNAME_CHANGED event: {event.get('event_id', 'unknown')}"
        )

        # Deserialize the event from dictionary to typed event DTO
        event_dto = deserialize_event(event)
        logger.info(
            f"Deserialized event: ID={event_dto.event_id}, Type={event_dto.event_type}"
        )

        # Get infrastructure factory using the same function as FastAPI
        factory = get_infrastructure_factory()
        logger.info("Got infrastructure factory")

        # Get projection
        projection = factory.create_username_changed_projection()
        logger.info("Created username changed projection")

        # Process the event
        async_to_sync(projection.handle)(event_dto)
        logger.info(
            f"Successfully processed USERNAME_CHANGED event for user {event_dto.aggregate_id}"
        )

    except Exception as e:
        logger.error(f"Error processing USERNAME_CHANGED event: {e}")
        raise
