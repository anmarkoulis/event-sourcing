from event_sourcing.config.settings import settings
from event_sourcing.infrastructure.provider import (
    InfrastructureFactoryDep,
    get_infrastructure_factory,
)


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


# Re-export from infrastructure layer
__all__ = ["InfrastructureFactoryDep", "get_infrastructure_factory"]
