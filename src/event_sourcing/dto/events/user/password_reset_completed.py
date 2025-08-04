from pydantic import Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.dto.events.base import EventDTO
from event_sourcing.enums import EventType


class PasswordResetCompletedDataV1(ModelConfigBaseModel):
    """Data for PASSWORD_RESET_COMPLETED event version 1"""

    password_hash: str = Field(..., description="New hashed password")
    reset_token: str = Field(..., description="Reset token used")


class PasswordResetCompletedV1(EventDTO[PasswordResetCompletedDataV1]):
    """PASSWORD_RESET_COMPLETED event version 1"""

    event_type: EventType = Field(
        default=EventType.PASSWORD_RESET_COMPLETED,
        description="Password reset completed event",
    )
    version: str = Field(default="1", description="Schema version")
    data: PasswordResetCompletedDataV1 = Field(
        ..., description="Password reset completion data"
    )
