import logging

from event_sourcing.application.commands.backfill import (
    BackfillSpecificEntityCommand,
)
from event_sourcing.application.commands.salesforce import CreateClientCommand
from event_sourcing.domain.mappings.registry import MappingRegistry
from event_sourcing.infrastructure.provider import get_infrastructure_factory

logger = logging.getLogger(__name__)


class BackfillSpecificEntityCommandHandler:
    """Handler for backfilling a specific entity"""

    def __init__(self) -> None:
        self.infrastructure_factory = get_infrastructure_factory()

    async def handle(self, command: BackfillSpecificEntityCommand) -> None:
        """Handle backfill specific entity command"""
        logger.info(
            f"Backfilling specific entity: {command.aggregate_type} {command.aggregate_id}"
        )

        # Get Salesforce client from infrastructure
        salesforce_client = self.infrastructure_factory.salesforce_client
        if not salesforce_client:
            logger.warning("Salesforce client is not available")
            return

        # Get entity from Salesforce
        entity = await salesforce_client.get_entity(
            command.aggregate_id, command.aggregate_type
        )

        if not entity:
            logger.warning(
                f"Entity not found: {command.aggregate_type} {command.aggregate_id}"
            )
            return

        # Process the entity
        await self._process_entity(entity, command.aggregate_type)

    async def _process_entity(self, entity: dict, entity_name: str) -> None:
        """Process a single entity for backfill"""
        entity_id = entity.get("Id")
        if not entity_id:
            logger.warning(f"Entity missing ID: {entity}")
            return

        # Create appropriate command based on entity type
        normalized_entity_name = MappingRegistry.get_normalized_entity_name(
            entity_name
        )

        if normalized_entity_name == "client":
            create_command = CreateClientCommand(
                client_id=entity_id,
                data=entity,
                source="backfill",
            )
            # Process the command
            await self._process_create_client_command(create_command)
        else:
            logger.warning(
                f"Backfill not implemented for entity type: {entity_name}"
            )

    async def _process_create_client_command(
        self, command: CreateClientCommand
    ) -> None:
        """Process create client command for backfill"""
        logger.info(
            f"Processing backfill create client command for: {command.client_id}"
        )

        # Get command handler
        from event_sourcing.application.commands.handlers.create_client import (
            CreateClientCommandHandler,
        )

        handler = CreateClientCommandHandler(
            event_store=self.infrastructure_factory.event_store,
            event_publisher=self.infrastructure_factory.event_publisher,
        )

        # Process the command
        await handler.handle(command)
