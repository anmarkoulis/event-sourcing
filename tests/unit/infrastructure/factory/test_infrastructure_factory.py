"""Unit tests for InfrastructureFactory and QueryHandlerWrappers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from event_sourcing.infrastructure.factory import (
    CommandHandlerWrapper,
    InfrastructureFactory,
    ProjectionWrapper,
)


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
    @patch(
        "event_sourcing.infrastructure.factory.infrastructure_factory.DatabaseManager"
    )
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
    @patch(
        "event_sourcing.infrastructure.factory.infrastructure_factory.EmailProviderFactory"
    )
    @patch(
        "event_sourcing.infrastructure.factory.infrastructure_factory.LoggingEmailProvider"
    )
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
    @patch(
        "event_sourcing.infrastructure.factory.infrastructure_factory.EmailProviderFactory"
    )
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
    @patch(
        "event_sourcing.infrastructure.factory.infrastructure_factory.EmailProviderFactory"
    )
    async def test_create_email_provider_default_config(
        self,
        email_provider_factory_mock: MagicMock,
        factory: InfrastructureFactory,
    ) -> None:
        """Test email provider creation with default config."""
        provider = factory.create_email_provider()
        assert provider is not None

    def test_get_hashing_service(self, factory: InfrastructureFactory) -> None:
        """Test hashing service creation."""
        from event_sourcing.infrastructure.security import (
            HashingServiceInterface,
        )

        hashing_service = factory.get_hashing_service()
        assert isinstance(hashing_service, HashingServiceInterface)
        assert hashing_service is not None

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
        import_mock.return_value.BackfillEntityTypeCommandHandler = (
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

        # Test that the wrapper is an instance of the expected class
        assert "QueryHandlerWrapper" in str(type(wrapper))

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
