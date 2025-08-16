import os
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import asyncpg
import httpx
import pytest
from freezegun import freeze_time
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.config.settings import settings
from event_sourcing.infrastructure.database.base import Base
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.snapshot_store.base import SnapshotStore
from event_sourcing.infrastructure.unit_of_work.base import BaseUnitOfWork

# No get_db function exists in this codebase - using infrastructure factory pattern instead
from event_sourcing.main import app


async def create_database_if_not_exists() -> None:
    test_database_url = make_url(settings.TEST_DATABASE_URL)
    try:
        await asyncpg.connect(
            host=test_database_url.host,
            port=test_database_url.port,
            user=test_database_url.username,
            password=test_database_url.password,
            database=test_database_url.database,
        )
    except asyncpg.InvalidCatalogNameError:
        sys_conn = await asyncpg.connect(
            host=test_database_url.host,
            port=test_database_url.port,
            user=test_database_url.username,
            password=test_database_url.password,
            database="template1",
        )
        await sys_conn.execute(f"CREATE DATABASE {test_database_url.database}")
        await sys_conn.close()


@pytest.fixture(scope="function")
async def db_engine() -> Any:
    await create_database_if_not_exists()
    engine: AsyncEngine = create_async_engine(
        settings.TEST_DATABASE_URL,
        pool_pre_ping=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine


@pytest.fixture(scope="function")
async def db(db_engine: Any) -> AsyncGenerator:
    connection = await db_engine.connect()
    await connection.begin()
    db = AsyncSession(
        bind=connection,
    )

    yield db

    await connection.rollback()
    await connection.close()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def test_infrastructure_factory(db_engine: Any) -> Any:
    """Create infrastructure factory configured with test database."""
    from event_sourcing.config.settings import settings
    from event_sourcing.infrastructure.factory import InfrastructureFactory

    # Enable sync event handling for tests
    settings.SYNC_EVENT_HANDLER = True

    return InfrastructureFactory(database_url=settings.TEST_DATABASE_URL)


@pytest.fixture
async def app_with_test_infrastructure(
    test_infrastructure_factory: Any,
) -> Any:
    """Override the app's infrastructure factory dependency to use test database."""
    from event_sourcing.api.depends import get_infrastructure_factory

    def override_get_infrastructure_factory() -> Any:
        return test_infrastructure_factory

    app.dependency_overrides[get_infrastructure_factory] = (
        override_get_infrastructure_factory
    )
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client_with_test_db(
    app_with_test_infrastructure: Any,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client configured with test database."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_with_test_infrastructure),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    from event_sourcing.main import app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# Common unit-test fixtures for command handlers


@pytest.fixture
def event_store_mock() -> MagicMock:
    """Bare EventStore double; tests configure awaited methods as needed."""
    return MagicMock(spec_set=EventStore)


@pytest.fixture
def event_handler_mock() -> MagicMock:
    """Bare EventHandler double; tests configure async methods as needed."""
    return MagicMock(spec_set=EventHandler)


@pytest.fixture
def unit_of_work() -> MagicMock:
    """Minimal async UoW double with context manager semantics."""
    uow = MagicMock(spec_set=BaseUnitOfWork)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    async def _aenter() -> MagicMock:
        return uow

    async def _aexit(
        exc_type: Any, exc: BaseException | None, tb: Any
    ) -> None:
        if exc:
            await uow.rollback()
        else:
            await uow.commit()
        return None

    uow.__aenter__ = AsyncMock(side_effect=_aenter)
    uow.__aexit__ = AsyncMock(side_effect=_aexit)

    return uow


@pytest.fixture
def snapshot_store_mock() -> MagicMock:
    """Snapshot store double with async get/set."""
    store = MagicMock(spec_set=SnapshotStore)
    store.get = AsyncMock(return_value=None)
    store.set = AsyncMock()
    return store


@pytest.fixture
def read_model_mock() -> MagicMock:
    """Bare PostgreSQLReadModel double; tests configure awaited methods as needed."""
    from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

    return MagicMock(spec_set=PostgreSQLReadModel)


@pytest.fixture
def freezer() -> Any:
    """Freezegun fixture for controlling time in tests."""
    return freeze_time


# System test fixtures for authentication and user management


@pytest.fixture
async def admin_user_credentials() -> dict:
    """Admin user credentials for testing."""
    return {
        "username": "admin",
        "password": "admin123",
        "email": "admin@test.com",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
    }


@pytest.fixture
async def regular_user_credentials() -> dict:
    """Regular user credentials for testing."""
    return {
        "username": "testuser",
        "password": "user123",
        "email": "user@test.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
    }


@pytest.fixture
async def admin_user(
    test_infrastructure_factory: Any,
    admin_user_credentials: dict,
) -> dict:
    """Create an admin user and return user info."""
    try:
        import uuid

        from event_sourcing.application.commands.user.create_user import (
            CreateUserCommand,
        )
        from event_sourcing.enums import Role

        # Create command handler
        command_handler = (
            test_infrastructure_factory.create_create_user_command_handler()
        )

        # Create the command
        command = CreateUserCommand(
            user_id=uuid.uuid4(),
            username=admin_user_credentials["username"],
            email=admin_user_credentials["email"],
            first_name=admin_user_credentials["first_name"],
            last_name=admin_user_credentials["last_name"],
            password=admin_user_credentials["password"],
            role=Role.ADMIN,
        )

        # Execute the command
        await command_handler.handle(command)

        return {
            "user_id": str(command.user_id),
            "username": admin_user_credentials["username"],
            "email": admin_user_credentials["email"],
            "first_name": admin_user_credentials["first_name"],
            "last_name": admin_user_credentials["last_name"],
            "role": admin_user_credentials["role"],
            "password": admin_user_credentials["password"],
        }

    except Exception as e:
        pytest.fail(f"Failed to create admin user: {e}")


@pytest.fixture
async def regular_user(
    test_infrastructure_factory: Any,
    regular_user_credentials: dict,
) -> dict:
    """Create a regular user and return user info."""
    try:
        import uuid

        from event_sourcing.application.commands.user.create_user import (
            CreateUserCommand,
        )
        from event_sourcing.enums import Role

        # Create command handler
        command_handler = (
            test_infrastructure_factory.create_create_user_command_handler()
        )

        # Create the command
        command = CreateUserCommand(
            user_id=uuid.uuid4(),
            username=regular_user_credentials["username"],
            email=regular_user_credentials["email"],
            first_name=regular_user_credentials["first_name"],
            last_name=regular_user_credentials["last_name"],
            password=regular_user_credentials["password"],
            role=Role.USER,
        )

        # Execute the command
        await command_handler.handle(command)

        return {
            "user_id": str(command.user_id),
            "username": regular_user_credentials["username"],
            "email": regular_user_credentials["email"],
            "first_name": regular_user_credentials["first_name"],
            "last_name": regular_user_credentials["last_name"],
            "role": regular_user_credentials["role"],
            "password": regular_user_credentials["password"],
        }

    except Exception as e:
        pytest.fail(f"Failed to create regular user: {e}")


@pytest.fixture
async def admin_jwt_token(
    async_client_with_test_db: httpx.AsyncClient,
    admin_user: dict,
) -> str:
    """Get JWT token for admin user."""
    try:
        response = await async_client_with_test_db.post(
            "/v1/auth/login/",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"],
            },
        )

        if response.status_code != 200:
            pytest.fail(
                f"Admin login failed: {response.status_code} - {response.text}"
            )

        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            pytest.fail("No access_token in response")
        return str(access_token)

    except Exception as e:
        pytest.fail(f"Failed to get admin JWT token: {e}")


@pytest.fixture
async def user_jwt_token(
    async_client_with_test_db: httpx.AsyncClient,
    regular_user: dict,
) -> str:
    """Get JWT token for regular user."""
    try:
        response = await async_client_with_test_db.post(
            "/v1/auth/login/",
            json={
                "username": regular_user["username"],
                "password": regular_user["password"],
            },
        )

        if response.status_code != 200:
            pytest.fail(
                f"User login failed: {response.status_code} - {response.text}"
            )

        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            pytest.fail("No access_token in response")
        return str(access_token)

    except Exception as e:
        pytest.fail(f"Failed to get user JWT token: {e}")


@pytest.fixture
async def admin_client(
    async_client_with_test_db: httpx.AsyncClient,
    admin_jwt_token: str,
) -> httpx.AsyncClient:
    """HTTP client authenticated as admin user."""
    # Create a new client instance to avoid sharing headers
    import httpx

    client = httpx.AsyncClient(
        transport=async_client_with_test_db._transport,
        base_url=async_client_with_test_db.base_url,
        headers={"Authorization": f"Bearer {admin_jwt_token}"},
    )
    return client


@pytest.fixture
async def user_client(
    async_client_with_test_db: httpx.AsyncClient,
    user_jwt_token: str,
) -> httpx.AsyncClient:
    """HTTP client authenticated as regular user."""
    # Create a new client instance to avoid sharing headers
    import httpx

    client = httpx.AsyncClient(
        transport=async_client_with_test_db._transport,
        base_url=async_client_with_test_db.base_url,
        headers={"Authorization": f"Bearer {user_jwt_token}"},
    )
    return client


@pytest.fixture
async def unauthenticated_client(
    async_client_with_test_db: httpx.AsyncClient,
) -> httpx.AsyncClient:
    """HTTP client without authentication."""
    # Ensure no auth headers are set
    if "Authorization" in async_client_with_test_db.headers:
        del async_client_with_test_db.headers["Authorization"]
    return async_client_with_test_db


def _get_test_db_url() -> str:
    """Get test database URL from environment or use default."""
    return (
        os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://test:test@localhost:5432/test_db",
        )
        or "postgresql://test:test@localhost:5432/test_db"
    )


def _get_test_db_url_async() -> str:
    """Get async test database URL from environment or use default."""
    return (
        os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5432/test_db",
        )
        or "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
