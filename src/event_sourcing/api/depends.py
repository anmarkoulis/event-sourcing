from event_sourcing.infrastructure.provider import (
    InfrastructureFactoryDep,
    get_infrastructure_factory,
)

# Re-export from infrastructure layer
__all__ = ["InfrastructureFactoryDep", "get_infrastructure_factory"]
