from typing import Generator
from fastapi import Depends

from .context import lifespan_context
from ..infrastructure.factory import InfrastructureFactory
from ..config.settings import settings
from ..application.services.dependency_service import DependencyService, get_infrastructure_factory


def get_database_url() -> str:
    """Get database URL from settings"""
    return settings.DATABASE_URL


def get_eventbridge_region() -> str:
    """Get EventBridge region from settings"""
    return getattr(settings, "EVENTBRIDGE_REGION", "us-east-1")


# Re-export from application layer
__all__ = ["DependencyService", "get_infrastructure_factory"]
