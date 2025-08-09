import logging
from typing import Any, Dict, Optional, Type

from event_sourcing.infrastructure.database.session import DatabaseManager
from event_sourcing.infrastructure.event_store import PostgreSQLEventStore
from event_sourcing.infrastructure.providers.email import (
    EmailProviderFactory,
    LoggingEmailProvider,
)
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel
from event_sourcing.infrastructure.unit_of_work import SQLAUnitOfWork

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages database session creation and lifecycle"""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager = database_manager
        self._session: Optional[Any] = None

    async def get_session(self) -> Any:
        """Get or create a database session"""
        if self._session is None:
            self._session = await self.database_manager.get_session()
        return self._session

    async def close_session(self) -> None:
        """Close the current session"""
        if self._session:
            await self._session.close()
            self._session = None


class CommandHandlerWrapper:
    """Wrapper that manages session creation for command handlers"""

    def __init__(
        self, factory: "InfrastructureFactory", handler_class: Type
    ) -> None:
        self.factory = factory
        self.handler_class = handler_class

    async def _create_handler_with_session(self) -> tuple[Any, Any]:
        """Create a fresh session and handler for this operation"""
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

        command_handler = self.handler_class(**ctor_kwargs)
        return command_handler, session

    async def handle(self, command: Any) -> Any:
        """Handle the command with proper session management"""
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


class ProjectionWrapper:
    """Wrapper that manages session creation for projections"""

    def __init__(
        self, factory: "InfrastructureFactory", projection_class: Type
    ) -> None:
        self.factory = factory
        self.projection_class = projection_class

    async def _create_projection_with_session(self) -> tuple[Any, Any]:
        """Create a fresh session and projection for this operation"""
        session = await self.factory.session_manager.get_session()
        read_model = PostgreSQLReadModel(session)

        # Check if the projection class expects unit_of_work parameter
        import inspect

        sig = inspect.signature(self.projection_class.__init__)
        if "unit_of_work" in sig.parameters:
            uow = SQLAUnitOfWork(session)
            projection = self.projection_class(
                read_model=read_model,
                unit_of_work=uow,
            )
        else:
            projection = self.projection_class(read_model=read_model)

        return projection, session

    async def handle(self, event: Any) -> Any:
        """Handle the event with proper session management"""
        projection, session = await self._create_projection_with_session()
        try:
            # The projection will handle its own transaction via Unit of Work
            return await projection.handle(event)
        finally:
            # Session is managed by the Unit of Work, just close it
            await session.close()


class InfrastructureFactory:
    """Factory for creating infrastructure components, command handlers, and query handlers"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._database_manager: Optional[DatabaseManager] = None
        self._event_handler: Optional[Any] = None
        self._session_manager: Optional[SessionManager] = None

        # Initialize email providers
        self._initialize_email_providers()

    @property
    def database_manager(self) -> DatabaseManager:
        """Get or create database manager"""
        if self._database_manager is None:
            logger.info("Creating database manager")
            self._database_manager = DatabaseManager(self.database_url)
        return self._database_manager

    @property
    def session_manager(self) -> SessionManager:
        """Get or create session manager"""
        if self._session_manager is None:
            self._session_manager = SessionManager(self.database_manager)
        return self._session_manager

    @property
    def event_handler(self) -> Any:
        """Get or create event handler"""
        if self._event_handler is None:
            logger.info("Creating event handler")
            # Dynamic import to avoid circular dependency
            from event_sourcing.application.events.handlers import (
                CeleryEventHandler,
            )

            self._event_handler = CeleryEventHandler()
        return self._event_handler

    def _initialize_email_providers(self) -> None:
        """Initialize email providers by registering them with the factory"""
        logger.info("Initializing email providers")
        EmailProviderFactory.register_provider("logging", LoggingEmailProvider)

    def create_email_provider(
        self,
        provider_name: str = "logging",
        config: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Create an email provider instance.

        :param provider_name: Name of the email provider to create.
        :param config: Optional configuration for the provider.
        :return: Email provider instance.
        """
        logger.info(f"Creating email provider: {provider_name}")
        return EmailProviderFactory.create_provider(
            provider_name, config or {}
        )

    def create_create_user_command_handler(self) -> Any:
        """Create CreateUserCommandHandler with all dependencies"""
        logger.info("Creating CreateUserCommandHandler")
        from event_sourcing.application.commands.handlers.user import (
            CreateUserCommandHandler,
        )

        return CommandHandlerWrapper(self, CreateUserCommandHandler)

    def create_update_user_command_handler(self) -> Any:
        """Create UpdateUserCommandHandler with all dependencies"""
        logger.info("Creating UpdateUserCommandHandler")
        from event_sourcing.application.commands.handlers.user import (
            UpdateUserCommandHandler,
        )

        return CommandHandlerWrapper(self, UpdateUserCommandHandler)

    # Removed: create_change_username_command_handler

    def create_change_password_command_handler(self) -> Any:
        """Create ChangePasswordCommandHandler with all dependencies"""
        logger.info("Creating ChangePasswordCommandHandler")
        from event_sourcing.application.commands.handlers.user import (
            ChangePasswordCommandHandler,
        )

        return CommandHandlerWrapper(self, ChangePasswordCommandHandler)

    def create_delete_user_command_handler(self) -> Any:
        """Create DeleteUserCommandHandler with all dependencies"""
        logger.info("Creating DeleteUserCommandHandler")
        from event_sourcing.application.commands.handlers.user import (
            DeleteUserCommandHandler,
        )

        return CommandHandlerWrapper(self, DeleteUserCommandHandler)

    # Removed: create_request_password_reset_command_handler

    # Removed: create_complete_password_reset_command_handler

    # User Projection Factory Methods
    def create_user_created_projection(self) -> Any:
        """Create UserCreatedProjection with read model dependency"""
        logger.info("Creating UserCreatedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserCreatedProjection,
        )

        return ProjectionWrapper(self, UserCreatedProjection)

    def create_user_updated_projection(self) -> Any:
        """Create UserUpdatedProjection with read model dependency"""
        logger.info("Creating UserUpdatedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserUpdatedProjection,
        )

        return ProjectionWrapper(self, UserUpdatedProjection)

    def create_user_deleted_projection(self) -> Any:
        """Create UserDeletedProjection with read model dependency"""
        logger.info("Creating UserDeletedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserDeletedProjection,
        )

        return ProjectionWrapper(self, UserDeletedProjection)

    # Removed: create_username_changed_projection

    def create_password_changed_projection(self) -> Any:
        """Create PasswordChangedProjection with read model dependency"""
        logger.info("Creating PasswordChangedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            PasswordChangedProjection,
        )

        return ProjectionWrapper(self, PasswordChangedProjection)

    # Removed: create_password_reset_requested_projection

    # Removed: create_password_reset_completed_projection

    def create_user_created_email_projection(self) -> Any:
        """Create UserCreatedEmailProjection with email provider dependency"""
        logger.info("Creating UserCreatedEmailProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserCreatedEmailProjection,
        )

        # Create email provider
        email_provider = self.create_email_provider()

        # Create projection with email provider
        projection = UserCreatedEmailProjection(email_provider=email_provider)
        return projection

    # User Query Handler Factory Methods
    def create_get_user_query_handler(self) -> Any:
        """Create GetUserQueryHandler with read model dependency"""
        logger.info("Creating GetUserQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.user import (
            GetUserQueryHandler,
        )

        # Create a wrapper that manages session creation
        class QueryHandlerWrapper:
            def __init__(self, factory: InfrastructureFactory) -> None:
                self.factory = factory

            async def _create_handler_with_session(self) -> tuple[Any, Any]:
                """Create a fresh session and handler for this operation"""
                session = await self.factory.session_manager.get_session()
                read_model = PostgreSQLReadModel(session)
                query_handler = GetUserQueryHandler(read_model=read_model)
                return query_handler, session

            async def handle(self, query: Any) -> Any:
                """Handle the query with proper session management"""
                (
                    query_handler,
                    session,
                ) = await self._create_handler_with_session()
                try:
                    return await query_handler.handle(query)
                finally:
                    await session.close()

        return QueryHandlerWrapper(self)

    def create_get_user_history_query_handler(self) -> Any:
        """Create GetUserHistoryQueryHandler with event store dependency"""
        logger.info("Creating GetUserHistoryQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.user import (
            GetUserHistoryQueryHandler,
        )

        # Create a wrapper that manages session creation
        class QueryHandlerWrapper:
            def __init__(self, factory: InfrastructureFactory) -> None:
                self.factory = factory

            async def _create_handler_with_session(self) -> tuple[Any, Any]:
                """Create a fresh session and handler for this operation"""
                session = await self.factory.session_manager.get_session()
                event_store = PostgreSQLEventStore(session)
                query_handler = GetUserHistoryQueryHandler(
                    event_store=event_store
                )
                return query_handler, session

            async def handle(self, query: Any) -> Any:
                """Handle the query with proper session management"""
                (
                    query_handler,
                    session,
                ) = await self._create_handler_with_session()
                try:
                    return await query_handler.handle(query)
                finally:
                    await session.close()

        return QueryHandlerWrapper(self)

    def create_list_users_query_handler(self) -> Any:
        """Create ListUsersQueryHandler with read model dependency"""
        logger.info("Creating ListUsersQueryHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.queries.handlers.user import (
            ListUsersQueryHandler,
        )

        # Create a wrapper that manages session creation
        class QueryHandlerWrapper:
            def __init__(self, factory: InfrastructureFactory) -> None:
                self.factory = factory

            async def _create_handler_with_session(self) -> tuple[Any, Any]:
                """Create a fresh session and handler for this operation"""
                session = await self.factory.session_manager.get_session()
                read_model = PostgreSQLReadModel(session)
                query_handler = ListUsersQueryHandler(read_model=read_model)
                return query_handler, session

            async def handle(self, query: Any) -> Any:
                """Handle the query with proper session management"""
                (
                    query_handler,
                    session,
                ) = await self._create_handler_with_session()
                try:
                    return await query_handler.handle(query)
                finally:
                    await session.close()

        return QueryHandlerWrapper(self)

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

    async def close(self) -> None:
        """Close all infrastructure components"""
        logger.info("Closing infrastructure components")

        if self._database_manager:
            await self._database_manager.close()
            self._database_manager = None
        self._event_handler = None
        self._session_manager = None

        logger.info("Infrastructure components closed")
