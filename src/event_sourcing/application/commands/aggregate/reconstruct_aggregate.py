from pydantic import BaseModel


class ReconstructAggregateCommand(BaseModel):
    """Command to reconstruct an aggregate from events"""

    aggregate_id: str
    aggregate_type: str
    entity_name: str
