"""Synchronous event handler for immediate event processing without Celery.

This handler processes events synchronously by calling projection handlers directly.
Useful for debugging, testing, and environments where immediate consistency is required.
"""

import logging
from typing import Any, List

from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.dto import EventDTO
from event_sourcing.enums import EventType

logger = logging.getLogger(__name__)


class SyncEventHandler(EventHandler):
    """Synchronous event handler for immediate event processing without Celery.

    This handler processes events synchronously by calling projection handlers directly.
    Useful for debugging, testing, and environments where immediate consistency is required.
    """

    def __init__(self, infrastructure_factory: Any = None) -> None:
        self.infrastructure_factory = infrastructure_factory

    async def dispatch(self, events: List[EventDTO]) -> None:
        """Process events synchronously by directly calling handlers"""
        logger.info(f"Processing {len(events)} events synchronously")

        for event in events:
            try:
                # Get handler functions for this event type
                handler_functions = self._get_handler_functions(
                    event.event_type
                )

                # Call all handlers for this event type
                for handler_name in handler_functions:
                    logger.info(
                        f"Processing event {event.id} with handler {handler_name}"
                    )

                    try:
                        # Import and call the handler function
                        await self._call_handler(handler_name, event)
                        logger.info(
                            f"Successfully processed event {event.id} with handler {handler_name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing event {event.id} with handler {handler_name}: {e}"
                        )
                        # In sync mode, we want to raise the error to see what's wrong
                        raise

            except Exception as e:
                logger.error(f"Error processing event {event.id}: {e}")
                raise

    async def _call_handler(self, handler_name: str, event: EventDTO) -> None:
        """Import and call the projection handlers directly"""
        try:
            # Import and call projection handlers directly
            if handler_name == "process_user_created_task":
                if self.infrastructure_factory:
                    # Use the infrastructure factory to create the projection
                    projection = self.infrastructure_factory.create_user_created_projection()
                    await projection.handle(event)
                else:
                    logger.warning(
                        "No infrastructure factory available for user created projection"
                    )

            elif handler_name == "process_user_created_email_task":
                if self.infrastructure_factory:
                    # Use the infrastructure factory to create the projection
                    projection = self.infrastructure_factory.create_user_created_email_projection()
                    await projection.handle(event)
                else:
                    logger.warning(
                        "No infrastructure factory available for email projection"
                    )

            elif handler_name == "process_user_updated_task":
                if self.infrastructure_factory:
                    # Use the infrastructure factory to create the projection
                    projection = self.infrastructure_factory.create_user_updated_projection()
                    await projection.handle(event)
                else:
                    logger.warning(
                        "No infrastructure factory available for user updated projection"
                    )

            elif handler_name == "process_user_deleted_task":
                if self.infrastructure_factory:
                    # Use the infrastructure factory to create the projection
                    projection = self.infrastructure_factory.create_user_deleted_projection()
                    await projection.handle(event)
                else:
                    logger.warning(
                        "No infrastructure factory available for user deleted projection"
                    )

            else:
                logger.warning(f"Unknown handler: {handler_name}")

        except ImportError as e:
            logger.error(f"Could not import handler {handler_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling handler {handler_name}: {e}")
            raise

    def _get_handler_functions(self, event_type: EventType) -> List[str]:
        """Map event type to list of handler function names"""
        handler_mappings = {
            EventType.USER_CREATED: [
                "process_user_created_task",
                "process_user_created_email_task",
            ],
            EventType.USER_UPDATED: ["process_user_updated_task"],
            EventType.USER_DELETED: ["process_user_deleted_task"],
        }

        return handler_mappings.get(event_type, ["default_event_handler"])
