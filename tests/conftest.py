from typing import Any, AsyncGenerator

import asyncpg
import httpx
import pytest
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from event_sourcing.config.settings import settings
from event_sourcing.infrastructure.database.models.base import Base
from event_sourcing.infrastructure.database.session import get_db
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


@pytest.fixture(scope="function")
async def app_with_test_db(db: AsyncSession) -> Any:
    """
    Override the app fixture to use an in-memory test database
    """

    def override_get_db() -> AsyncSession:
        return db

    app.dependency_overrides[get_db] = override_get_db
    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client() -> AsyncGenerator:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
