"""Unit tests for ListUsersQueryHandler module."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from event_sourcing.application.queries.handlers.user.list_users_query_handler import (
    ListUsersQueryHandler,
)
from event_sourcing.application.queries.user import ListUsersQuery
from event_sourcing.infrastructure.read_model import ReadModel


class TestListUsersQueryHandler:
    """Test cases for ListUsersQueryHandler class."""

    @pytest.fixture
    def mock_read_model(self) -> MagicMock:
        """Create a mock read model."""
        read_model = MagicMock(spec=ReadModel)
        read_model.list_users = AsyncMock()
        return read_model

    @pytest.fixture
    def sample_users(self) -> list[dict]:
        """Create sample user data."""
        return [
            {
                "id": str(uuid4()),
                "username": "user1",
                "email": "user1@example.com",
                "first_name": "User",
                "last_name": "One",
                "created_at": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            },
            {
                "id": str(uuid4()),
                "username": "user2",
                "email": "user2@example.com",
                "first_name": "User",
                "last_name": "Two",
                "created_at": datetime(2023, 1, 1, 13, 0, tzinfo=timezone.utc),
            },
        ]

    def test_init(self, mock_read_model: MagicMock) -> None:
        """Test handler initialization."""
        handler = ListUsersQueryHandler(mock_read_model)
        assert handler.read_model == mock_read_model

    @pytest.mark.asyncio
    async def test_handle_basic_query(
        self, mock_read_model: MagicMock, sample_users: list[dict]
    ) -> None:
        """Test handling basic list users query."""
        # Arrange
        mock_read_model.list_users.return_value = (sample_users, 2)
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(page=1, page_size=10)

        # Act
        result = await handler.handle(query)

        # Assert
        mock_read_model.list_users.assert_awaited_once_with(
            page=1, page_size=10, username=None, email=None
        )
        assert result["results"] == sample_users
        assert result["count"] == 2
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["next"] is None  # Only 1 page with 2 users
        assert result["previous"] is None  # First page

    @pytest.mark.asyncio
    async def test_handle_with_filters(
        self, mock_read_model: MagicMock, sample_users: list[dict]
    ) -> None:
        """Test handling query with username and email filters."""
        # Arrange
        mock_read_model.list_users.return_value = (sample_users, 2)
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(
            page=1, page_size=10, username="user1", email="user1@example.com"
        )

        # Act
        result = await handler.handle(query)

        # Assert
        mock_read_model.list_users.assert_awaited_once_with(
            page=1, page_size=10, username="user1", email="user1@example.com"
        )
        assert result["results"] == sample_users

    @pytest.mark.asyncio
    async def test_handle_pagination_next_page(
        self, mock_read_model: MagicMock, sample_users: list[dict]
    ) -> None:
        """Test pagination with next page available."""
        # Arrange
        mock_read_model.list_users.return_value = (
            sample_users,
            25,
        )  # 25 total users
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(page=1, page_size=10)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result["count"] == 25
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["next"] == "/users/?page=2&page_size=10"
        assert result["previous"] is None

    @pytest.mark.asyncio
    async def test_handle_pagination_previous_page(
        self, mock_read_model: MagicMock, sample_users: list[dict]
    ) -> None:
        """Test pagination with previous page available."""
        # Arrange
        mock_read_model.list_users.return_value = (
            sample_users,
            25,
        )  # 25 total users
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(page=2, page_size=10)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result["count"] == 25
        assert result["page"] == 2
        assert result["page_size"] == 10
        assert result["next"] == "/users/?page=3&page_size=10"
        assert result["previous"] == "/users/?page=1&page_size=10"

    @pytest.mark.asyncio
    async def test_handle_pagination_with_filters(
        self, mock_read_model: MagicMock, sample_users: list[dict]
    ) -> None:
        """Test pagination URLs include filters."""
        # Arrange
        mock_read_model.list_users.return_value = (sample_users, 25)
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(
            page=2, page_size=10, username="user1", email="user1@example.com"
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert (
            result["next"]
            == "/users/?page=3&page_size=10&username=user1&email=user1@example.com"
        )
        assert (
            result["previous"]
            == "/users/?page=1&page_size=10&username=user1&email=user1@example.com"
        )

    @pytest.mark.asyncio
    async def test_handle_last_page(
        self, mock_read_model: MagicMock, sample_users: list[dict]
    ) -> None:
        """Test handling query for the last page."""
        # Arrange
        mock_read_model.list_users.return_value = (sample_users, 25)
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(
            page=3, page_size=10
        )  # Last page (25 users / 10 per page = 3 pages)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result["next"] is None  # No next page
        assert result["previous"] == "/users/?page=2&page_size=10"

    @pytest.mark.asyncio
    async def test_handle_empty_results(
        self, mock_read_model: MagicMock
    ) -> None:
        """Test handling query with no results."""
        # Arrange
        mock_read_model.list_users.return_value = ([], 0)
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(page=1, page_size=10)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result["results"] == []
        assert result["count"] == 0
        assert result["next"] is None
        assert result["previous"] is None

    @pytest.mark.asyncio
    async def test_handle_error_returns_empty_result(
        self, mock_read_model: MagicMock
    ) -> None:
        """Test that errors return empty result instead of crashing."""
        # Arrange
        mock_read_model.list_users.side_effect = Exception("Database error")
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(page=1, page_size=10)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result["results"] == []
        assert result["count"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["next"] is None
        assert result["previous"] is None

    @pytest.mark.asyncio
    async def test_handle_exact_page_size(
        self, mock_read_model: MagicMock, sample_users: list[dict]
    ) -> None:
        """Test pagination when total count equals page size."""
        # Arrange
        mock_read_model.list_users.return_value = (
            sample_users,
            10,
        )  # Exactly 10 users
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(page=1, page_size=10)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result["count"] == 10
        assert result["next"] is None  # No next page needed
        assert result["previous"] is None

    @pytest.mark.asyncio
    async def test_handle_large_page_size(
        self, mock_read_model: MagicMock, sample_users: list[dict]
    ) -> None:
        """Test pagination with page size larger than total count."""
        # Arrange
        mock_read_model.list_users.return_value = (
            sample_users,
            2,
        )  # Only 2 users
        handler = ListUsersQueryHandler(mock_read_model)
        query = ListUsersQuery(page=1, page_size=100)  # Large page size

        # Act
        result = await handler.handle(query)

        # Assert
        assert result["count"] == 2
        assert result["next"] is None  # No next page needed
        assert result["previous"] is None
