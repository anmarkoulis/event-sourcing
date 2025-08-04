from pydantic import Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.dto.events.base import EventDTO
from event_sourcing.enums import EventType


class PasswordChangedDataV1(ModelConfigBaseModel):
    """Data for PASSWORD_CHANGED event version 1"""

    password_hash: str = Field(..., description="New hashed password")


class PasswordChangedV1(EventDTO[PasswordChangedDataV1]):
    """PASSWORD_CHANGED event version 1"""

    event_type: EventType = Field(
        default=EventType.PASSWORD_CHANGED,
        description="Password changed event",
    )
    version: str = Field(default="1", description="Schema version")
    data: PasswordChangedDataV1 = Field(
        ..., description="Password change data"
    )
