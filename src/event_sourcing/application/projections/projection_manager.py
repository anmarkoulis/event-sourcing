import logging
from typing import Any, Dict, Optional

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.messaging import EventPublisher

logger = logging.getLogger(__name__)


class ProjectionManager:
    """Manages projections for different event types"""

    def __init__(
        self,
        projections: Dict[str, Any],
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.projections = projections
        self.event_publisher = event_publisher

    async def handle_event(self, event: EventDTO) -> None:
        """Handle a single event by routing to appropriate projections"""
        logger.info(
            f"Handling event {event.event_id} of type {event.event_type}"
        )

        # Route to appropriate projection based on event type
        projection = self._get_projection_for_event(event)
        if projection:
            try:
                await self._handle_event_with_projection(event, projection)
                logger.info(
                    f"Successfully handled event {event.event_id} with projection"
                )
            except Exception as e:
                logger.error(
                    f"Error handling event {event.event_id} with projection: {e}"
                )
                raise
        else:
            logger.warning(
                f"No projection found for event type {event.event_type}"
            )

    def _get_projection_for_event(self, event: EventDTO) -> Optional[Any]:
        """Get the appropriate projection for an event type"""
        # Map event types to projections
        projection_map = {
            "CLIENT_CREATED": "client_projection",
            "CLIENT_UPDATED": "client_projection",
            "CLIENT_DELETED": "client_projection",
            "PROJECTION_CREATED": "projection_projection",
            "PROJECTION_UPDATED": "projection_projection",
        }

        projection_name = projection_map.get(event.event_type.value)
        return (
            self.projections.get(projection_name) if projection_name else None
        )

    async def _handle_event_with_projection(
        self, event: EventDTO, projection: Any
    ) -> None:
        """Handle event with specific projection"""
        # Route to appropriate projection method based on event type
        if event.event_type.value == "CLIENT_CREATED":
            await projection.handle_client_created(event)
        elif event.event_type.value == "CLIENT_UPDATED":
            await projection.handle_client_updated(event)
        elif event.event_type.value == "CLIENT_DELETED":
            await projection.handle_client_deleted(event)
        elif event.event_type.value == "PROJECTION_CREATED":
            await projection.handle_projection_created(event)
        elif event.event_type.value == "PROJECTION_UPDATED":
            await projection.handle_projection_updated(event)
        else:
            logger.warning(
                f"Unknown event type {event.event_type} for projection"
            )

    async def handle_events(self, events: list[EventDTO]) -> None:
        """Handle multiple events in sequence"""
        logger.info(f"Handling {len(events)} events")

        for event in events:
            try:
                await self.handle_event(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_id}: {e}")
                # Continue processing other events
                continue

        logger.info(f"Finished handling {len(events)} events")
