from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from typing import AsyncIterator
from contextlib import asynccontextmanager
import logging

from ...infrastructure.factory import InfrastructureFactory
from ...config.settings import settings
from ..context import lifespan_context

logger = logging.getLogger(__name__)


@asynccontextmanager
async def configure_lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Configures the application's lifespan (e.g., for caching, lifecycle tasks).
    """
    logger.info("Starting application...")
    
    # Initialize infrastructure factory
    database_url = settings.DATABASE_URL
    eventbridge_region = getattr(settings, "EVENTBRIDGE_REGION", "us-east-1")
    
    infrastructure_factory = InfrastructureFactory(database_url, eventbridge_region)
    lifespan_context["infrastructure_factory"] = infrastructure_factory
    
    logger.info("Infrastructure factory initialized")
    
    # Initialize cache
    FastAPICache.init(InMemoryBackend())
    
    try:
        yield
    finally:
        # Cleanup
        logger.info("Shutting down application...")
        await infrastructure_factory.close()
        logger.info("Application shutdown complete")
