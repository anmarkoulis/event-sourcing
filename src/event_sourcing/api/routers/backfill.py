import logging
from typing import Any, Dict

from fastapi import APIRouter

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.application.commands.backfill import (
    BackfillEntityTypeCommand,
)
from event_sourcing.application.queries.base import GetBackfillStatusQuery

logger = logging.getLogger(__name__)

backfill_router = APIRouter(prefix="/backfill", tags=["backfill"])


@backfill_router.post(
    "/{entity_type}", description="Trigger backfill for entity type"
)
async def trigger_backfill(
    entity_type: str,
    page: int = 1,
    page_size: int = 50,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
    """
    Trigger backfill for a specific entity type.
    This endpoint demonstrates using command handlers for write operations.
    """
    logger.info(f"Triggering backfill for entity type: {entity_type}")

    # Create backfill command
    command = BackfillEntityTypeCommand(
        entity_name=entity_type,
        page=page,
        page_size=page_size,
        source="api",
    )

    # Create command handler using factory method
    handler = (
        infrastructure_factory.create_backfill_entity_type_command_handler()
    )

    # Process command (this will trigger the backfill process)
    await handler.handle(command)

    return {
        "status": "success",
        "message": f"Backfill triggered for entity type: {entity_type}",
        "entity_type": entity_type,
        "page": page,
        "page_size": page_size,
    }


@backfill_router.get(
    "/{entity_type}/status", description="Get backfill status for entity type"
)
async def get_backfill_status(
    entity_type: str,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
    """
    Get backfill status for a specific entity type.
    This endpoint demonstrates using query handlers for read operations.
    """
    logger.info(f"Getting backfill status for entity type: {entity_type}")

    # Create query handler using factory method
    query_handler = (
        infrastructure_factory.create_get_backfill_status_query_handler()
    )

    # Create query object
    query = GetBackfillStatusQuery(entity_type=entity_type)

    # Execute query
    status = await query_handler.handle(query)

    return {
        "status": "success",
        "backfill_status": status,
    }
