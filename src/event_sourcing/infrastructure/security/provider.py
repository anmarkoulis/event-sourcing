"""Authentication service dependency provider."""

from typing import Annotated

from fastapi import Depends

from event_sourcing.infrastructure.factory import InfrastructureFactory
from event_sourcing.infrastructure.provider import get_infrastructure_factory

from .services import AuthServiceInterface


def get_auth_service(
    infrastructure_factory: InfrastructureFactory = Depends(
        get_infrastructure_factory
    ),
) -> AuthServiceInterface:
    """Get authentication service instance - FastAPI dependency.

    :param infrastructure_factory: Infrastructure factory.
    :return: Authentication service instance.
    """
    return infrastructure_factory.get_auth_service()  # type: ignore[no-any-return]


# Type aliases for FastAPI dependency injection
AuthServiceDep = Annotated[AuthServiceInterface, Depends(get_auth_service)]
