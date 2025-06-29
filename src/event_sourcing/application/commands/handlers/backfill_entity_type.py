import logging

from event_sourcing.application.commands.backfill import (
    BackfillEntityPageCommand,
    BackfillEntityTypeCommand,
)
from event_sourcing.application.commands.salesforce import (
    CreateClientCommand,
)
from event_sourcing.domain.mappings.registry import MappingRegistry
from event_sourcing.infrastructure.provider import get_infrastructure_factory

logger = logging.getLogger(__name__)


class BackfillEntityTypeCommandHandler:
    """Handler for backfilling all entities of a specific type"""

    def __init__(self) -> None:
        self.infrastructure_factory = get_infrastructure_factory()

    async def handle(self, command: BackfillEntityTypeCommand) -> None:
        """Handle backfill entity type command"""
        logger.info(
            f"Starting backfill for entity type: {command.entity_name}"
        )

        page = command.page
        page_size = command.page_size

        while True:
            # Create page command
            page_command = BackfillEntityPageCommand(
                entity_name=command.entity_name,
                page=page,
                page_size=page_size,
                source=command.source,
            )

            # Process page
            has_next = await self._process_page(page_command)
            if not has_next:
                break
            page += 1

        logger.info(
            f"Completed backfill for entity type: {command.entity_name}"
        )

    async def _process_page(self, command: BackfillEntityPageCommand) -> bool:
        """Process a single page of entities"""
        logger.debug(
            f"Processing page {command.page} for {command.entity_name}"
        )

        # Get Salesforce client from infrastructure
        salesforce_client = self.infrastructure_factory.salesforce_client
        if not salesforce_client:
            logger.warning("Salesforce client is not available")
            return False

        # Fetch entities from Salesforce
        entities_page = await salesforce_client.get_entities(
            entity=command.entity_name,
            page=command.page,
            page_size=command.page_size,
        )

        if not entities_page.results:
            logger.debug("No more entities to fetch")
            return False

        # Process each entity
        for entity in entities_page.results:
            await self._process_entity(entity, command.entity_name)

        return bool(entities_page.next)

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
