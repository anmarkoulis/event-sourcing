import logging
from typing import Any, List

from event_sourcing.application.commands.crm import ProcessCRMEventCommand
from event_sourcing.domain.aggregates.registry import AggregateRegistry
from event_sourcing.domain.events.base import DomainEvent
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.providers.base import CRMProviderFactory

logger = logging.getLogger(__name__)


class ProcessCRMEventCommandHandler:
    """Handler for processing CRM events from any provider"""

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
        logger.info(
            f"Processing {command.provider} event: {command.raw_event}"
        )

        # 1. Get appropriate provider
        provider = self.provider_factory.create_provider(
            command.provider, self.provider_config
        )

        # 2. Parse event using provider
        parsed_event = provider.parse_event(command.raw_event)
        if not parsed_event:
            logger.warning(f"Failed to parse {command.provider} event")
            return

        logger.info(f"Parsed {command.provider} event: {parsed_event}")

        # 3. Transform to domain event
        domain_event = provider.translate_to_domain_event(parsed_event)

        # 4. Process through aggregate (pure business logic)
        aggregate = await self._get_or_create_aggregate(
            domain_event.aggregate_id, domain_event.aggregate_type
        )
        events = await self._process_event_through_aggregate(
            domain_event, aggregate, provider
        )

        # 5. Store events
        for event in events:
            await self.event_store.save_event(event)
            logger.info(f"Saved domain event: {event}")

    async def _process_event_through_aggregate(
        self, domain_event: DomainEvent, aggregate: Any, provider: Any
    ) -> List[DomainEvent]:
        """Process domain event through aggregate for business logic"""
        logger.info(
            f"Processing domain event through aggregate: {domain_event.event_type}"
        )

        # Check if we need to handle missing create events
        if self._needs_create_event(domain_event, aggregate):
            logger.info(
                f"Handling missing create event for {domain_event.aggregate_id}"
            )
            complete_state = await provider.get_entity(
                domain_event.aggregate_id, domain_event.aggregate_type
            )
            if complete_state:
                create_event = self._create_missing_create_event(
                    complete_state, domain_event
                )
                events = [create_event, domain_event]
            else:
                logger.warning(
                    f"Could not fetch complete state for {domain_event.aggregate_id}"
                )
                events = [domain_event]
        else:
            # Process event through aggregate (pure business logic)
            if hasattr(aggregate, "process_crm_event"):
                events = aggregate.process_crm_event(domain_event)
            else:
                # Fallback: create domain event directly
                events = [domain_event]

        logger.info(
            f"Aggregate processed event into {len(events)} domain events"
        )
        return events

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

    def _needs_create_event(self, event: DomainEvent, aggregate: Any) -> bool:
        """Check if we need to create a missing CREATE event"""
        # Business rule: If UPDATE/DELETE received before CREATE, we need to fetch complete state
        return (
            event.event_type in ["Updated", "Deleted"]
            and not aggregate.events
            and event.metadata.get("source") in ["salesforce", "hubspot"]
        )

    def _create_missing_create_event(
        self, complete_state: dict, original_event: DomainEvent
    ) -> DomainEvent:
        """Create a missing CREATE event from complete state"""
        from event_sourcing.domain.events.client import ClientCreatedEvent

        # Create CREATE event with complete state
        create_event = ClientCreatedEvent.create(
            aggregate_id=original_event.aggregate_id,
            data=complete_state,
            metadata={
                "source": original_event.metadata.get("source"),
                "created_from_backfill": True,
                "original_event_id": original_event.event_id,
            },
        )

        logger.info(
            f"Created missing CREATE event for {original_event.aggregate_id}"
        )
        return create_event
