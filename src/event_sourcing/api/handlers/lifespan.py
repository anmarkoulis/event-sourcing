import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from event_sourcing.api.context import lifespan_context
from event_sourcing.config.settings import settings
from event_sourcing.infrastructure.factory import InfrastructureFactory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def configure_lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Configures the application's lifespan (e.g., for caching, lifecycle tasks).
    """
    logger.debug("Starting application...")

    # Initialize infrastructure factory
    database_url = settings.DATABASE_URL

    infrastructure_factory = InfrastructureFactory(database_url)
    lifespan_context["infrastructure_factory"] = infrastructure_factory

    logger.debug("Infrastructure factory initialized")

    # Initialize cache
    FastAPICache.init(InMemoryBackend())

    try:
        yield
    finally:
        # Cleanup
        logger.debug("Shutting down application...")
        await infrastructure_factory.close()
        logger.debug("Application shutdown complete")
