import logging
from typing import Any, Dict, Optional

from event_sourcing.infrastructure.database.session import DatabaseManager
from event_sourcing.infrastructure.event_store import PostgreSQLEventStore
from event_sourcing.infrastructure.messaging import EventBridgePublisher
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
    def event_handler(self) -> Any:
        """Get or create event handler"""
        if self._event_handler is None:
            logger.info("Creating event handler")
            # Dynamic import to avoid circular dependency
            from event_sourcing.application.events.handlers import (
                CeleryEventHandler,
            )

            # Create task registry with available Celery tasks
            task_registry = self._create_task_registry()

            self._event_handler = CeleryEventHandler(task_registry)
        return self._event_handler

    def _create_task_registry(self) -> Dict[str, Any]:
        """Create registry of available Celery tasks"""
        try:
            # Return task names as strings instead of function objects
            return {
                "USER_CREATED": ["process_user_created_task"],
                "USER_UPDATED": ["process_user_updated_task"],
                "USER_DELETED": ["process_user_deleted_task"],
                "USERNAME_CHANGED": ["process_username_changed_task"],
                "PASSWORD_CHANGED": ["process_password_changed_task"],
                "PASSWORD_RESET_REQUESTED": [
                    "process_password_reset_requested_task"
                ],
                "PASSWORD_RESET_COMPLETED": [
                    "process_password_reset_completed_task"
                ],
            }
        except ImportError as e:
            logger.warning(f"Could not import user tasks: {e}")
            return {}

    @property
    def event_store(self) -> PostgreSQLEventStore:
        """Get or create event store"""
        if self._event_store is None:
            logger.info("Creating event store")
            self._event_store = PostgreSQLEventStore(self.database_manager)
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

    # User Command Handler Factory Methods
    def create_create_user_command_handler(self) -> Any:
        """Create CreateUserCommandHandler with all dependencies"""
        logger.info("Creating CreateUserCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.user import (
            CreateUserCommandHandler,
        )

        return CreateUserCommandHandler(
            event_store=self.event_store,
            event_handler=self.event_handler,
        )

    def create_update_user_command_handler(self) -> Any:
        """Create UpdateUserCommandHandler with all dependencies"""
        logger.info("Creating UpdateUserCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.user import (
            UpdateUserCommandHandler,
        )

        return UpdateUserCommandHandler(
            event_store=self.event_store,
            event_handler=self.event_handler,
        )

    def create_change_username_command_handler(self) -> Any:
        """Create ChangeUsernameCommandHandler with all dependencies"""
        logger.info("Creating ChangeUsernameCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.user import (
            ChangeUsernameCommandHandler,
        )

        return ChangeUsernameCommandHandler(
            event_store=self.event_store,
            event_handler=self.event_handler,
        )

    def create_change_password_command_handler(self) -> Any:
        """Create ChangePasswordCommandHandler with all dependencies"""
        logger.info("Creating ChangePasswordCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.user import (
            ChangePasswordCommandHandler,
        )

        return ChangePasswordCommandHandler(
            event_store=self.event_store,
            event_handler=self.event_handler,
        )

    def create_request_password_reset_command_handler(self) -> Any:
        """Create RequestPasswordResetCommandHandler with all dependencies"""
        logger.info("Creating RequestPasswordResetCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.user import (
            RequestPasswordResetCommandHandler,
        )

        return RequestPasswordResetCommandHandler(
            event_store=self.event_store,
            event_handler=self.event_handler,
        )

    def create_complete_password_reset_command_handler(self) -> Any:
        """Create CompletePasswordResetCommandHandler with all dependencies"""
        logger.info("Creating CompletePasswordResetCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.user import (
            CompletePasswordResetCommandHandler,
        )

        return CompletePasswordResetCommandHandler(
            event_store=self.event_store,
            event_handler=self.event_handler,
        )

    def create_delete_user_command_handler(self) -> Any:
        """Create DeleteUserCommandHandler with all dependencies"""
        logger.info("Creating DeleteUserCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.user import (
            DeleteUserCommandHandler,
        )

        return DeleteUserCommandHandler(
            event_store=self.event_store,
            event_handler=self.event_handler,
        )

    # User Projection Factory Methods
    def create_user_created_projection(self) -> Any:
        """Create UserCreatedProjection with read model dependency"""
        logger.info("Creating UserCreatedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserCreatedProjection,
        )

        return UserCreatedProjection(read_model=self.read_model)

    def create_user_updated_projection(self) -> Any:
        """Create UserUpdatedProjection with read model dependency"""
        logger.info("Creating UserUpdatedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserUpdatedProjection,
        )

        return UserUpdatedProjection(read_model=self.read_model)

    def create_user_deleted_projection(self) -> Any:
        """Create UserDeletedProjection with read model dependency"""
        logger.info("Creating UserDeletedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserDeletedProjection,
        )

        return UserDeletedProjection(read_model=self.read_model)

    def create_username_changed_projection(self) -> Any:
        """Create UsernameChangedProjection with read model dependency"""
        logger.info("Creating UsernameChangedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UsernameChangedProjection,
        )

        return UsernameChangedProjection(read_model=self.read_model)

    def create_password_changed_projection(self) -> Any:
        """Create PasswordChangedProjection with read model dependency"""
        logger.info("Creating PasswordChangedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            PasswordChangedProjection,
        )

        return PasswordChangedProjection(read_model=self.read_model)

    def create_password_reset_requested_projection(self) -> Any:
        """Create PasswordResetRequestedProjection with read model dependency"""
        logger.info("Creating PasswordResetRequestedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            PasswordResetRequestedProjection,
        )

        return PasswordResetRequestedProjection(read_model=self.read_model)

    def create_password_reset_completed_projection(self) -> Any:
        """Create PasswordResetCompletedProjection with read model dependency"""
        logger.info("Creating PasswordResetCompletedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            PasswordResetCompletedProjection,
        )

        return PasswordResetCompletedProjection(read_model=self.read_model)

    # User Query Handler Factory Methods
    def create_get_user_query_handler(self) -> Any:
        """Create GetUserQueryHandler with read model dependency"""
        logger.info("Creating GetUserQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.user import (
            GetUserQueryHandler,
        )

        return GetUserQueryHandler(read_model=self.read_model)

    def create_get_user_history_query_handler(self) -> Any:
        """Create GetUserHistoryQueryHandler with event store dependency"""
        logger.info("Creating GetUserHistoryQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.user import (
            GetUserHistoryQueryHandler,
        )

        return GetUserHistoryQueryHandler(event_store=self.event_store)

    # Legacy methods for backward compatibility
    def create_process_crm_event_command_handler(self) -> Any:
        """Legacy method - now redirects to user handlers"""
        logger.warning(
            "ProcessCRMEventCommandHandler is deprecated, use user handlers instead"
        )
        return self.create_create_user_command_handler()

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

    # Query Handler Factory Methods (legacy - will be updated for users)
    def create_get_client_query_handler(self) -> Any:
        """Legacy method - placeholder for user queries"""
        logger.warning(
            "GetClientQueryHandler is deprecated, use user queries instead"
        )
        return None

    def create_search_clients_query_handler(self) -> Any:
        """Legacy method - placeholder for user queries"""
        logger.warning(
            "SearchClientsQueryHandler is deprecated, use user queries instead"
        )
        return None

    def create_get_client_history_query_handler(self) -> Any:
        """Legacy method - placeholder for user queries"""
        logger.warning(
            "GetClientHistoryQueryHandler is deprecated, use user queries instead"
        )
        return None

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
        self._event_handler = None

        logger.info("Infrastructure components closed")
