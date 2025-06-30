import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.application.queries.base import (
    GetClientHistoryQuery,
    GetClientQuery,
    SearchClientsQuery,
)

logger = logging.getLogger(__name__)

clients_router = APIRouter(prefix="/clients", tags=["clients"])


@clients_router.get("/", description="Search clients from read model")
async def search_clients(
    search_term: Optional[str] = Query(
        None, description="Search term for client name"
    ),
    status: Optional[str] = Query(None, description="Filter by client status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
    """
    Search clients from the read model with filtering and pagination.
    """
    # Create query handler using factory method
    query_handler = (
        infrastructure_factory.create_search_clients_query_handler()
    )

    # Create query object
    query = SearchClientsQuery(
        search_term=search_term,
        status=status,
        page=page,
        page_size=page_size,
    )

    # Execute query
    clients = await query_handler.handle(query)

    return {
        "status": "success",
        "count": len(clients),
        "page": page,
        "page_size": page_size,
        "clients": [client.dict() for client in clients],
    }


@clients_router.get("/{client_id}", description="Get specific client by ID")
async def get_client(
    client_id: str,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
    """
    Get a specific client by ID from the read model.
    """
    # Create query handler using factory method
    query_handler = infrastructure_factory.create_get_client_query_handler()

    # Create query object
    query = GetClientQuery(client_id=client_id)

    # Execute query
    client = await query_handler.handle(query)

    if not client:
        return {
            "status": "error",
            "message": f"Client not found: {client_id}",
        }

    return {
        "status": "success",
        "client": client.dict(),
    }


@clients_router.get(
    "/{client_id}/history", description="Get client event history"
)
async def get_client_history(
    client_id: str,
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
    """
    Get event history for a specific client from the event store.
    """
    # Create query handler using factory method
    query_handler = (
        infrastructure_factory.create_get_client_history_query_handler()
    )

    # Parse dates if provided
    from_date_parsed = None
    to_date_parsed = None

    if from_date:
        from datetime import datetime

        from_date_parsed = datetime.fromisoformat(
            from_date.replace("Z", "+00:00")
        )

    if to_date:
        from datetime import datetime

        to_date_parsed = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

    # Create query object
    query = GetClientHistoryQuery(
        client_id=client_id,
        from_date=from_date_parsed,
        to_date=to_date_parsed,
    )

    # Execute query
    events = await query_handler.handle(query)

    return {
        "status": "success",
        "client_id": client_id,
        "count": len(events),
        "events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "metadata": event.metadata,
            }
            for event in events
        ],
    }
