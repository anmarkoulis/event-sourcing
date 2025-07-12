import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.application.commands.crm import AsyncProcessCRMEventCommand
from event_sourcing.dto.event import EventReadDTO, EventWriteDTO

logger = logging.getLogger(__name__)

events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.post(
    "/salesforce/",
    description="Process Salesforce events from AWS EventBridge asynchronously via Celery",
    response_model=EventReadDTO,
)
async def process_salesforce_event(
    salesforce_event: Dict[str, Any],  # Accept raw dict, no DTO
    infrastructure_factory: InfrastructureFactoryDep,
) -> EventReadDTO:
    """
    Process Salesforce events from AWS EventBridge asynchronously via Celery.
    Accepts the full AWS EventBridge payload as-is, with no DTO or field aliasing.
    """
    # Use the factory method to create EventWriteDTO from Salesforce event
    raw_event = EventWriteDTO.from_salesforce_event(salesforce_event)

    provider = raw_event.source.value
    logger.info(f"Processing {provider} event asynchronously: {raw_event}")
    entity_type = "client"  # Default to client for now

    command = AsyncProcessCRMEventCommand(
        raw_event=raw_event,
        provider=provider,
        entity_type=entity_type,
    )

    handler = (
        infrastructure_factory.create_async_process_crm_event_command_handler()
    )

    await handler.handle(command)

    logger.info(
        f"Successfully triggered async processing for {provider} event"
    )

    # Ensure event_id is not None since we generate it in the factory method
    event_id = raw_event.event_id
    if event_id is None:
        raise HTTPException(
            status_code=500, detail="Event ID was not generated properly"
        )

    return EventReadDTO(
        event_id=event_id,
        aggregate_id=raw_event.aggregate_id,
        aggregate_type=raw_event.aggregate_type,
        event_type=raw_event.event_type,
        timestamp=raw_event.timestamp,
        version=raw_event.version,
        data=raw_event.data,
        event_metadata=raw_event.event_metadata,
        validation_info=raw_event.validation_info,
        source=raw_event.source,
        processed_at=raw_event.timestamp,
    )
