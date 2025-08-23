"""Unit tests for PostgreSQL Unit of Work."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.infrastructure.unit_of_work.psql import SQLAUnitOfWork


class TestSQLAUnitOfWork:
    """Test cases for SQLAUnitOfWork class."""

    def test_init(self) -> None:
        """Test SQLAUnitOfWork initialization."""
        mock_db = AsyncMock(spec=AsyncSession)
        uow = SQLAUnitOfWork(mock_db)

        assert uow.db is mock_db

    async def test_commit_success(self) -> None:
        """Test successful commit operation."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_obj1 = MagicMock()
        mock_obj2 = MagicMock()
        mock_db.new = [mock_obj1, mock_obj2]  # 2 new objects

        uow = SQLAUnitOfWork(mock_db)

        await uow.commit()

        # Verify commit was called
        mock_db.commit.assert_called_once()

    async def test_commit_with_no_new_objects(self) -> None:
        """Test commit operation when session has no new objects."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.new = []  # No new objects

        uow = SQLAUnitOfWork(mock_db)

        await uow.commit()

        # Verify commit was called
        mock_db.commit.assert_called_once()

    async def test_commit_with_exception(self) -> None:
        """Test commit operation when an exception occurs."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.new = [MagicMock()]
        mock_db.commit.side_effect = Exception("Database error")

        uow = SQLAUnitOfWork(mock_db)

        with pytest.raises(Exception, match="Database error"):
            await uow.commit()

        # Verify commit was called
        mock_db.commit.assert_called_once()

    async def test_rollback(self) -> None:
        """Test rollback operation."""
        mock_db = AsyncMock(spec=AsyncSession)
        uow = SQLAUnitOfWork(mock_db)

        await uow.rollback()

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    async def test_context_manager_enter(self) -> None:
        """Test async context manager enter."""
        mock_db = AsyncMock(spec=AsyncSession)
        uow = SQLAUnitOfWork(mock_db)

        result = await uow.__aenter__()

        assert result is uow

    async def test_context_manager_exit_with_exception(self) -> None:
        """Test async context manager exit with exception."""
        mock_db = AsyncMock(spec=AsyncSession)
        uow = SQLAUnitOfWork(mock_db)

        exception = Exception("Test exception")

        await uow.__aexit__(Exception, exception, None)

        # Verify rollback was called due to exception
        mock_db.rollback.assert_called_once()

    async def test_context_manager_exit_without_exception(self) -> None:
        """Test async context manager exit without exception."""
        mock_db = AsyncMock(spec=AsyncSession)
        uow = SQLAUnitOfWork(mock_db)

        await uow.__aexit__(None, None, None)

        # Verify commit was called (no exception)
        mock_db.commit.assert_called_once()

    async def test_context_manager_exit_with_exception_instance(self) -> None:
        """Test async context manager exit with exception instance."""
        mock_db = AsyncMock(spec=AsyncSession)
        uow = SQLAUnitOfWork(mock_db)

        exception = Exception("Test exception")

        await uow.__aexit__(Exception, exception, None)

        # Verify rollback was called due to exception
        mock_db.rollback.assert_called_once()

    async def test_context_manager_exit_with_different_exception_types(
        self,
    ) -> None:
        """Test async context manager exit with different exception types."""
        mock_db = AsyncMock(spec=AsyncSession)
        uow = SQLAUnitOfWork(mock_db)

        # Test with ValueError
        await uow.__aexit__(ValueError, ValueError("Value error"), None)
        mock_db.rollback.assert_called_once()
        mock_db.rollback.reset_mock()

        # Test with RuntimeError
        await uow.__aexit__(RuntimeError, RuntimeError("Runtime error"), None)
        mock_db.rollback.assert_called_once()
