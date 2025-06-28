from event_sourcing.application.services.dependency_service import (
    DependencyService,
)
from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.config.settings import settings


def get_database_url() -> str:
    """Get database URL from settings"""
    return settings.DATABASE_URL


def get_eventbridge_region() -> str:
    """Get EventBridge region from settings"""
    return getattr(settings, "EVENTBRIDGE_REGION", "us-east-1")


# Re-export from application layer
__all__ = ["DependencyService", "get_infrastructure_factory"]
