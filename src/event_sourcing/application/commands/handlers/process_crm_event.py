import logging
import uuid
from typing import Any

from event_sourcing.application.commands.crm import ProcessCRMEventCommand
from event_sourcing.domain.aggregates.registry import AggregateRegistry
from event_sourcing.dto.event import EventDTO
from event_sourcing.enums import EventType
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.providers.base.provider_factory import (
    CRMProviderFactory,
)

logger = logging.getLogger(__name__)


class ProcessCRMEventCommandHandler:
    """Handler for processing CRM events"""

    def __init__(
        self,
        event_store: EventStore,
        provider_factory: CRMProviderFactory,
        provider_config: dict,
    ):
        self.event_store = event_store
        self.provider_factory = provider_factory
        self.provider_config = provider_config

    async def handle(self, command: ProcessCRMEventCommand) -> None:
        """Handle process CRM event command"""
        logger.info(f"Processing {command.provider} event: {command.event}")

        # Note: Provider is created but not currently used in this implementation
        # This is a placeholder for future provider-specific event parsing
        # provider = self.provider_factory.create_provider(
        #     command.provider, self.provider_config
        # )

        # Get or create aggregate using external_id + source lookup
        aggregate = await self._get_or_create_aggregate(
            command.event.external_id,
            command.event.source.value,
            command.event.aggregate_type,
        )

        # Set the aggregate_id on the event if it was None
        if command.event.aggregate_id is None:
            command.event.aggregate_id = aggregate.aggregate_id

        # Apply event to aggregate (pure domain logic)
        aggregate.apply(command.event)

        # Store the event
        await self.event_store.save_event(command.event)
        logger.info(f"Saved event: {command.event}")

    async def _get_or_create_aggregate(
        self, external_id: str, source: str, aggregate_type: str
    ) -> Any:
        """Get or create aggregate instance using external_id + source lookup"""
        # Try to find existing aggregate by external_id + source
        existing_events = (
            await self.event_store.get_events_by_external_id_and_source(
                external_id, source
            )
        )

        if existing_events:
            # Use existing aggregate_id from first event
            aggregate_id = existing_events[0].aggregate_id
            if aggregate_id is None:
                raise ValueError(
                    f"Found existing event with None aggregate_id for external_id: {external_id}"
                )
            logger.info(
                f"Found existing aggregate: {aggregate_id} for external_id: {external_id}"
            )
        else:
            # Generate new aggregate_id for new aggregate
            aggregate_id = uuid.uuid4()
            logger.info(
                f"Creating new aggregate: {aggregate_id} for external_id: {external_id}"
            )

        # Get aggregate class from registry
        aggregate_class = AggregateRegistry.get_aggregate(aggregate_type)
        if not aggregate_class:
            raise ValueError(f"No aggregate found for type: {aggregate_type}")

        # Create aggregate instance with the determined aggregate_id
        aggregate = aggregate_class(aggregate_id)

        # Apply existing events to reconstruct state
        for event in existing_events:
            aggregate.apply(event)

        return aggregate

    def _needs_create_event(self, event: EventDTO, aggregate: Any) -> bool:
        """Check if we need to create a missing CREATE event"""
        # Business rule: If UPDATE/DELETE received before CREATE, we need to fetch complete state
        source = (
            event.event_metadata.get("source")
            if event.event_metadata
            else None
        )
        return (
            event.event_type.value in ["CLIENT_UPDATED", "CLIENT_DELETED"]
            and not aggregate.events
            and source in ["salesforce", "hubspot"]
        )

    def _create_missing_create_event(
        self, complete_state: dict, original_event: EventDTO
    ) -> EventDTO:
        """Create a missing CREATE event from complete state"""

        # Create CREATE event with complete state
        create_event = EventDTO(
            event_id=original_event.event_id,
            aggregate_id=original_event.aggregate_id,
            external_id=original_event.external_id,
            aggregate_type=original_event.aggregate_type,
            event_type=EventType.CLIENT_CREATED,
            timestamp=original_event.timestamp,
            version=original_event.version,
            data=complete_state,
            event_metadata={
                "source": original_event.event_metadata.get("source")
                if original_event.event_metadata
                else None,
                "created_from_backfill": True,
                "original_event_id": original_event.event_id,
            },
            validation_info=original_event.validation_info,
            source=original_event.source,
            processed_at=original_event.processed_at,
        )

        logger.info(
            f"Created missing CREATE event for {original_event.aggregate_id}"
        )
        return create_event
