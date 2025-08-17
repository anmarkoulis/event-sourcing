import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.config.celery_app import app
from event_sourcing.infrastructure.event_store.deserializer import (
    deserialize_event,
)
from event_sourcing.infrastructure.provider import get_infrastructure_factory
from event_sourcing.utils import log_celery_task

logger = logging.getLogger(__name__)


@app.task(name="process_user_deleted_task")
@log_celery_task
def process_user_deleted_task(event: Dict[str, Any]) -> None:
    """Celery task for processing USER_DELETED events"""
    # Deserialize the event from dictionary to typed event DTO
    event_dto = deserialize_event(event)

    # Get infrastructure factory using the same function as FastAPI
    factory = get_infrastructure_factory()

    # Get projection
    projection = factory.create_user_deleted_projection()

    # Process the event
    async_to_sync(projection.handle)(event_dto)
