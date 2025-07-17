import logging
import uuid
from typing import Any, Dict

from event_sourcing.application.commands.crm import ProcessCRMEventCommand
from event_sourcing.domain.aggregates.registry import AggregateRegistry
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.providers.base import CRMProviderFactory

logger = logging.getLogger(__name__)


class ProcessCRMEventCommandHandler:
    """Handler for processing CRM events - thin orchestration layer"""

    def __init__(
        self,
        event_store: EventStore,
        provider_factory: CRMProviderFactory,
        provider_config: Dict[str, Any],
    ):
        self.event_store = event_store
        self.provider_factory = provider_factory
        self.provider_config = provider_config

    async def handle(self, command: ProcessCRMEventCommand) -> None:
        """Handle process CRM event command - thin orchestration"""
        logger.info(f"Processing {command.provider} event via command handler")

        # 1. Get provider instance
        provider = self.provider_factory.create_provider(
            command.provider, self.provider_config
        )

        # 2. Use provider to extract external_id and source
        external_id, source = provider.extract_identifiers(command.raw_event)

        # 3. Use provider to determine aggregate type
        aggregate_type = provider.extract_aggregate_type(command.raw_event)

        # 4. Query previous events for this external_id and source
        previous_events = (
            await self.event_store.get_events_by_external_id_and_source(
                external_id, source
            )
        )

        # 5. Find or create aggregate ID using event store
        aggregate_id = await self.event_store.find_or_create_aggregate_id(
            external_id, source, aggregate_type
        )

        # 6. Create aggregate instance with the correct ID and provider
        aggregate = self._create_aggregate_instance(
            aggregate_id, provider, aggregate_type
        )

        # 7. Let aggregate handle CRM parsing, lifecycle, and business logic
        domain_events = aggregate.process_crm_event(
            command.raw_event, previous_events, command.provider
        )

        # 7. Store domain events (event store handles dispatching)
        for event in domain_events:
            await self.event_store.save_event(event)
            logger.info(f"Saved domain event: {event.event_id}")

    def _extract_identifiers(
        self, raw_event: Dict[str, Any], provider: Any
    ) -> tuple[str, str]:
        """Extract external_id and source from raw CRM event"""
        # For Salesforce events
        if (
            hasattr(provider, "get_provider_name")
            and provider.get_provider_name() == "salesforce"
        ):
            payload = raw_event.get("detail", {}).get("payload", {})
            change_header = payload.get("ChangeEventHeader", {})
            record_ids = change_header.get("recordIds", [])
            external_id = record_ids[0] if record_ids else str(uuid.uuid4())
            source = "SALESFORCE"  # This should match EventSourceEnum.SALESFORCE.value
            return external_id, source
        else:
            # For other providers, implement as needed
            raise ValueError(
                f"Unsupported provider for identifier extraction: {provider}"
            )

    def _create_aggregate_instance(
        self, aggregate_id: uuid.UUID, provider: Any, aggregate_type: str
    ) -> Any:
        """Create empty aggregate instance based on aggregate type"""
        # Get aggregate class from registry
        aggregate_class = AggregateRegistry.get_aggregate(aggregate_type)
        if not aggregate_class:
            raise ValueError(f"No aggregate found for type: {aggregate_type}")

        # Create empty aggregate instance with the provided ID and provider
        aggregate = aggregate_class(aggregate_id, provider)
        logger.info(
            f"Created {aggregate_type} aggregate instance with ID: {aggregate_id}"
        )

        return aggregate
