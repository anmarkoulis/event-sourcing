import logging

from event_sourcing.domain.events.base import DomainEvent
from event_sourcing.domain.mappings.registry import MappingRegistry
from event_sourcing.infrastructure.read_model import ReadModel

logger = logging.getLogger(__name__)


class ClientProjection:
    """Projection for building client read models from events"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def handle_client_created(self, event: DomainEvent) -> None:
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

    async def handle_client_updated(self, event: DomainEvent) -> None:
        """Handle client updated event"""
        logger.info(f"Handling client updated event: {event.event_id}")

        # Apply mappings to event data
        mapped_data = self._apply_mappings(event.data, "Account")

        # Get existing client
        existing_client = await self.read_model.get_client(event.aggregate_id)
        if not existing_client:
            logger.warning(
                f"Client not found for update: {event.aggregate_id}"
            )
            return

        # Update only provided fields
        update_data = {"updated_at": event.timestamp}
        if "name" in mapped_data and mapped_data["name"] is not None:
            update_data["name"] = mapped_data["name"]
        if "parent_id" in mapped_data and mapped_data["parent_id"] is not None:
            update_data["parent_id"] = mapped_data["parent_id"]
        if "status" in mapped_data and mapped_data["status"] is not None:
            update_data["status"] = mapped_data["status"]

        # Save updated client
        await self.read_model.update_client(event.aggregate_id, update_data)
        logger.info(f"Client read model updated: {event.aggregate_id}")

    async def handle_client_deleted(self, event: DomainEvent) -> None:
        """Handle client deleted event"""
        logger.info(f"Handling client deleted event: {event.event_id}")

        # Mark client as deleted
        update_data = {
            "is_deleted": True,
            "updated_at": event.timestamp,
        }

        await self.read_model.update_client(event.aggregate_id, update_data)
        logger.info(
            f"Client read model marked as deleted: {event.aggregate_id}"
        )

    def _apply_mappings(self, event_data: dict, entity_name: str) -> dict:
        """Apply field mappings to event data"""
        mappings_class = MappingRegistry.get_mappings(entity_name)
        if not mappings_class:
            logger.warning(f"No mappings found for entity: {entity_name}")
            return event_data

        mappings = mappings_class.get_mappings()
        mapped_data = {}

        for key, mapping in mappings.items():
            try:
                mapped_data[key] = (
                    mapping.operation(event_data, mapping.value)
                    if callable(mapping.operation)
                    else mapping.value
                )
            except KeyError:
                logger.debug(f"Field {key} not found in event data")
                continue
            except Exception as e:
                logger.error(f"Error applying mapping for field {key}: {e}")
                continue

        return mapped_data
