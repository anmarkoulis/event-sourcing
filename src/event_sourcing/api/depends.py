from event_sourcing.application.services.dependency_service import (
    DependencyService,
)
from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.config.settings import settings


def get_database_url() -> str:
    """Get database URL from settings"""
    return str(settings.DATABASE_URL)


def get_eventbridge_region() -> str:
    """Get EventBridge region from settings"""
    default_region = "us-east-1"
    if hasattr(settings, "EVENTBRIDGE_REGION"):
        region_value = settings.EVENTBRIDGE_REGION
        if isinstance(region_value, str):
            return region_value
    return default_region


# Re-export from application layer
__all__ = ["DependencyService", "get_infrastructure_factory"]
