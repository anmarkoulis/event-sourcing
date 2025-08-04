from pydantic import Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.dto.events.base import EventDTO
from event_sourcing.enums import EventType


class UserDeletedDataV1(ModelConfigBaseModel):
    """Data for USER_DELETED event version 1"""

    # No additional data needed for deletion


class UserDeletedV1(EventDTO[UserDeletedDataV1]):
    """USER_DELETED event version 1"""

    event_type: EventType = Field(
        default=EventType.USER_DELETED, description="User deleted event"
    )
    version: str = Field(default="1", description="Schema version")
    data: UserDeletedDataV1 = Field(..., description="User deletion data")
