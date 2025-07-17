import logging
from typing import Any, Dict

from fastapi import APIRouter

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.application.commands.crm import ProcessCRMEventCommand

logger = logging.getLogger(__name__)

events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.post(
    "/salesforce/",
    description="Process Salesforce events from AWS EventBridge asynchronously via Celery",
)
async def process_salesforce_event(
    salesforce_event: Dict[str, Any],  # Accept raw dict, no DTO
    infrastructure_factory: InfrastructureFactoryDep,
) -> Dict[str, str]:
    """
    Process Salesforce events from AWS EventBridge asynchronously via Celery.
    Accepts the full AWS EventBridge payload as-is, with no DTO or field aliasing.
    """
    try:
        command = ProcessCRMEventCommand(
            provider="salesforce", raw_event=salesforce_event
        )

        # Process through command handler (synchronously)
        command_handler = (
            infrastructure_factory.create_process_crm_event_command_handler()
        )
        await command_handler.handle(command)
        logger.info(
            f"Successfully processed Salesforce event via command handler"
        )
    except Exception as e:
        logger.error(f"Error processing Salesforce event: {e}")

    return {"status": "processing"}
