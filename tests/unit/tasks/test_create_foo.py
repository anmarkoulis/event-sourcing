from logging import getLogger
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from event_sourcing.dto import FooInDTO
from event_sourcing.tasks.create_foo import create_foo, create_foo_task

logger = getLogger(__name__)


@pytest.mark.anyio
class TestCreateFoo:
    @patch("event_sourcing.services.concrete.foo.FooService")
    async def test_create_foo(self, mock_service: MagicMock) -> None:
        # Arrange
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        # Act
        await create_foo("test_bar")

        # Assert
        mock_service.assert_called_once()
        mock_service_instance.create_foo.assert_awaited_once_with(
            FooInDTO(bar="test_bar")
        )

    @patch("event_sourcing.tasks.create_foo.create_foo")
    def test_create_foo_task(self, mock_create_foo: AsyncMock) -> None:
        # Arrange
        mock_create_foo.return_value = None

        # Act
        create_foo_task("test_bar")

        # Assert
        mock_create_foo.assert_called_once_with("test_bar")
