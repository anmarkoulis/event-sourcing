import logging
import uuid
from datetime import datetime

from event_sourcing.application.commands.salesforce import CreateClientCommand
from event_sourcing.domain.mappings.registry import MappingRegistry
from event_sourcing.dto.event import EventDTO
from event_sourcing.enums import EventSourceEnum, EventType
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.messaging import EventPublisher

logger = logging.getLogger(__name__)


class CreateClientCommandHandler:
    """Handler for creating client aggregates"""

    def __init__(
        self,
        event_store: EventStore,
        event_publisher: EventPublisher,
    ):
        self.event_store = event_store
        self.event_publisher = event_publisher

    async def handle(self, command: CreateClientCommand) -> None:
        """Handle create client command"""
        logger.info(f"Creating client: {command.client_id}")

        # Apply mappings to raw data
        mapped_data = self._apply_mappings(command.data, "Account")

        # Create event DTO
        event = EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=command.client_id,
            aggregate_type="client",
            event_type=EventType.CLIENT_CREATED,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            data=mapped_data,
            event_metadata={
                "source": command.source,
                "command_id": command.client_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            validation_info={},
            source=EventSourceEnum.SALESFORCE,
            processed_at=datetime.utcnow(),
        )

        # Save event to event store (this will trigger projections automatically)
        await self.event_store.save_event(event)

        # Publish to external systems if needed
        if self.event_publisher:
            await self.event_publisher.publish(
                {
                    "event_type": "ClientCreated",
                    "aggregate_id": command.client_id,
                    "data": mapped_data,
                    "timestamp": event.timestamp.isoformat(),
                }
            )

        logger.info(f"Successfully created client: {command.client_id}")

    def _apply_mappings(self, raw_data: dict, entity_name: str) -> dict:
        """Apply field mappings to raw data"""
        mappings_class = MappingRegistry.get_mappings(entity_name)
        if not mappings_class:
            logger.warning(f"No mappings found for entity: {entity_name}")
            return raw_data

        mappings = mappings_class.get_mappings()
        mapped_data = {}

        for key, mapping in mappings.items():
            try:
                mapped_data[key] = (
                    mapping.operation(raw_data, mapping.value)
                    if callable(mapping.operation)
                    else mapping.value
                )
            except KeyError:
                logger.debug(f"Field {key} not found in raw data")
                continue
            except Exception as e:
                logger.error(f"Error applying mapping for field {key}: {e}")
                continue

        return mapped_data
