import logging
from typing import Any, List

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

        provider = self.provider_factory.create_provider(
            command.provider, self.provider_config
        )

        # 4. Process through aggregate (pure business logic)
        aggregate = await self._get_or_create_aggregate(
            command.event.aggregate_id, command.event.aggregate_type
        )
        events = await self._process_event_through_aggregate(
            command.event, aggregate, provider
        )

        # 5. Store events
        for event in events:
            await self.event_store.save_event(event)
            logger.info(f"Saved event: {event}")

    async def _process_event_through_aggregate(
        self, event_dto: EventDTO, aggregate: Any, provider: Any
    ) -> List[EventDTO]:
        """Process event through aggregate with business logic"""
        logger.info(
            f"Processing event through aggregate: {event_dto.event_id}"
        )

        # Let aggregate process the event (business logic validation first)
        processed_events = aggregate.process_crm_event(event_dto)

        # Apply event to aggregate state after validation
        aggregate.apply(event_dto)

        logger.info(f"Aggregate processed {len(processed_events)} events")
        return processed_events  # type: ignore[no-any-return]

    async def _get_or_create_aggregate(
        self, aggregate_id: str, aggregate_type: str
    ) -> Any:
        """Get or create aggregate instance"""
        # Get existing events for this aggregate
        existing_events = await self.event_store.get_events(
            aggregate_id, aggregate_type
        )

        # Get aggregate class from registry
        aggregate_class = AggregateRegistry.get_aggregate(aggregate_type)
        if not aggregate_class:
            raise ValueError(f"No aggregate found for type: {aggregate_type}")

        # Create aggregate instance
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
