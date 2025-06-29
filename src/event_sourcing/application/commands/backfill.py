from pydantic import BaseModel


class BackfillEntityTypeCommand(BaseModel):
    """Command to backfill all entities of a specific type"""

    entity_name: str
    page: int = 1
    page_size: int = 50
    source: str = "backfill"


class BackfillSpecificEntityCommand(BaseModel):
    """Command to backfill a specific entity"""

    aggregate_id: str
    aggregate_type: str
    source: str = "backfill"


class BackfillEntityPageCommand(BaseModel):
    """Command to backfill a specific page of entities"""

    entity_name: str
    page: int
    page_size: int
    source: str = "backfill"
