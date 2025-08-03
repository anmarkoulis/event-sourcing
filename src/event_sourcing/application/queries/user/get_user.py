import uuid

from pydantic import BaseModel


class GetUserQuery(BaseModel):
    """Query to get user by ID"""

    user_id: uuid.UUID
