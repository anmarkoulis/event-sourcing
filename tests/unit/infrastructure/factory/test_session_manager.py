"""Unit tests for SessionManager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from event_sourcing.infrastructure.factory import SessionManager


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
