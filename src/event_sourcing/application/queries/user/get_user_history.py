import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GetUserHistoryQuery(BaseModel):
    """Query to get user event history"""

    user_id: uuid.UUID
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
