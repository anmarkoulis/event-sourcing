"""Unit tests for CommandHandlerWrapper."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from event_sourcing.infrastructure.factory import CommandHandlerWrapper


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
    @patch(
        "event_sourcing.infrastructure.factory.command_handler_wrapper.SQLAUnitOfWork"
    )
    @patch(
        "event_sourcing.infrastructure.factory.command_handler_wrapper.PostgreSQLEventStore"
    )
    @patch(
        "event_sourcing.infrastructure.snapshot_store.psql_store.PsqlSnapshotStore"
    )
    async def test_handle_integration(
        self,
        psql_snapshot_store_mock: MagicMock,
        postgresql_event_store_mock: MagicMock,
        sqla_uow_mock: MagicMock,
        wrapper: CommandHandlerWrapper,
        session_mock: MagicMock,
        command_mock: MagicMock,
    ) -> None:
        """Test command handling integration through public handle method."""
        # Setup mocks
        wrapper.factory.session_manager.get_session.return_value = session_mock
        wrapper.factory.event_handler = MagicMock()

        # Mock the handler class constructor and handle method
        handler_mock = MagicMock()
        handler_mock.handle = AsyncMock(return_value="success")
        wrapper.handler_class.return_value = handler_mock

        # Mock the dependencies
        sqla_uow_mock.return_value = MagicMock()
        postgresql_event_store_mock.return_value = MagicMock()
        psql_snapshot_store_mock.return_value = MagicMock()

        # Mock session close
        session_mock.close = AsyncMock()

        # Test through public interface
        result = await wrapper.handle(command_mock)

        # Verify the result
        assert result == "success"

        # Verify session management
        wrapper.factory.session_manager.get_session.assert_awaited_once()
        session_mock.close.assert_awaited_once()

        # Verify handler creation and execution
        wrapper.handler_class.assert_called_once()
        handler_mock.handle.assert_awaited_once_with(command_mock)

    @pytest.mark.asyncio
    @patch(
        "event_sourcing.infrastructure.factory.command_handler_wrapper.SQLAUnitOfWork"
    )
    @patch(
        "event_sourcing.infrastructure.factory.command_handler_wrapper.PostgreSQLEventStore"
    )
    @patch(
        "event_sourcing.infrastructure.snapshot_store.psql_store.PsqlSnapshotStore"
    )
    async def test_handle_success(
        self,
        psql_snapshot_store_mock: MagicMock,
        postgresql_event_store_mock: MagicMock,
        sqla_uow_mock: MagicMock,
        wrapper: CommandHandlerWrapper,
        command_mock: MagicMock,
    ) -> None:
        """Test successful command handling through public interface."""
        # Setup mocks
        session_mock = MagicMock()
        session_mock.close = AsyncMock()
        wrapper.factory.session_manager.get_session.return_value = session_mock
        wrapper.factory.event_handler = MagicMock()

        # Mock the handler class constructor and handle method
        handler_mock = MagicMock()
        handler_mock.handle = AsyncMock(return_value="success")
        wrapper.handler_class.return_value = handler_mock

        # Mock the dependencies
        sqla_uow_mock.return_value = MagicMock()
        postgresql_event_store_mock.return_value = MagicMock()
        psql_snapshot_store_mock.return_value = MagicMock()

        result = await wrapper.handle(command_mock)

        assert result == "success"
        handler_mock.handle.assert_awaited_once_with(command_mock)
        session_mock.close.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "event_sourcing.infrastructure.factory.command_handler_wrapper.SQLAUnitOfWork"
    )
    @patch(
        "event_sourcing.infrastructure.factory.command_handler_wrapper.PostgreSQLEventStore"
    )
    @patch(
        "event_sourcing.infrastructure.snapshot_store.psql_store.PsqlSnapshotStore"
    )
    async def test_handle_error(
        self,
        psql_snapshot_store_mock: MagicMock,
        postgresql_event_store_mock: MagicMock,
        sqla_uow_mock: MagicMock,
        wrapper: CommandHandlerWrapper,
        command_mock: MagicMock,
    ) -> None:
        """Test command handling with error through public interface."""
        # Setup mocks
        session_mock = MagicMock()
        session_mock.close = AsyncMock()
        wrapper.factory.session_manager.get_session.return_value = session_mock
        wrapper.factory.event_handler = MagicMock()

        # Mock the handler class constructor and handle method
        handler_mock = MagicMock()
        error = ValueError("Test error")
        handler_mock.handle = AsyncMock(side_effect=error)
        wrapper.handler_class.return_value = handler_mock

        # Mock the dependencies
        sqla_uow_mock.return_value = MagicMock()
        postgresql_event_store_mock.return_value = MagicMock()
        psql_snapshot_store_mock.return_value = MagicMock()

        with pytest.raises(ValueError, match="Test error"):
            await wrapper.handle(command_mock)

        session_mock.close.assert_awaited_once()
