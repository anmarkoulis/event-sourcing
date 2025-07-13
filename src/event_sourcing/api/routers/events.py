import logging
from typing import Any, Dict

from fastapi import APIRouter

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.dto.event import EventDTO

logger = logging.getLogger(__name__)

events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.post(
    "/salesforce/",
    description="Process Salesforce events from AWS EventBridge asynchronously via Celery",
    response_model=EventDTO,
)
async def process_salesforce_event(
    salesforce_event: Dict[str, Any],  # Accept raw dict, no DTO
    infrastructure_factory: InfrastructureFactoryDep,
) -> EventDTO:
    """
    Process Salesforce events from AWS EventBridge asynchronously via Celery.
    Accepts the full AWS EventBridge payload as-is, with no DTO or field aliasing.
    """
    # Use the factory method to create EventDTO from Salesforce event
    event_dto = EventDTO.from_salesforce_event(salesforce_event)

    provider = event_dto.source.value
    logger.info(f"Processing {provider} event asynchronously: {event_dto}")

    # Get event handler directly from infrastructure factory
    event_handler = infrastructure_factory.event_handler

    # Dispatch event directly via event handler
    await event_handler.dispatch(event_dto)

    logger.info(f"Successfully dispatched {provider} event via event handler")

    return event_dto
