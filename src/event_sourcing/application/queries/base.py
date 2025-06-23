from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class Query(BaseModel):
    """Base query for all read operations"""
    pass


class SearchClientsQuery(Query):
    """Query for searching clients"""
    search_term: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20


class GetClientQuery(Query):
    """Query for getting a specific client"""
    client_id: str


class GetClientHistoryQuery(Query):
    """Query for getting client event history"""
    client_id: str
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class GetBackfillStatusQuery(Query):
    """Query for getting backfill status"""
    entity_type: str 