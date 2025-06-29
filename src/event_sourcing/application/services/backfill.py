import logging
from datetime import datetime
from typing import Any, Dict

from event_sourcing.application.commands.salesforce import (
    CreateClientCommand,
    CreateClientCommandData,
)
from event_sourcing.domain.mappings.registry import MappingRegistry

logger = logging.getLogger(__name__)


class BackfillService:
    """Service for handling historical data ingestion and processing"""

    def __init__(self, salesforce_client, event_store):
        self.salesforce_client = salesforce_client
        self.event_store = event_store

    async def backfill_entity_type(self, entity_name: str) -> None:
        """Backfill all entities of a specific type"""
        logger.info(f"Starting backfill for entity type: {entity_name}")

        page = 1
        page_size = 50

        while True:
            has_next = await self._backfill_page(entity_name, page, page_size)
            if not has_next:
                break
            page += 1

        logger.info(f"Completed backfill for entity type: {entity_name}")

    async def _backfill_page(
        self, entity_name: str, page: int, page_size: int
    ) -> bool:
        """Process a single page of entities for backfill"""
        logger.debug(f"Fetching {entity_name} from Salesforce, page {page}")

        entities_page = await self.salesforce_client.get_entities(
            entity=entity_name, page=page, page_size=page_size
        )

        if not entities_page.results:
            logger.debug("No more entities to fetch")
            return False

        for entity in entities_page.results:
            # Generate creation command for each entity
            self._create_creation_command(entity, entity_name)
            # In a real implementation, this would be sent to a command bus
            logger.info(
                f"Created backfill command for {entity_name} {entity['Id']}"
            )

        return bool(entities_page.next)

    async def trigger_backfill(
        self, aggregate_id: str, aggregate_type: str
    ) -> None:
        """Trigger backfill for a specific aggregate"""
        logger.info(f"Triggering backfill for {aggregate_type} {aggregate_id}")

        # Get entity from Salesforce
        entity = await self.salesforce_client.get_entity(
            aggregate_id, aggregate_type
        )
        if entity:
            self._create_creation_command(entity, aggregate_type)
            # In a real implementation, this would be sent to a command bus
            logger.info(
                f"Created backfill command for {aggregate_type} {aggregate_id}"
            )

    def _create_creation_command(
        self, entity: dict, entity_name: str
    ) -> CreateClientCommand:
        """Create a creation command from entity data"""
        normalized_entity_name = MappingRegistry.get_normalized_entity_name(
            entity_name
        )

        if normalized_entity_name == "client":
            data = CreateClientCommandData(
                client_id=entity["Id"],
                data=entity,
                source="backfill",
            )
            return CreateClientCommand.create(
                data=data.dict(),
                metadata={"entity_name": entity_name},
            )
        # Add other entity types as needed
        raise NotImplementedError(
            f"Backfill not implemented for entity type: {entity_name}"
        )

    async def get_backfill_status(self, entity_type: str) -> Dict[str, Any]:
        """Get status of backfill operation"""
        # Implementation for tracking backfill progress
        # This would typically query a status table or cache
        return {
            "entity_type": entity_type,
            "status": "not_implemented",
            "timestamp": datetime.utcnow(),
        }
