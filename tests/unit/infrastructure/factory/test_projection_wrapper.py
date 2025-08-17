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
        with patch(
            "event_sourcing.infrastructure.factory.projection_wrapper.inspect"
        ) as inspect_mock:
            sig_mock = MagicMock()
            sig_mock.parameters = {
                "read_model": MagicMock(),
                "unit_of_work": MagicMock(),
            }
            inspect_mock.signature.return_value = sig_mock

            (
                projection,
                session,
            ) = await wrapper._create_projection_with_session()

        assert session == session_mock
        wrapper.factory.session_manager.get_session.assert_awaited_once()
        postgresql_read_model_mock.assert_called_once_with(session_mock)
        sqla_uow_mock.assert_called_once_with(session_mock)

    @pytest.mark.asyncio
    @patch(
        "event_sourcing.infrastructure.factory.projection_wrapper.PostgreSQLReadModel"
    )
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
        with patch(
            "event_sourcing.infrastructure.factory.projection_wrapper.inspect"
        ) as inspect_mock:
            sig_mock = MagicMock()
            sig_mock.parameters = {"read_model": MagicMock()}
            inspect_mock.signature.return_value = sig_mock

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
