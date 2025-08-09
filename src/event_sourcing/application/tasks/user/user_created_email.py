import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.config.celery_app import app
from event_sourcing.infrastructure.event_store.deserializer import (
    deserialize_event,
)
from event_sourcing.infrastructure.provider import get_infrastructure_factory

logger = logging.getLogger(__name__)


@app.task(name="process_user_created_email_task")
def process_user_created_email_task(event: Dict[str, Any]) -> None:
    """Celery task for processing USER_CREATED events and sending welcome emails"""
    try:
        logger.info(
            f"Starting Celery task for USER_CREATED email projection: {event.get('id', 'unknown')}"
        )

        # Deserialize the event from dictionary to typed event DTO
        event_dto = deserialize_event(event)
        logger.info(
            f"Deserialized event: ID={event_dto.id}, Type={event_dto.event_type}"
        )

        # Get infrastructure factory using the same function as FastAPI
        factory = get_infrastructure_factory()

        # Get email projection
        projection = factory.create_user_created_email_projection()

        # Process the event
        async_to_sync(projection.handle)(event_dto)

        logger.info(
            f"Successfully processed USER_CREATED email projection for user {event_dto.aggregate_id}"
        )

    except Exception as e:
        logger.error(f"Error processing USER_CREATED email projection: {e}")
        raise
