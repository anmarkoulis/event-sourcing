"""Wrapper for managing session creation in command handlers."""

import inspect
import logging
from typing import TYPE_CHECKING, Any, Dict, Type

from event_sourcing.infrastructure.event_store import PostgreSQLEventStore
from event_sourcing.infrastructure.unit_of_work import SQLAUnitOfWork

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .infrastructure_factory import InfrastructureFactory


class CommandHandlerWrapper:
    """Wrapper that manages session creation for command handlers."""

    def __init__(
        self, factory: "InfrastructureFactory", handler_class: Type
    ) -> None:
        """Initialize CommandHandlerWrapper.

        :param factory: Infrastructure factory instance.
        :param handler_class: Command handler class to wrap.
        """
        self.factory = factory
        self.handler_class = handler_class

    async def _create_handler_with_session(self) -> tuple[Any, Any]:
        """Create a fresh session and handler for this operation.

        :return: Tuple of (command_handler, session).
        """
        session = await self.factory.session_manager.get_session()
        uow = SQLAUnitOfWork(session)
        event_store = PostgreSQLEventStore(session)

        # Build constructor kwargs (all command handlers receive snapshot_store)
        ctor_kwargs: Dict[str, Any] = {
            "event_store": event_store,
            "event_handler": self.factory.event_handler,
            "unit_of_work": uow,
        }

        from event_sourcing.infrastructure.snapshot_store.psql_store import (
            PsqlSnapshotStore,
        )

        logger.info("Creating snapshot store")
        ctor_kwargs["snapshot_store"] = PsqlSnapshotStore(session)

        # Add hashing service only for command handlers that need it
        # Check if the handler class expects hashing_service parameter
        sig = inspect.signature(self.handler_class.__init__)
        if "hashing_service" in sig.parameters:
            from event_sourcing.infrastructure.security.hashing_service import (
                BcryptHashingService,
            )

            ctor_kwargs["hashing_service"] = BcryptHashingService()

        command_handler = self.handler_class(**ctor_kwargs)
        return command_handler, session

    async def handle(self, command: Any) -> Any:
        """Handle the command with proper session management.

        :param command: Command to handle.
        :return: Result from command handler.
        """
        logger.info(
            f"Wrapper: Starting command handler for command: {type(command).__name__}"
        )
        command_handler, session = await self._create_handler_with_session()
        try:
            logger.info(f"Wrapper: Calling command handler")
            result = await command_handler.handle(command)
            logger.info(f"Wrapper: Command handler completed successfully")
            return result
        except Exception as e:
            logger.error(f"Wrapper: Error in command handler: {e}")
            raise
        finally:
            logger.info(f"Wrapper: Closing session")
            await session.close()
