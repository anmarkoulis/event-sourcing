from pydantic import Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.dto.events.base import EventDTO
from event_sourcing.enums import EventType


class UsernameChangedDataV1(ModelConfigBaseModel):
    """Data for USERNAME_CHANGED event version 1"""

    old_username: str = Field(..., description="Previous username")
    new_username: str = Field(..., description="New username")


class UsernameChangedV1(EventDTO[UsernameChangedDataV1]):
    """USERNAME_CHANGED event version 1"""

    event_type: EventType = Field(
        default=EventType.USERNAME_CHANGED,
        description="Username changed event",
    )
    version: str = Field(default="1", description="Schema version")
    data: UsernameChangedDataV1 = Field(
        ..., description="Username change data"
    )
