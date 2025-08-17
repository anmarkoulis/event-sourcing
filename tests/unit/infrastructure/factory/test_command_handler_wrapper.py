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
