from pydantic import BaseModel


class BackfillEntityTypeCommand(BaseModel):
    """Command to backfill an entity type"""

    entity_name: str
