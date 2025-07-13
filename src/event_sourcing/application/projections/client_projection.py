import logging
from typing import Any, Dict, Optional

from event_sourcing.domain.mappings.registry import MappingRegistry
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.messaging import EventPublisher
from event_sourcing.infrastructure.read_model import ReadModel

logger = logging.getLogger(__name__)


class ClientProjection:
    """Projection for building client read models from events"""

    def __init__(
        self,
        read_model: ReadModel,
        event_publisher: Optional[EventPublisher] = None,
    ) -> None:
        self.read_model = read_model
        self.event_publisher = event_publisher

    async def handle_client_created(self, event: EventDTO) -> None:
        """Handle client created event"""
        logger.info(f"Handling client created event: {event.event_id}")

        # Apply mappings to event data
        mapped_data = self._apply_mappings(event.data, "Account")

        # Build read model from event
        client_data = {
            "aggregate_id": event.aggregate_id,
            "name": mapped_data.get("name"),
            "parent_id": mapped_data.get("parent_id"),
            "status": mapped_data.get("status"),
            "created_at": event.timestamp,
            "updated_at": event.timestamp,
        }

        # Save to read model
        await self.read_model.save_client(client_data)
        logger.info(f"Client read model created: {event.aggregate_id}")

        # Broadcast read model to EventBridge
        await self._publish_client_event("ClientCreated", client_data, event)

    async def handle_client_updated(self, event: EventDTO) -> None:
        """Handle client updated event"""
        logger.info(f"Handling client updated event: {event.event_id}")

        # Apply mappings to event data
        mapped_data = self._apply_mappings(event.data, "Account")

        # Build read model from event
        client_data = {
            "aggregate_id": event.aggregate_id,
            "name": mapped_data.get("name"),
            "parent_id": mapped_data.get("parent_id"),
            "status": mapped_data.get("status"),
            "updated_at": event.timestamp,
        }

        # Update read model
        await self.read_model.update_client(client_data)
        logger.info(f"Client read model updated: {event.aggregate_id}")

        # Broadcast read model to EventBridge
        await self._publish_client_event("ClientUpdated", client_data, event)

    async def handle_client_deleted(self, event: EventDTO) -> None:
        """Handle client deleted event"""
        logger.info(f"Handling client deleted event: {event.event_id}")

        # Build read model from event
        client_data = {
            "aggregate_id": event.aggregate_id,
            "deleted_at": event.timestamp,
        }

        # Mark as deleted in read model
        await self.read_model.delete_client(event.aggregate_id)
        logger.info(f"Client read model deleted: {event.aggregate_id}")

        # Broadcast read model to EventBridge
        await self._publish_client_event("ClientDeleted", client_data, event)

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

    async def _publish_client_event(
        self,
        event_type: str,
        client_data: Dict[str, Any],
        domain_event: EventDTO,
    ) -> None:
        """Publish client event to EventBridge"""
        if not self.event_publisher:
            logger.debug("No event publisher configured, skipping broadcast")
            return

        try:
            await self.event_publisher.publish(
                {
                    "event_type": event_type,
                    "aggregate_id": domain_event.aggregate_id,
                    "data": client_data,
                    "timestamp": domain_event.timestamp.isoformat(),
                    "source": domain_event.source.value,
                }
            )
            logger.info(f"Published {event_type} event to EventBridge")
        except Exception as e:
            logger.error(f"Error publishing {event_type} event: {e}")
            # Don't fail the projection if publishing fails
