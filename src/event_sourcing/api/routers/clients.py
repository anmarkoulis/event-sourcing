import logging
from typing import Any, Dict

from fastapi import APIRouter

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.application.queries.base import SearchClientsQuery

logger = logging.getLogger(__name__)

clients_router = APIRouter(prefix="/clients", tags=["clients"])


@clients_router.get("/", description="Get all clients from read model")
async def get_clients(
    infrastructure_factory: InfrastructureFactoryDep,
) -> Dict[str, Any]:
    """
    Get all clients from the read model to see the results of event processing.
    """
    # Get read model from infrastructure factory
    read_model = infrastructure_factory.read_model

    # Create a simple search query to get all clients
    query = SearchClientsQuery(
        search_term="", status=None, page=1, page_size=100
    )

    clients = await read_model.search_clients(query)

    return {
        "status": "success",
        "count": len(clients),
        "clients": [client.dict() for client in clients],
    }
