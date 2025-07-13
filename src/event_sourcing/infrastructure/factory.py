import logging
from typing import Any, Dict, Optional

from event_sourcing.infrastructure.database.session import DatabaseManager
from event_sourcing.infrastructure.event_store import PostgreSQLEventStore
from event_sourcing.infrastructure.messaging import EventBridgePublisher
from event_sourcing.infrastructure.providers.base import CRMProviderFactory
from event_sourcing.infrastructure.providers.salesforce import (
    SalesforceProvider,
)
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class InfrastructureFactory:
    """Factory for creating infrastructure components, command handlers, and query handlers"""

    def __init__(
        self, database_url: str, eventbridge_region: str = "us-east-1"
    ):
        self.database_url = database_url
        self.eventbridge_region = eventbridge_region
        self._database_manager: Optional[DatabaseManager] = None
        self._event_store: Optional[PostgreSQLEventStore] = None
        self._read_model: Optional[PostgreSQLReadModel] = None
        self._event_publisher: Optional[EventBridgePublisher] = None
        self._projection_manager: Optional[Any] = None
        self._salesforce_client: Optional[Any] = None
        self._provider_factory: Optional[CRMProviderFactory] = None
        self._event_handler: Optional[Any] = None

    @property
    def database_manager(self) -> DatabaseManager:
        """Get or create database manager"""
        if self._database_manager is None:
            logger.info("Creating database manager")
            self._database_manager = DatabaseManager(self.database_url)
        return self._database_manager

    @property
    def read_model(self) -> PostgreSQLReadModel:
        """Get or create read model"""
        if self._read_model is None:
            logger.info("Creating read model")
            self._read_model = PostgreSQLReadModel(self.database_manager)
        return self._read_model

    @property
    def salesforce_client(self) -> Optional[Any]:
        """Get Salesforce client (returns None if not configured)"""
        # In a real implementation, this would create and configure a Salesforce client
        # For now, return None to indicate it's not available
        return self._salesforce_client

    @property
    def provider_factory(self) -> CRMProviderFactory:
        """Get or create provider factory"""
        if self._provider_factory is None:
            logger.info("Creating provider factory")
            self._provider_factory = CRMProviderFactory()

            # Register available providers
            self._provider_factory.register_provider(
                "salesforce", SalesforceProvider
            )

            # Set up Salesforce provider with client
            if self.salesforce_client:
                salesforce_provider = self._provider_factory.create_provider(
                    "salesforce", {}
                )
                salesforce_provider.set_client(self.salesforce_client)

        return self._provider_factory

    @property
    def event_handler(self) -> Any:
        """Get or create event handler"""
        if self._event_handler is None:
            logger.info("Creating event handler")
            # Dynamic import to avoid circular dependency
            from event_sourcing.application.events.event_handler import (
                CeleryEventHandler,
            )

            # Create task registry with available Celery tasks
            task_registry = self._create_task_registry()

            self._event_handler = CeleryEventHandler(task_registry)
        return self._event_handler

    def _create_task_registry(self) -> Dict[str, Any]:
        """Create registry of available Celery tasks"""
        try:
            # Dynamic import to avoid circular dependency
            from event_sourcing.application.tasks.process_crm_event import (
                process_crm_event_task,
            )
            from event_sourcing.application.tasks.process_projection import (
                process_projection_task,
            )
            from event_sourcing.application.tasks.publish_snapshot import (
                publish_snapshot_task,
            )

            return {
                "process_crm_event": process_crm_event_task,
                "process_projection": process_projection_task,
                "publish_snapshot": publish_snapshot_task,
            }
        except ImportError as e:
            logger.warning(f"Could not import Celery tasks: {e}")
            return {}

    @property
    def projection_manager(self) -> Any:
        """Get or create projection manager"""
        if self._projection_manager is None:
            logger.info("Creating projection manager")
            # Dynamic import to avoid circular dependency
            from event_sourcing.application.projections.projection_manager_interface import (
                GenericProjectionManager,
            )

            # Create generic projection manager with event handler
            projection_manager = GenericProjectionManager(self.event_handler)

            # Register projection handlers for different event types
            projection_manager.register_projection_handler(
                "client.CLIENT_CREATED", "process_client_created_projection"
            )
            projection_manager.register_projection_handler(
                "client.CLIENT_UPDATED", "process_client_updated_projection"
            )
            projection_manager.register_projection_handler(
                "client.CLIENT_DELETED", "process_client_deleted_projection"
            )

            self._projection_manager = projection_manager
        return self._projection_manager

    @property
    def event_store(self) -> PostgreSQLEventStore:
        """Get or create event store with projection manager"""
        if self._event_store is None:
            logger.info("Creating event store with projection manager")
            self._event_store = PostgreSQLEventStore(
                self.database_manager, self.projection_manager
            )
        return self._event_store

    @property
    def event_publisher(self) -> EventBridgePublisher:
        """Get or create event publisher"""
        if self._event_publisher is None:
            logger.info("Creating event publisher")
            self._event_publisher = EventBridgePublisher(
                self.eventbridge_region
            )
        return self._event_publisher

    # Command Handler Factory Methods
    def create_process_crm_event_command_handler(self) -> Any:
        """Create ProcessCRMEventCommandHandler with all dependencies"""
        logger.info("Creating ProcessCRMEventCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.process_crm_event import (
            ProcessCRMEventCommandHandler,
        )

        return ProcessCRMEventCommandHandler(
            event_store=self.event_store,
            provider_factory=self.provider_factory,
            provider_config={},  # Empty config for now
        )

    def create_backfill_entity_type_command_handler(self) -> Any:
        """Create BackfillEntityTypeCommandHandler (no dependencies needed)"""
        logger.info("Creating BackfillEntityTypeCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.backfill_entity_type import (
            BackfillEntityTypeCommandHandler,
        )

        return BackfillEntityTypeCommandHandler()

    def create_backfill_specific_entity_command_handler(self) -> Any:
        """Create BackfillSpecificEntityCommandHandler (no dependencies needed)"""
        logger.info("Creating BackfillSpecificEntityCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.backfill_specific_entity import (
            BackfillSpecificEntityCommandHandler,
        )

        return BackfillSpecificEntityCommandHandler()

    # Query Handler Factory Methods
    def create_get_client_query_handler(self) -> Any:
        """Create GetClientQueryHandler with read model dependency"""
        logger.info("Creating GetClientQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.get_client import (
            GetClientQueryHandler,
        )

        return GetClientQueryHandler(read_model=self.read_model)

    def create_search_clients_query_handler(self) -> Any:
        """Create SearchClientsQueryHandler with read model dependency"""
        logger.info("Creating SearchClientsQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.search_clients import (
            SearchClientsQueryHandler,
        )

        return SearchClientsQueryHandler(read_model=self.read_model)

    def create_get_client_history_query_handler(self) -> Any:
        """Create GetClientHistoryQueryHandler with event store dependency"""
        logger.info("Creating GetClientHistoryQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.get_client_history import (
            GetClientHistoryQueryHandler,
        )

        return GetClientHistoryQueryHandler(event_store=self.event_store)

    def create_get_backfill_status_query_handler(self) -> Any:
        """Create GetBackfillStatusQueryHandler with read model dependency"""
        logger.info("Creating GetBackfillStatusQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.get_backfill_status import (
            GetBackfillStatusQueryHandler,
        )

        return GetBackfillStatusQueryHandler(read_model=self.read_model)

    async def close(self) -> None:
        """Close all infrastructure components"""
        logger.info("Closing infrastructure components")

        if self._database_manager:
            await self._database_manager.close()
            self._database_manager = None

        self._event_store = None
        self._read_model = None
        self._event_publisher = None
        self._projection_manager = None
        self._event_handler = None

        logger.info("Infrastructure components closed")
