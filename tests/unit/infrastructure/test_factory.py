"""Unit tests for InfrastructureFactory."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from event_sourcing.infrastructure.factory import (
    CommandHandlerWrapper,
    InfrastructureFactory,
    ProjectionWrapper,
    SessionManager,
)


class TestSessionManager:
    """Test cases for SessionManager."""

    @pytest.fixture
    def database_manager_mock(self) -> MagicMock:
        """Provide a mock database manager."""
        mock = MagicMock()
        mock.get_session = AsyncMock()
        return mock

    @pytest.fixture
    def session_manager(
        self, database_manager_mock: MagicMock
    ) -> SessionManager:
        """Provide a SessionManager instance."""
        return SessionManager(database_manager_mock)

    @pytest.fixture
    def session_mock(self) -> MagicMock:
        """Provide a mock database session."""
        mock = MagicMock()
        mock.close = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_init(self, database_manager_mock: MagicMock) -> None:
        """Test SessionManager initialization."""
        session_manager = SessionManager(database_manager_mock)
        assert session_manager.database_manager == database_manager_mock
        assert session_manager._session is None

    @pytest.mark.asyncio
    async def test_get_session_first_time(
        self, session_manager: SessionManager, session_mock: MagicMock
    ) -> None:
        """Test getting session for the first time."""
        session_manager.database_manager.get_session.return_value = (
            session_mock
        )

        result = await session_manager.get_session()

        assert result == session_mock
        session_manager.database_manager.get_session.assert_awaited_once()
        assert session_manager._session == session_mock

    @pytest.mark.asyncio
    async def test_get_session_cached(
        self, session_manager: SessionManager, session_mock: MagicMock
    ) -> None:
        """Test getting cached session."""
        session_manager._session = session_mock

        result = await session_manager.get_session()

        assert result == session_mock
        session_manager.database_manager.get_session.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_session_with_session(
        self, session_manager: SessionManager, session_mock: MagicMock
    ) -> None:
        """Test closing session when session exists."""
        session_manager._session = session_mock

        await session_manager.close_session()

        session_mock.close.assert_awaited_once()
        assert session_manager._session is None

    @pytest.mark.asyncio
    async def test_close_session_no_session(
        self, session_manager: SessionManager
    ) -> None:
        """Test closing session when no session exists."""
        session_manager._session = None

        await session_manager.close_session()

        # Should not raise any errors
        assert session_manager._session is None


class TestCommandHandlerWrapper:
    """Test cases for CommandHandlerWrapper."""

    @pytest.fixture
    def factory_mock(self) -> MagicMock:
        """Provide a mock InfrastructureFactory."""
        mock = MagicMock()
        mock.session_manager.get_session = AsyncMock()
        mock.event_handler = MagicMock()
        return mock

    @pytest.fixture
    def handler_class_mock(self) -> MagicMock:
        """Provide a mock handler class."""
        return MagicMock()

    @pytest.fixture
    def wrapper(
        self, factory_mock: MagicMock, handler_class_mock: MagicMock
    ) -> CommandHandlerWrapper:
        """Provide a CommandHandlerWrapper instance."""
        return CommandHandlerWrapper(factory_mock, handler_class_mock)

    @pytest.fixture
    def session_mock(self) -> MagicMock:
        """Provide a mock database session."""
        return MagicMock()

    @pytest.fixture
    def command_mock(self) -> MagicMock:
        """Provide a mock command."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_init(
        self, factory_mock: MagicMock, handler_class_mock: MagicMock
    ) -> None:
        """Test CommandHandlerWrapper initialization."""
        wrapper = CommandHandlerWrapper(factory_mock, handler_class_mock)
        assert wrapper.factory == factory_mock
        assert wrapper.handler_class == handler_class_mock

    @pytest.mark.asyncio
    @patch("event_sourcing.infrastructure.factory.SQLAUnitOfWork")
    @patch("event_sourcing.infrastructure.factory.PostgreSQLEventStore")
    async def test_create_handler_with_session(
        self,
        postgresql_event_store_mock: MagicMock,
        sqla_uow_mock: MagicMock,
        wrapper: CommandHandlerWrapper,
        session_mock: MagicMock,
    ) -> None:
        """Test creating handler with session."""
        wrapper.factory.session_manager.get_session.return_value = session_mock
        sqla_uow_mock.return_value = MagicMock()
        postgresql_event_store_mock.return_value = MagicMock()

        handler, session = await wrapper._create_handler_with_session()

        assert session == session_mock
        wrapper.factory.session_manager.get_session.assert_awaited_once()
        sqla_uow_mock.assert_called_once_with(session_mock)
        postgresql_event_store_mock.assert_called_once_with(session_mock)

    @pytest.mark.asyncio
    async def test_handle_success(
        self, wrapper: CommandHandlerWrapper, command_mock: MagicMock
    ) -> None:
        """Test successful command handling."""
        handler_mock = MagicMock()
        handler_mock.handle = AsyncMock(return_value="success")
        session_mock = MagicMock()
        session_mock.close = AsyncMock()

        wrapper._create_handler_with_session = AsyncMock(
            return_value=(handler_mock, session_mock)
        )

        result = await wrapper.handle(command_mock)

        assert result == "success"
        handler_mock.handle.assert_awaited_once_with(command_mock)
        session_mock.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_error(
        self, wrapper: CommandHandlerWrapper, command_mock: MagicMock
    ) -> None:
        """Test command handling with error."""
        handler_mock = MagicMock()
        error = ValueError("Test error")
        handler_mock.handle = AsyncMock(side_effect=error)
        session_mock = MagicMock()
        session_mock.close = AsyncMock()

        wrapper._create_handler_with_session = AsyncMock(
            return_value=(handler_mock, session_mock)
        )

        with pytest.raises(ValueError, match="Test error"):
            await wrapper.handle(command_mock)

        session_mock.close.assert_awaited_once()


class TestProjectionWrapper:
    """Test cases for ProjectionWrapper."""

    @pytest.fixture
    def factory_mock(self) -> MagicMock:
        """Provide a mock InfrastructureFactory."""
        mock = MagicMock()
        mock.session_manager.get_session = AsyncMock()
        return mock

    @pytest.fixture
    def projection_class_mock(self) -> MagicMock:
        """Provide a mock projection class."""
        return MagicMock()

    @pytest.fixture
    def wrapper(
        self, factory_mock: MagicMock, projection_class_mock: MagicMock
    ) -> ProjectionWrapper:
        """Provide a ProjectionWrapper instance."""
        return ProjectionWrapper(factory_mock, projection_class_mock)

    @pytest.fixture
    def event_mock(self) -> MagicMock:
        """Provide a mock event."""
        return MagicMock()

    @pytest.fixture
    def session_mock(self) -> MagicMock:
        """Provide a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_init(
        self, factory_mock: MagicMock, projection_class_mock: MagicMock
    ) -> None:
        """Test ProjectionWrapper initialization."""
        wrapper = ProjectionWrapper(factory_mock, projection_class_mock)
        assert wrapper.factory == factory_mock
        assert wrapper.projection_class == projection_class_mock

    @pytest.mark.asyncio
    @patch("event_sourcing.infrastructure.factory.PostgreSQLReadModel")
    @patch("event_sourcing.infrastructure.factory.SQLAUnitOfWork")
    async def test_create_projection_with_session_with_uow(
        self,
        sqla_uow_mock: MagicMock,
        postgresql_read_model_mock: MagicMock,
        wrapper: ProjectionWrapper,
        session_mock: MagicMock,
    ) -> None:
        """Test creating projection with session when UoW is expected."""
        wrapper.factory.session_manager.get_session.return_value = session_mock
        postgresql_read_model_mock.return_value = MagicMock()
        sqla_uow_mock.return_value = MagicMock()

        # Mock inspect.signature to return parameters including unit_of_work
        with patch("builtins.__import__") as import_mock:
            inspect_mock = MagicMock()
            sig_mock = MagicMock()
            sig_mock.parameters = {
                "read_model": MagicMock(),
                "unit_of_work": MagicMock(),
            }
            inspect_mock.signature.return_value = sig_mock
            import_mock.return_value = inspect_mock

            (
                projection,
                session,
            ) = await wrapper._create_projection_with_session()

        assert session == session_mock
        wrapper.factory.session_manager.get_session.assert_awaited_once()
        postgresql_read_model_mock.assert_called_once_with(session_mock)
        sqla_uow_mock.assert_called_once_with(session_mock)

    @pytest.mark.asyncio
    @patch("event_sourcing.infrastructure.factory.PostgreSQLReadModel")
    async def test_create_projection_with_session_without_uow(
        self,
        postgresql_read_model_mock: MagicMock,
        wrapper: ProjectionWrapper,
        session_mock: MagicMock,
    ) -> None:
        """Test creating projection with session when UoW is not expected."""
        wrapper.factory.session_manager.get_session.return_value = session_mock
        postgresql_read_model_mock.return_value = MagicMock()

        # Mock inspect.signature to return parameters excluding unit_of_work
        with patch("builtins.__import__") as import_mock:
            inspect_mock = MagicMock()
            sig_mock = MagicMock()
            sig_mock.parameters = {"read_model": MagicMock()}
            inspect_mock.signature.return_value = sig_mock
            import_mock.return_value = inspect_mock

            (
                projection,
                session,
            ) = await wrapper._create_projection_with_session()

        assert session == session_mock
        wrapper.factory.session_manager.get_session.assert_awaited_once()
        postgresql_read_model_mock.assert_called_once_with(session_mock)

    @pytest.mark.asyncio
    async def test_handle_success(
        self, wrapper: ProjectionWrapper, event_mock: MagicMock
    ) -> None:
        """Test successful event handling."""
        projection_mock = MagicMock()
        projection_mock.handle = AsyncMock(return_value="success")
        session_mock = MagicMock()
        session_mock.close = AsyncMock()

        wrapper._create_projection_with_session = AsyncMock(
            return_value=(projection_mock, session_mock)
        )

        result = await wrapper.handle(event_mock)

        assert result == "success"
        projection_mock.handle.assert_awaited_once_with(event_mock)
        session_mock.close.assert_awaited_once()


class TestInfrastructureFactory:
    """Test cases for InfrastructureFactory."""

    @pytest.fixture
    def database_url(self) -> str:
        """Provide a test database URL."""
        return "postgresql://test:test@localhost:5432/testdb"  # pragma: allowlist secret

    @pytest.fixture
    def factory(self, database_url: str) -> InfrastructureFactory:
        """Provide an InfrastructureFactory instance."""
        return InfrastructureFactory(database_url)

    @pytest.fixture
    def session_mock(self) -> MagicMock:
        """Provide a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_init(self, database_url: str) -> None:
        """Test InfrastructureFactory initialization."""
        factory = InfrastructureFactory(database_url)
        assert factory.database_url == database_url
        assert factory._database_manager is None
        assert factory._event_handler is None
        assert factory._session_manager is None

    @pytest.mark.asyncio
    @patch("event_sourcing.infrastructure.factory.DatabaseManager")
    async def test_database_manager_property_first_time(
        self, database_manager_mock: MagicMock, factory: InfrastructureFactory
    ) -> None:
        """Test database_manager property when accessed first time."""
        database_manager_mock.return_value = MagicMock()

        result = factory.database_manager

        database_manager_mock.assert_called_once_with(factory.database_url)
        assert result == database_manager_mock.return_value
        assert factory._database_manager == result

    @pytest.mark.asyncio
    async def test_database_manager_property_cached(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test database_manager property when already cached."""
        cached_manager = MagicMock()
        factory._database_manager = cached_manager

        result = factory.database_manager

        assert result == cached_manager

    @pytest.mark.asyncio
    async def test_session_manager_property_first_time(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test session_manager property when accessed first time."""
        # Mock database_manager property
        mock_db_manager = MagicMock()
        factory._database_manager = mock_db_manager

        result = factory.session_manager

        assert result is not None
        assert result.database_manager == mock_db_manager
        assert factory._session_manager == result

    @pytest.mark.asyncio
    async def test_session_manager_property_cached(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test session_manager property when already cached."""
        cached_session_manager = MagicMock()
        factory._session_manager = cached_session_manager

        result = factory.session_manager

        assert result == cached_session_manager

    @pytest.mark.asyncio
    @patch("builtins.__import__")
    async def test_event_handler_property_first_time(
        self, import_mock: MagicMock, factory: InfrastructureFactory
    ) -> None:
        """Test event_handler property when accessed first time."""
        mock_event_handler = MagicMock()
        import_mock.return_value.CeleryEventHandler = mock_event_handler
        mock_event_handler.return_value = MagicMock()

        result = factory.event_handler

        assert result is not None
        assert factory._event_handler == result

    @pytest.mark.asyncio
    async def test_event_handler_property_cached(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test event_handler property when already cached."""
        cached_event_handler = MagicMock()
        factory._event_handler = cached_event_handler

        result = factory.event_handler

        assert result == cached_event_handler

    @pytest.mark.asyncio
    @patch("event_sourcing.infrastructure.factory.EmailProviderFactory")
    @patch("event_sourcing.infrastructure.factory.LoggingEmailProvider")
    async def test_initialize_email_providers(
        self,
        logging_email_provider_mock: MagicMock,
        email_provider_factory_mock: MagicMock,
        factory: InfrastructureFactory,
    ) -> None:
        """Test email providers initialization."""
        factory._initialize_email_providers()

        email_provider_factory_mock.register_provider.assert_called_once_with(
            "logging", logging_email_provider_mock
        )

    @pytest.mark.asyncio
    @patch("event_sourcing.infrastructure.factory.EmailProviderFactory")
    async def test_create_email_provider(
        self,
        email_provider_factory_mock: MagicMock,
        factory: InfrastructureFactory,
    ) -> None:
        """Test creating email provider."""
        provider_name = "logging"
        config = {"key": "value"}
        mock_provider = MagicMock()
        email_provider_factory_mock.create_provider.return_value = (
            mock_provider
        )

        result = factory.create_email_provider(provider_name, config)

        email_provider_factory_mock.create_provider.assert_called_once_with(
            provider_name, config
        )
        assert result == mock_provider

    @pytest.mark.asyncio
    @patch("event_sourcing.infrastructure.factory.EmailProviderFactory")
    async def test_create_email_provider_default_config(
        self,
        email_provider_factory_mock: MagicMock,
        factory: InfrastructureFactory,
    ) -> None:
        """Test creating email provider with default config."""
        provider_name = "logging"
        mock_provider = MagicMock()
        email_provider_factory_mock.create_provider.return_value = (
            mock_provider
        )

        result = factory.create_email_provider(provider_name)

        email_provider_factory_mock.create_provider.assert_called_once_with(
            provider_name, {}
        )
        assert result == mock_provider

    @pytest.mark.asyncio
    async def test_create_create_user_command_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating CreateUserCommandHandler."""
        result = factory.create_create_user_command_handler()

        assert isinstance(result, CommandHandlerWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    async def test_create_update_user_command_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating UpdateUserCommandHandler."""
        result = factory.create_update_user_command_handler()

        assert isinstance(result, CommandHandlerWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    async def test_create_change_password_command_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating ChangePasswordCommandHandler."""
        result = factory.create_change_password_command_handler()

        assert isinstance(result, CommandHandlerWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    async def test_create_delete_user_command_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating DeleteUserCommandHandler."""
        result = factory.create_delete_user_command_handler()

        assert isinstance(result, CommandHandlerWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    async def test_create_user_created_projection(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating UserCreatedProjection."""
        result = factory.create_user_created_projection()

        assert isinstance(result, ProjectionWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    async def test_create_user_updated_projection(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating UserUpdatedProjection."""
        result = factory.create_user_updated_projection()

        assert isinstance(result, ProjectionWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    async def test_create_user_deleted_projection(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating UserDeletedProjection."""
        result = factory.create_user_deleted_projection()

        assert isinstance(result, ProjectionWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    async def test_create_password_changed_projection(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating PasswordChangedProjection."""
        result = factory.create_password_changed_projection()

        assert isinstance(result, ProjectionWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    async def test_create_user_created_email_projection(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating UserCreatedEmailProjection."""
        with patch.object(
            factory, "create_email_provider"
        ) as mock_create_email:
            mock_email_provider = MagicMock()
            mock_create_email.return_value = mock_email_provider

            result = factory.create_user_created_email_projection()

            # The method calls create_email_provider() without arguments
            mock_create_email.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_create_get_user_query_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating GetUserQueryHandler."""
        result = factory.create_get_user_query_handler()

        assert result is not None
        assert hasattr(result, "handle")
        assert hasattr(result, "_create_handler_with_session")

    @pytest.mark.asyncio
    async def test_create_get_user_history_query_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating GetUserHistoryQueryHandler."""
        result = factory.create_get_user_history_query_handler()

        assert result is not None
        assert hasattr(result, "handle")
        assert hasattr(result, "_create_handler_with_session")

    @pytest.mark.asyncio
    async def test_create_list_users_query_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating ListUsersQueryHandler."""
        result = factory.create_list_users_query_handler()

        assert result is not None
        assert hasattr(result, "handle")
        assert hasattr(result, "_create_handler_with_session")

    @pytest.mark.asyncio
    async def test_create_process_crm_event_command_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating ProcessCRMEventCommandHandler (legacy)."""
        result = factory.create_process_crm_event_command_handler()

        assert isinstance(result, CommandHandlerWrapper)
        assert result.factory == factory

    @pytest.mark.asyncio
    @patch("builtins.__import__")
    async def test_create_backfill_entity_type_command_handler(
        self, import_mock: MagicMock, factory: InfrastructureFactory
    ) -> None:
        """Test creating BackfillEntityTypeCommandHandler."""
        mock_handler = MagicMock()
        import_mock.return_value.BackfillEntityTypeCommandHandler = (
            mock_handler
        )

        result = factory.create_backfill_entity_type_command_handler()

        assert result is not None

    @pytest.mark.asyncio
    @patch("builtins.__import__")
    async def test_create_backfill_specific_entity_command_handler(
        self, import_mock: MagicMock, factory: InfrastructureFactory
    ) -> None:
        """Test creating BackfillSpecificEntityCommandHandler."""
        mock_handler = MagicMock()
        import_mock.return_value.BackfillSpecificEntityCommandHandler = (
            mock_handler
        )

        result = factory.create_backfill_specific_entity_command_handler()

        assert result is not None

    @pytest.mark.asyncio
    async def test_create_get_client_query_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating GetClientQueryHandler (legacy)."""
        result = factory.create_get_client_query_handler()

        assert result is None

    @pytest.mark.asyncio
    async def test_create_search_clients_query_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating SearchClientsQueryHandler (legacy)."""
        result = factory.create_search_clients_query_handler()

        assert result is None

    @pytest.mark.asyncio
    async def test_create_get_client_history_query_handler(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test creating GetClientHistoryQueryHandler (legacy)."""
        result = factory.create_get_client_history_query_handler()

        assert result is None

    @pytest.mark.asyncio
    async def test_close_with_database_manager(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test closing factory with database manager."""
        mock_db_manager = MagicMock()
        mock_db_manager.close = AsyncMock()
        factory._database_manager = mock_db_manager

        await factory.close()

        mock_db_manager.close.assert_awaited_once()
        assert factory._database_manager is None
        assert factory._event_handler is None
        assert factory._session_manager is None

    @pytest.mark.asyncio
    async def test_close_without_database_manager(
        self, factory: InfrastructureFactory
    ) -> None:
        """Test closing factory without database manager."""
        factory._database_manager = None

        await factory.close()

        assert factory._database_manager is None
        assert factory._event_handler is None
        assert factory._session_manager is None


class TestQueryHandlerWrappers:
    """Test cases for query handler wrappers created by the factory."""

    @pytest.fixture
    def factory_mock(self) -> MagicMock:
        """Provide a mock InfrastructureFactory."""
        mock = MagicMock()
        mock.session_manager.get_session = AsyncMock()
        return mock

    @pytest.fixture
    def session_mock(self) -> MagicMock:
        """Provide a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_user_query_handler_wrapper(
        self, factory_mock: MagicMock
    ) -> None:
        """Test GetUserQueryHandler wrapper functionality."""
        from event_sourcing.infrastructure.factory import InfrastructureFactory

        # Create the factory and get the wrapper
        factory = InfrastructureFactory("test_url")
        factory._database_manager = MagicMock()
        factory._session_manager = factory_mock

        wrapper = factory.create_get_user_query_handler()

        # Test that the wrapper has the expected interface
        assert hasattr(wrapper, "handle")
        assert hasattr(wrapper, "_create_handler_with_session")
        assert callable(wrapper.handle)
        assert callable(wrapper._create_handler_with_session)

    @pytest.mark.asyncio
    async def test_get_user_query_handler_wrapper_methods(
        self, factory_mock: MagicMock
    ) -> None:
        """Test GetUserQueryHandler wrapper internal methods."""
        from event_sourcing.infrastructure.factory import InfrastructureFactory

        # Create the factory and get the wrapper
        factory = InfrastructureFactory("test_url")
        factory._database_manager = MagicMock()
        factory._session_manager = factory_mock

        wrapper = factory.create_get_user_query_handler()

        # Test that the wrapper has the expected methods and they are callable
        assert hasattr(wrapper, "handle")
        assert hasattr(wrapper, "_create_handler_with_session")
        assert callable(wrapper.handle)
        assert callable(wrapper._create_handler_with_session)

        # Test that the wrapper is an instance of the expected class
        assert "QueryHandlerWrapper" in str(type(wrapper))

    @pytest.mark.asyncio
    async def test_get_user_history_query_handler_wrapper(
        self, factory_mock: MagicMock
    ) -> None:
        """Test GetUserHistoryQueryHandler wrapper functionality."""
        from event_sourcing.infrastructure.factory import InfrastructureFactory

        # Create the factory and get the wrapper
        factory = InfrastructureFactory("test_url")
        factory._database_manager = MagicMock()
        factory._session_manager = factory_mock

        wrapper = factory.create_get_user_history_query_handler()

        # Test that the wrapper has the expected interface
        assert hasattr(wrapper, "handle")
        assert hasattr(wrapper, "_create_handler_with_session")
        assert callable(wrapper.handle)
        assert callable(wrapper._create_handler_with_session)

    @pytest.mark.asyncio
    async def test_get_user_history_query_handler_wrapper_methods(
        self, factory_mock: MagicMock
    ) -> None:
        """Test GetUserHistoryQueryHandler wrapper internal methods."""
        from event_sourcing.infrastructure.factory import InfrastructureFactory

        # Create the factory and get the wrapper
        factory = InfrastructureFactory("test_url")
        factory._database_manager = MagicMock()
        factory._session_manager = factory_mock

        wrapper = factory.create_get_user_history_query_handler()

        # Test that the wrapper has the expected methods and they are callable
        assert hasattr(wrapper, "handle")
        assert hasattr(wrapper, "_create_handler_with_session")
        assert callable(wrapper.handle)
        assert callable(wrapper._create_handler_with_session)

        # Test that the wrapper is an instance of the expected class
        assert "QueryHandlerWrapper" in str(type(wrapper))

    @pytest.mark.asyncio
    async def test_list_users_query_handler_wrapper(
        self, factory_mock: MagicMock
    ) -> None:
        """Test ListUsersQueryHandler wrapper functionality."""
        from event_sourcing.infrastructure.factory import InfrastructureFactory

        # Create the factory and get the wrapper
        factory = InfrastructureFactory("test_url")
        factory._database_manager = MagicMock()
        factory._session_manager = factory_mock

        wrapper = factory.create_list_users_query_handler()

        # Test that the wrapper has the expected interface
        assert hasattr(wrapper, "handle")
        assert hasattr(wrapper, "_create_handler_with_session")
        assert callable(wrapper.handle)
        assert callable(wrapper._create_handler_with_session)

    @pytest.mark.asyncio
    async def test_list_users_query_handler_wrapper_methods(
        self, factory_mock: MagicMock
    ) -> None:
        """Test ListUsersQueryHandler wrapper internal methods."""
        from event_sourcing.infrastructure.factory import InfrastructureFactory

        # Create the factory and get the wrapper
        factory = InfrastructureFactory("test_url")
        factory._database_manager = MagicMock()
        factory._session_manager = factory_mock

        wrapper = factory.create_list_users_query_handler()

        # Test that the wrapper has the expected methods and they are callable
        assert hasattr(wrapper, "handle")
        assert hasattr(wrapper, "_create_handler_with_session")
        assert callable(wrapper.handle)
        assert callable(wrapper._create_handler_with_session)

        # Test that the wrapper is an instance of the expected class
        assert "QueryHandlerWrapper" in str(type(wrapper))
