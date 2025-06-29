import logging
from typing import Any, List

from event_sourcing.application.commands.backfill import (
    BackfillSpecificEntityCommand,
)
from event_sourcing.application.commands.salesforce import (
    ProcessSalesforceEventCommand,
)
from event_sourcing.domain.aggregates.registry import AggregateRegistry
from event_sourcing.domain.events.base import DomainEvent
from event_sourcing.domain.events.client import (
    ClientCreatedEvent,
    ClientDeletedEvent,
    ClientUpdatedEvent,
)
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.messaging import EventPublisher
from event_sourcing.infrastructure.provider import get_infrastructure_factory
from event_sourcing.infrastructure.read_model import ReadModel

logger = logging.getLogger(__name__)


class ProcessSalesforceEventCommandHandler:
    """Handler for processing Salesforce CDC events"""

    def __init__(
        self,
        event_store: EventStore,
        read_model: ReadModel,
        event_publisher: EventPublisher,
    ):
        self.event_store = event_store
        self.read_model = read_model
        self.event_publisher = event_publisher

    async def handle(self, command: ProcessSalesforceEventCommand) -> None:
        """Handle process Salesforce event command"""
        logger.info(f"Processing Salesforce event: {command.raw_event}")

        # 1. Parse and validate raw event
        parsed_events = self._parse_salesforce_event(command.raw_event)
        logger.info(f"Parsed events: {parsed_events}")

        for parsed_event in parsed_events:
            logger.info(f"Processing parsed event: {parsed_event}")

            # 2. Process event through aggregate (business logic)
            domain_events = await self._process_event_through_aggregate(
                parsed_event
            )

            # 3. Store domain events (this automatically triggers projections)
            for domain_event in domain_events:
                await self.event_store.save_event(domain_event)
                logger.info(
                    f"Saved domain event and triggered projections: {domain_event}"
                )

    async def _process_event_through_aggregate(
        self, salesforce_event: DomainEvent
    ) -> List[DomainEvent]:
        """Process Salesforce event through aggregate for business logic"""
        aggregate_id = salesforce_event.aggregate_id
        aggregate_type = salesforce_event.aggregate_type

        # Get or create aggregate
        aggregate = await self._get_or_create_aggregate(
            aggregate_id, aggregate_type
        )

        # Get Salesforce client for API calls if needed
        infrastructure_factory = get_infrastructure_factory()
        salesforce_client = infrastructure_factory.salesforce_client

        # Process event through aggregate (business logic)
        # Cast to ClientAggregate since we know it has the process_salesforce_event method
        from event_sourcing.domain.aggregates.client import ClientAggregate

        if isinstance(aggregate, ClientAggregate):
            domain_events = aggregate.process_salesforce_event(
                salesforce_event, salesforce_client
            )
        else:
            # Fallback: create domain event directly
            domain_events = [salesforce_event]

        logger.info(
            f"Aggregate processed event into {len(domain_events)} domain events"
        )
        return domain_events  # type: ignore[no-any-return]

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

    def _parse_salesforce_event(self, raw_event: dict) -> List[DomainEvent]:
        """Parse Salesforce CDC event into domain events"""
        try:
            # Extract the payload from the CDC event structure
            payload = raw_event.get("detail", {}).get("payload", {})
            change_event_header = payload.get("ChangeEventHeader", {})

            entity_name = change_event_header.get("entityName")
            change_type = change_event_header.get("changeType")
            record_ids = change_event_header.get("recordIds", [])

            if not record_ids:
                logger.warning("No record IDs found in ChangeEventHeader")
                return []

            record_id = record_ids[0]  # Take the first record ID

            # Create metadata for the event
            metadata = {
                "source": "salesforce",
                "entity_name": entity_name,
                "change_type": change_type,
                "record_id": record_id,
                "commit_timestamp": change_event_header.get("commitTimestamp"),
            }

            events = []

            # Map Salesforce entity names to our domain entities
            if entity_name == "Account":
                # Create appropriate domain event based on change type
                if change_type == "CREATE":
                    event = ClientCreatedEvent.create(
                        aggregate_id=record_id, data=payload, metadata=metadata
                    )
                    events.append(event)
                elif change_type == "UPDATE":
                    event = ClientUpdatedEvent.create(
                        aggregate_id=record_id, data=payload, metadata=metadata
                    )
                    events.append(event)
                elif change_type == "DELETE":
                    event = ClientDeletedEvent.create(
                        aggregate_id=record_id, data=payload, metadata=metadata
                    )
                    events.append(event)
                else:
                    logger.warning(f"Unsupported change type: {change_type}")
            else:
                logger.warning(f"Unsupported entity type: {entity_name}")

            logger.info(
                f"Created {len(events)} domain events from Salesforce event"
            )
            return events

        except Exception as e:
            logger.error(f"Error parsing Salesforce event: {e}")
            return []

    async def _validate_event_ordering(self, event: DomainEvent) -> bool:
        """Validate event ordering and consistency"""
        existing_events = await self.event_store.get_events(
            event.aggregate_id, event.aggregate_type
        )

        if event.event_type == "Created":
            if existing_events:
                logger.warning(
                    f"Creation event received for existing aggregate {event.aggregate_id}"
                )
                return False
        else:
            if not existing_events:
                logger.warning(
                    f"Non-creation event received for non-existent aggregate {event.aggregate_id}"
                )
                # Trigger backfill using command instead of service
                await self._trigger_backfill(
                    event.aggregate_id, event.aggregate_type
                )
                return False

        return True

    async def _trigger_backfill(
        self, aggregate_id: str, aggregate_type: str
    ) -> None:
        """Trigger backfill using command instead of service"""
        logger.info(f"Triggering backfill for {aggregate_type} {aggregate_id}")

        # Create backfill command
        backfill_command = BackfillSpecificEntityCommand(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            source="salesforce_event",
        )

        # Process backfill command
        from .backfill_specific_entity import (
            BackfillSpecificEntityCommandHandler,
        )

        backfill_handler = BackfillSpecificEntityCommandHandler()
        await backfill_handler.handle(backfill_command)
