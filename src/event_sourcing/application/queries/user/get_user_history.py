import uuid
from datetime import datetime

from pydantic import BaseModel


class GetUserHistoryQuery(BaseModel):
    """Query to get user state at a specific point in time"""

    user_id: uuid.UUID
    timestamp: datetime
