from pydantic import BaseModel


class AsyncReconstructAggregateCommand(BaseModel):
    """Command to asynchronously reconstruct an aggregate from events via Celery"""

    aggregate_id: str
    aggregate_type: str
    entity_name: str
