from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from ..depends import DependencyService
from ...application.queries.base import SearchClientsQuery

logger = logging.getLogger(__name__)

clients_router = APIRouter(prefix="/clients", tags=["clients"])


@clients_router.get("/", description="Get all clients from read model")
async def get_clients(
    read_model = Depends(DependencyService.get_read_model)
) -> Dict[str, Any]:
    """
    Get all clients from the read model to see the results of event processing.
    """
    # Create a simple search query to get all clients
    query = SearchClientsQuery(search_term="", status=None, page=1, page_size=100)
    
    clients = await read_model.search_clients(query)
    
    return {
        "status": "success",
        "count": len(clients),
        "clients": [client.dict() for client in clients]
    } 