from event_sourcing.config.settings import settings
from event_sourcing.infrastructure.factory import InfrastructureFactory


def get_infrastructure_factory() -> InfrastructureFactory:
    """Get infrastructure factory instance"""
    return InfrastructureFactory(
        database_url=settings.DATABASE_URL,
        eventbridge_region=getattr(
            settings, "EVENTBRIDGE_REGION", "us-east-1"
        ),
    )
