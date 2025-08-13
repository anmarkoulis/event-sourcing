from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import asyncpg
import httpx
import pytest
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


@pytest.fixture(scope="session")
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
    from event_sourcing.infrastructure.factory import InfrastructureFactory

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
