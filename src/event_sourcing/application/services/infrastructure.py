from ...infrastructure.factory import InfrastructureFactory
from ...config.settings import settings


def get_infrastructure_factory() -> InfrastructureFactory:
    """Get infrastructure factory instance"""
    return InfrastructureFactory(
        database_url=settings.DATABASE_URL,
        eventbridge_region=getattr(settings, "EVENTBRIDGE_REGION", "us-east-1")
    ) 