from unittest.mock import AsyncMock, MagicMock

import pytest

from event_sourcing.application.queries.handlers.user.list_users_query_handler import (
    ListUsersQueryHandler,
)
from event_sourcing.application.queries.user.list_users import ListUsersQuery


@pytest.fixture
def read_model_mock() -> MagicMock:
    rm = MagicMock()
    rm.list_users = AsyncMock()
    return rm


@pytest.fixture
def handler(read_model_mock: MagicMock) -> ListUsersQueryHandler:
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
