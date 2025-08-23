"""Unit tests for DatabaseManager."""

from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.infrastructure.database.session import DatabaseManager


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    @patch(
        "event_sourcing.infrastructure.database.session.create_async_engine"
    )
    @patch("event_sourcing.infrastructure.database.session.async_sessionmaker")
    async def test_get_session(
        self,
        mock_async_sessionmaker: MagicMock,
        mock_create_async_engine: MagicMock,
    ) -> None:
        """Test getting a new database session."""
        # Arrange
        mock_engine = MagicMock()
        mock_session_maker = MagicMock()
        mock_session = AsyncMock(spec=AsyncSession)

        mock_create_async_engine.return_value = mock_engine
        mock_async_sessionmaker.return_value = mock_session_maker
        mock_session_maker.return_value = mock_session

        db_manager = DatabaseManager("test_url")

        # Act
        result = await db_manager.get_session()

        # Assert
        assert result == mock_session
        mock_session_maker.assert_called_once()

    @patch(
        "event_sourcing.infrastructure.database.session.create_async_engine"
    )
    @patch("event_sourcing.infrastructure.database.session.async_sessionmaker")
    @patch("event_sourcing.infrastructure.database.session.logger")
    async def test_close(
        self,
        mock_logger: MagicMock,
        mock_async_sessionmaker: MagicMock,
        mock_create_async_engine: MagicMock,
    ) -> None:
        """Test closing the database engine."""
        # Arrange
        mock_engine = AsyncMock()
        mock_session_maker = MagicMock()

        mock_create_async_engine.return_value = mock_engine
        mock_async_sessionmaker.return_value = mock_session_maker

        db_manager = DatabaseManager("test_url")

        # Act
        await db_manager.close()

        # Assert
        mock_engine.dispose.assert_awaited_once()
        mock_logger.debug.assert_called_once_with("Database engine closed")
