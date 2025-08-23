"""Unit tests for ProjectionWrapper."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from event_sourcing.infrastructure.factory import ProjectionWrapper


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
    @patch(
        "event_sourcing.infrastructure.factory.projection_wrapper.PostgreSQLReadModel"
    )
    @patch(
        "event_sourcing.infrastructure.factory.projection_wrapper.SQLAUnitOfWork"
    )
    async def test_handle_integration_with_uow(
        self,
        sqla_uow_mock: MagicMock,
        postgresql_read_model_mock: MagicMock,
        wrapper: ProjectionWrapper,
        session_mock: MagicMock,
        event_mock: MagicMock,
    ) -> None:
        """Test projection handling integration through public handle method when UoW is expected."""
        # Setup mocks
        wrapper.factory.session_manager.get_session.return_value = session_mock
        postgresql_read_model_mock.return_value = MagicMock()
        sqla_uow_mock.return_value = MagicMock()

        # Mock the projection class constructor and handle method
        projection_mock = MagicMock()
        projection_mock.handle = AsyncMock(return_value="success")
        wrapper.projection_class.return_value = projection_mock

        # Mock session close
        session_mock.close = AsyncMock()

        # Mock inspect.signature to return parameters including unit_of_work
        with patch(
            "event_sourcing.infrastructure.factory.projection_wrapper.inspect"
        ) as inspect_mock:
            sig_mock = MagicMock()
            sig_mock.parameters = {
                "read_model": MagicMock(),
                "unit_of_work": MagicMock(),
            }
            inspect_mock.signature.return_value = sig_mock

            # Test through public interface
            result = await wrapper.handle(event_mock)

        # Verify the result
        assert result == "success"

        # Verify session management
        wrapper.factory.session_manager.get_session.assert_awaited_once()
        session_mock.close.assert_awaited_once()

        # Verify projection creation and execution
        wrapper.projection_class.assert_called_once()
        projection_mock.handle.assert_awaited_once_with(event_mock)

    @pytest.mark.asyncio
    @patch(
        "event_sourcing.infrastructure.factory.projection_wrapper.PostgreSQLReadModel"
    )
    async def test_handle_integration_without_uow(
        self,
        postgresql_read_model_mock: MagicMock,
        wrapper: ProjectionWrapper,
        session_mock: MagicMock,
        event_mock: MagicMock,
    ) -> None:
        """Test projection handling integration through public handle method when UoW is not expected."""
        # Setup mocks
        wrapper.factory.session_manager.get_session.return_value = session_mock
        postgresql_read_model_mock.return_value = MagicMock()

        # Mock the projection class constructor and handle method
        projection_mock = MagicMock()
        projection_mock.handle = AsyncMock(return_value="success")
        wrapper.projection_class.return_value = projection_mock

        # Mock session close
        session_mock.close = AsyncMock()

        # Mock inspect.signature to return parameters excluding unit_of_work
        with patch(
            "event_sourcing.infrastructure.factory.projection_wrapper.inspect"
        ) as inspect_mock:
            sig_mock = MagicMock()
            sig_mock.parameters = {"read_model": MagicMock()}
            inspect_mock.signature.return_value = sig_mock

            # Test through public interface
            result = await wrapper.handle(event_mock)

        # Verify the result
        assert result == "success"

        # Verify session management
        wrapper.factory.session_manager.get_session.assert_awaited_once()
        session_mock.close.assert_awaited_once()

        # Verify projection creation and execution
        wrapper.projection_class.assert_called_once()
        projection_mock.handle.assert_awaited_once_with(event_mock)

    @pytest.mark.asyncio
    @patch(
        "event_sourcing.infrastructure.factory.projection_wrapper.PostgreSQLReadModel"
    )
    async def test_handle_success(
        self,
        postgresql_read_model_mock: MagicMock,
        wrapper: ProjectionWrapper,
        event_mock: MagicMock,
    ) -> None:
        """Test successful event handling through public interface."""
        # Setup mocks
        session_mock = MagicMock()
        session_mock.close = AsyncMock()
        wrapper.factory.session_manager.get_session.return_value = session_mock
        postgresql_read_model_mock.return_value = MagicMock()

        # Mock the projection class constructor and handle method
        projection_mock = MagicMock()
        projection_mock.handle = AsyncMock(return_value="success")
        wrapper.projection_class.return_value = projection_mock

        # Mock session close
        session_mock.close = AsyncMock()

        # Mock inspect.signature to return parameters including unit_of_work
        with patch(
            "event_sourcing.infrastructure.factory.projection_wrapper.inspect"
        ) as inspect_mock:
            sig_mock = MagicMock()
            sig_mock.parameters = {
                "read_model": MagicMock(),
                "unit_of_work": MagicMock(),
            }
            inspect_mock.signature.return_value = sig_mock

            result = await wrapper.handle(event_mock)

        assert result == "success"
        projection_mock.handle.assert_awaited_once_with(event_mock)
        session_mock.close.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "event_sourcing.infrastructure.factory.projection_wrapper.PostgreSQLReadModel"
    )
    async def test_handle_error(
        self,
        postgresql_read_model_mock: MagicMock,
        wrapper: ProjectionWrapper,
        event_mock: MagicMock,
    ) -> None:
        """Test event handling with error through public interface."""
        # Setup mocks
        session_mock = MagicMock()
        session_mock.close = AsyncMock()
        wrapper.factory.session_manager.get_session.return_value = session_mock
        postgresql_read_model_mock.return_value = MagicMock()

        # Mock the projection class constructor and handle method
        projection_mock = MagicMock()
        error = ValueError("Test error")
        projection_mock.handle = AsyncMock(side_effect=error)
        wrapper.projection_class.return_value = projection_mock

        # Mock session close
        session_mock.close = AsyncMock()

        # Mock inspect.signature to return parameters including unit_of_work
        with patch(
            "event_sourcing.infrastructure.factory.projection_wrapper.inspect"
        ) as inspect_mock:
            sig_mock = MagicMock()
            sig_mock.parameters = {
                "read_model": MagicMock(),
                "unit_of_work": MagicMock(),
            }
            inspect_mock.signature.return_value = sig_mock

            with pytest.raises(ValueError, match="Test error"):
                await wrapper.handle(event_mock)

        session_mock.close.assert_awaited_once()
