from unittest.mock import AsyncMock, MagicMock

import pytest

from event_sourcing.application.queries.handlers.user.list_users import (
    ListUsersQueryHandler,
)
from event_sourcing.application.queries.user.list_users import ListUsersQuery


@pytest.fixture
def handler(read_model_mock: MagicMock) -> ListUsersQueryHandler:
    # Configure the mock for this specific test
    read_model_mock.list_users = AsyncMock()
    return ListUsersQueryHandler(read_model=read_model_mock)


@pytest.fixture
def query() -> ListUsersQuery:
    return ListUsersQuery(page=2, page_size=2, username="a", email=None)


class TestListUsersQueryHandler:
    @pytest.mark.asyncio
    async def test_handle_success_builds_pagination(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
        query: ListUsersQuery,
    ) -> None:
        read_model_mock.list_users.return_value = ([{"id": 1}], 5)

        result = await handler.handle(query)

        read_model_mock.list_users.assert_awaited_once_with(
            page=2, page_size=2, username="a", email=None
        )
        assert result["results"] == [{"id": 1}]
        assert result["count"] == 5
        assert result["page"] == 2
        assert result["page_size"] == 2
        assert result["next"] == "/users/?page=3&page_size=2&username=a"
        assert result["previous"] == "/users/?page=1&page_size=2&username=a"

    @pytest.mark.asyncio
    async def test_handle_error_returns_empty_payload(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
        query: ListUsersQuery,
    ) -> None:
        read_model_mock.list_users.side_effect = Exception("boom")

        result = await handler.handle(query)

        assert result == {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
            "page": query.page,
            "page_size": query.page_size,
        }

    @pytest.mark.asyncio
    async def test_handle_first_page_no_previous_url(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that first page has no previous URL."""
        query = ListUsersQuery(page=1, page_size=10, username=None, email=None)
        read_model_mock.list_users.return_value = ([{"id": 1}], 15)

        result = await handler.handle(query)

        assert result["previous"] is None
        assert result["next"] == "/users/?page=2&page_size=10"
        assert result["page"] == 1

    @pytest.mark.asyncio
    async def test_handle_last_page_no_next_url(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that last page has no next URL."""
        query = ListUsersQuery(page=3, page_size=5, username=None, email=None)
        read_model_mock.list_users.return_value = ([{"id": 1}], 15)

        result = await handler.handle(query)

        assert result["next"] is None
        assert result["previous"] == "/users/?page=2&page_size=5"
        assert result["page"] == 3

    @pytest.mark.asyncio
    async def test_handle_single_page_no_pagination(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that single page has no next or previous URLs."""
        query = ListUsersQuery(page=1, page_size=20, username=None, email=None)
        read_model_mock.list_users.return_value = ([{"id": 1}], 15)

        result = await handler.handle(query)

        assert result["next"] is None
        assert result["previous"] is None
        assert result["page"] == 1

    @pytest.mark.asyncio
    async def test_handle_with_username_and_email_filters(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test URL building with both username and email filters."""
        query = ListUsersQuery(
            page=2, page_size=10, username="john", email="john@example.com"
        )
        read_model_mock.list_users.return_value = ([{"id": 1}], 25)

        result = await handler.handle(query)

        assert (
            result["next"]
            == "/users/?page=3&page_size=10&username=john&email=john@example.com"
        )
        assert (
            result["previous"]
            == "/users/?page=1&page_size=10&username=john&email=john@example.com"
        )

    @pytest.mark.asyncio
    async def test_handle_with_zero_total_count(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test handling when no users exist."""
        query = ListUsersQuery(page=1, page_size=10, username=None, email=None)
        read_model_mock.list_users.return_value = ([], 0)

        result = await handler.handle(query)

        assert result["next"] is None
        assert result["previous"] is None
        assert result["count"] == 0
        # total_pages is not returned in the response, it's calculated internally

    @pytest.mark.asyncio
    async def test_handle_with_exact_page_size_match(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test when total count exactly matches page size."""
        query = ListUsersQuery(page=1, page_size=5, username=None, email=None)
        read_model_mock.list_users.return_value = (
            [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
            5,
        )

        result = await handler.handle(query)

        assert (
            result["next"] is None
        )  # No next page since we have exactly 5 items
        assert result["previous"] is None
        assert result["count"] == 5
        # total_pages is not returned in the response

    @pytest.mark.asyncio
    async def test_handle_with_username_only_filter(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test URL building with only username filter."""
        query = ListUsersQuery(
            page=2, page_size=10, username="alice", email=None
        )
        read_model_mock.list_users.return_value = (
            [{"id": 1}],
            25,
        )  # Need more than 10 to have next page

        result = await handler.handle(query)

        assert result["next"] == "/users/?page=3&page_size=10&username=alice"
        assert (
            result["previous"] == "/users/?page=1&page_size=10&username=alice"
        )
        # Email should not appear in URL since it's None

    @pytest.mark.asyncio
    async def test_handle_with_email_only_filter(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test URL building with only email filter."""
        query = ListUsersQuery(
            page=2, page_size=10, username=None, email="admin@example.com"
        )
        read_model_mock.list_users.return_value = (
            [{"id": 1}],
            25,
        )  # Need more than 10 to have next page

        result = await handler.handle(query)

        assert (
            result["next"]
            == "/users/?page=3&page_size=10&email=admin@example.com"
        )
        assert (
            result["previous"]
            == "/users/?page=1&page_size=10&email=admin@example.com"
        )
        # Username should not appear in URL since it's None

    @pytest.mark.asyncio
    async def test_handle_with_username_and_email_filters_next_url(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that username and email filters are properly added to next URL."""
        query = ListUsersQuery(
            page=1, page_size=5, username="testuser", email="test@example.com"
        )
        read_model_mock.list_users.return_value = (
            [{"id": 1}],
            10,
        )  # Need more than 5 to have next page

        result = await handler.handle(query)

        # Should have next URL with both filters
        assert (
            result["next"]
            == "/users/?page=2&page_size=5&username=testuser&email=test@example.com"
        )
        assert result["previous"] is None  # First page has no previous

    @pytest.mark.asyncio
    async def test_handle_with_username_and_email_filters_previous_url(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that username and email filters are properly added to previous URL."""
        query = ListUsersQuery(
            page=3, page_size=5, username="testuser", email="test@example.com"
        )
        read_model_mock.list_users.return_value = (
            [{"id": 1}],
            10,
        )  # Need more than 5 to have next page

        result = await handler.handle(query)

        # Should have previous URL with both filters
        assert (
            result["previous"]
            == "/users/?page=2&page_size=5&username=testuser&email=test@example.com"
        )
        assert result["next"] is None  # Last page has no next

    @pytest.mark.asyncio
    async def test_handle_with_username_only_filter_next_url(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that username filter is properly added to next URL."""
        query = ListUsersQuery(
            page=1, page_size=5, username="testuser", email=None
        )
        read_model_mock.list_users.return_value = (
            [{"id": 1}],
            10,
        )  # Need more than 5 to have next page

        result = await handler.handle(query)

        # Should have next URL with username filter only
        assert result["next"] == "/users/?page=2&page_size=5&username=testuser"
        assert result["previous"] is None  # First page has no previous

    @pytest.mark.asyncio
    async def test_handle_with_email_only_filter_next_url(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that email filter is properly added to next URL."""
        query = ListUsersQuery(
            page=1, page_size=5, username=None, email="test@example.com"
        )
        read_model_mock.list_users.return_value = (
            [{"id": 1}],
            10,
        )  # Need more than 5 to have next page

        result = await handler.handle(query)

        # Should have next URL with email filter only
        assert (
            result["next"]
            == "/users/?page=2&page_size=5&email=test@example.com"
        )
        assert result["previous"] is None  # First page has no previous

    @pytest.mark.asyncio
    async def test_handle_with_username_only_filter_previous_url(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that username filter is properly added to previous URL."""
        query = ListUsersQuery(
            page=3, page_size=5, username="testuser", email=None
        )
        read_model_mock.list_users.return_value = (
            [{"id": 1}],
            10,
        )  # Need more than 5 to have next page

        result = await handler.handle(query)

        # Should have previous URL with username filter only
        assert (
            result["previous"]
            == "/users/?page=2&page_size=5&username=testuser"
        )
        assert result["next"] is None  # Last page has no next

    @pytest.mark.asyncio
    async def test_handle_with_email_only_filter_previous_url(
        self,
        handler: ListUsersQueryHandler,
        read_model_mock: MagicMock,
    ) -> None:
        """Test that email filter is properly added to previous URL."""
        query = ListUsersQuery(
            page=3, page_size=5, username=None, email="test@example.com"
        )
        read_model_mock.list_users.return_value = (
            [{"id": 1}],
            10,
        )  # Need more than 5 to have next page

        result = await handler.handle(query)

        # Should have previous URL with email filter only
        assert (
            result["previous"]
            == "/users/?page=2&page_size=5&email=test@example.com"
        )
        assert result["next"] is None  # Last page has no next
