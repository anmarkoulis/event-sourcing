"""Factory for creating infrastructure components, command handlers, and query handlers."""

import logging
from typing import Any, Dict, Optional

from event_sourcing.infrastructure.database.session import DatabaseManager
from event_sourcing.infrastructure.event_store import PostgreSQLEventStore
from event_sourcing.infrastructure.providers.email import (
    EmailProviderFactory,
    LoggingEmailProvider,
)
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

from .command_handler_wrapper import CommandHandlerWrapper
from .projection_wrapper import ProjectionWrapper
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class InfrastructureFactory:
    """Factory for creating infrastructure components, command handlers, and query handlers."""

    def __init__(self, database_url: str) -> None:
        """Initialize InfrastructureFactory.

        :param database_url: Database connection URL.
        """
        self.database_url = database_url
        self._database_manager: Optional[DatabaseManager] = None
        self._event_handler: Optional[Any] = None
        self._session_manager: Optional[SessionManager] = None

        # Initialize email providers
        self._initialize_email_providers()

    @property
    def database_manager(self) -> DatabaseManager:
        """Get or create database manager.

        :return: Database manager instance.
        """
        if self._database_manager is None:
            logger.info("Creating database manager")
            self._database_manager = DatabaseManager(self.database_url)
        return self._database_manager

    @property
    def session_manager(self) -> SessionManager:
        """Get or create session manager.

        :return: Session manager instance.
        """
        if self._session_manager is None:
            self._session_manager = SessionManager(self.database_manager)
        return self._session_manager

    @property
    def event_handler(self) -> Any:
        """Get or create event handler.

        :return: Event handler instance.
        """
        if self._event_handler is None:
            logger.info("Creating event handler")
            # Dynamic import to avoid circular dependency
            from event_sourcing.application.events.handlers import (
                CeleryEventHandler,
                SyncEventHandler,
            )
            from event_sourcing.config.settings import settings

            if settings.SYNC_EVENT_HANDLER:
                self._event_handler = SyncEventHandler(self)
            else:
                self._event_handler = CeleryEventHandler()
        return self._event_handler

    def _initialize_email_providers(self) -> None:
        """Initialize email providers by registering them with the factory."""
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
        """Create CreateUserCommandHandler with all dependencies.

        :return: Wrapped command handler.
        """
        logger.info("Creating CreateUserCommandHandler")
        from event_sourcing.application.commands.handlers.user import (
            CreateUserCommandHandler,
        )

        return CommandHandlerWrapper(self, CreateUserCommandHandler)

    def create_update_user_command_handler(self) -> Any:
        """Create UpdateUserCommandHandler with all dependencies.

        :return: Wrapped command handler.
        """
        logger.info("Creating UpdateUserCommandHandler")
        from event_sourcing.application.commands.handlers.user import (
            UpdateUserCommandHandler,
        )

        return CommandHandlerWrapper(self, UpdateUserCommandHandler)

    def create_change_password_command_handler(self) -> Any:
        """Create ChangePasswordCommandHandler with all dependencies.

        :return: Wrapped command handler.
        """
        logger.info("Creating ChangePasswordCommandHandler")
        from event_sourcing.application.commands.handlers.user import (
            ChangePasswordCommandHandler,
        )

        return CommandHandlerWrapper(self, ChangePasswordCommandHandler)

    def create_delete_user_command_handler(self) -> Any:
        """Create DeleteUserCommandHandler with all dependencies.

        :return: Wrapped command handler.
        """
        logger.info("Creating DeleteUserCommandHandler")
        from event_sourcing.application.commands.handlers.user import (
            DeleteUserCommandHandler,
        )

        return CommandHandlerWrapper(self, DeleteUserCommandHandler)

    def create_user_created_projection(self) -> Any:
        """Create UserCreatedProjection with read model dependency.

        :return: Wrapped projection.
        """
        logger.info("Creating UserCreatedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserCreatedProjection,
        )

        return ProjectionWrapper(self, UserCreatedProjection)

    def create_user_updated_projection(self) -> Any:
        """Create UserUpdatedProjection with read model dependency.

        :return: Wrapped projection.
        """
        logger.info("Creating UserUpdatedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserUpdatedProjection,
        )

        return ProjectionWrapper(self, UserUpdatedProjection)

    def create_user_deleted_projection(self) -> Any:
        """Create UserDeletedProjection with read model dependency.

        :return: Wrapped projection.
        """
        logger.info("Creating UserDeletedProjection")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.projections.user import (
            UserDeletedProjection,
        )

        return ProjectionWrapper(self, UserDeletedProjection)

    def create_user_created_email_projection(self) -> Any:
        """Create UserCreatedEmailProjection with email provider dependency.

        :return: Email projection instance.
        """
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

    def create_get_user_query_handler(self) -> Any:
        """Create GetUserQueryHandler with read model dependency.

        :return: Wrapped query handler.
        """
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
                """Create a fresh session and handler for this operation.

                :return: Tuple of (query_handler, session).
                """
                session = await self.factory.session_manager.get_session()
                read_model = PostgreSQLReadModel(session)
                query_handler = GetUserQueryHandler(read_model=read_model)
                return query_handler, session

            async def handle(self, query: Any) -> Any:
                """Handle the query with proper session management.

                :param query: Query to handle.
                :return: Result from query handler.
                """
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
        """Create GetUserHistoryQueryHandler with event store dependency.

        :return: Wrapped query handler.
        """
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
                """Create a fresh session and handler for this operation.

                :return: Tuple of (query_handler, session).
                """
                session = await self.factory.session_manager.get_session()
                event_store = PostgreSQLEventStore(session)
                query_handler = GetUserHistoryQueryHandler(
                    event_store=event_store
                )
                return query_handler, session

            async def handle(self, query: Any) -> Any:
                """Handle the query with proper session management.

                :param query: Query to handle.
                :return: Result from query handler.
                """
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
        """Create ListUsersQueryHandler with read model dependency.

        :return: Wrapped query handler.
        """
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
                """Create a fresh session and handler for this operation.

                :return: Tuple of (query_handler, session).
                """
                session = await self.factory.session_manager.get_session()
                read_model = PostgreSQLReadModel(session)
                query_handler = ListUsersQueryHandler(read_model=read_model)
                return query_handler, session

            async def handle(self, query: Any) -> Any:
                """Handle the query with proper session management.

                :param query: Query to handle.
                :return: Result from query handler.
                """
                (
                    query_handler,
                    session,
                ) = await self._create_handler_with_session()
                try:
                    return await query_handler.handle(query)
                finally:
                    await session.close()

        return QueryHandlerWrapper(self)

    def create_process_crm_event_command_handler(self) -> Any:
        """Legacy method - now redirects to user handlers.

        :return: Wrapped command handler.
        """
        logger.warning(
            "ProcessCRMEventCommandHandler is deprecated, use user handlers instead"
        )
        return self.create_create_user_command_handler()

    def create_backfill_entity_type_command_handler(self) -> Any:
        """Create BackfillEntityTypeCommandHandler (no dependencies needed).

        :return: Command handler instance.
        """
        logger.info("Creating BackfillEntityTypeCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.backfill_entity_type import (
            BackfillEntityTypeCommandHandler,
        )

        return BackfillEntityTypeCommandHandler()

    def create_backfill_specific_entity_command_handler(self) -> Any:
        """Create BackfillSpecificEntityCommandHandler (no dependencies needed).

        :return: Command handler instance.
        """
        logger.info("Creating BackfillSpecificEntityCommandHandler")
        # Dynamic import to avoid circular dependency
        from event_sourcing.application.commands.handlers.backfill_specific_entity import (
            BackfillSpecificEntityCommandHandler,
        )

        return BackfillSpecificEntityCommandHandler()

    def create_get_client_query_handler(self) -> Any:
        """Legacy method - placeholder for user queries.

        :return: None (deprecated).
        """
        logger.warning(
            "GetClientQueryHandler is deprecated, use user queries instead"
        )
        return None

    def create_search_clients_query_handler(self) -> Any:
        """Legacy method - placeholder for user queries.

        :return: None (deprecated).
        """
        logger.warning(
            "SearchClientsQueryHandler is deprecated, use user queries instead"
        )
        return None

    def create_get_client_history_query_handler(self) -> Any:
        """Legacy method - placeholder for user queries.

        :return: None (deprecated).
        """
        logger.warning(
            "GetClientHistoryQueryHandler is deprecated, use user queries instead"
        )
        return None

    @property
    def auth_service(self) -> Any:
        """Get or create authentication service.

        :return: Authentication service instance.
        """
        if not hasattr(self, "_auth_service"):
            logger.info("Creating auth service")

            logger.info("Using JWT authentication service")
            from event_sourcing.infrastructure.security import (
                BcryptHashingService,
                JWTAuthService,
            )

            # Create hashing service for JWT auth
            hashing_service = BcryptHashingService()

            # Create JWT auth service with factory reference
            # The auth service will get the event store when needed
            self._auth_service = JWTAuthService(None, hashing_service)

            # Store factory reference for dynamic event store creation
            self._auth_service._factory = self

        return self._auth_service

    async def close(self) -> None:
        """Close all infrastructure components."""
        logger.info("Closing infrastructure components")

        if self._database_manager:
            await self._database_manager.close()
            self._database_manager = None
        self._event_handler = None
        self._session_manager = None

        logger.info("Infrastructure components closed")
