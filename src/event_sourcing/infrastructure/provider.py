from typing import Annotated

from fastapi import Depends

from event_sourcing.config.settings import settings
from event_sourcing.infrastructure.factory import InfrastructureFactory


def get_infrastructure_factory() -> InfrastructureFactory:
    """Get infrastructure factory instance - FastAPI dependency"""
    return InfrastructureFactory(
        database_url=settings.DATABASE_URL,
    )


# Type aliases for FastAPI dependency injection
InfrastructureFactoryDep = Annotated[
    InfrastructureFactory, Depends(get_infrastructure_factory)
]
