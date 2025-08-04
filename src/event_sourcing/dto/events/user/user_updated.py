from typing import Optional

from pydantic import Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.dto.events.base import EventDTO
from event_sourcing.enums import EventType


class UserUpdatedDataV1(ModelConfigBaseModel):
    """Data for USER_UPDATED event version 1"""

    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    email: Optional[str] = Field(None, description="Email address")


class UserUpdatedV1(EventDTO[UserUpdatedDataV1]):
    """USER_UPDATED event version 1"""

    event_type: EventType = Field(
        default=EventType.USER_UPDATED, description="User updated event"
    )
    version: str = Field(default="1", description="Schema version")
    data: UserUpdatedDataV1 = Field(..., description="User update data")
