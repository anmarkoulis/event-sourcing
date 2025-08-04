from pydantic import Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.dto.events.base import EventDTO
from event_sourcing.enums import EventType


class PasswordResetRequestedDataV1(ModelConfigBaseModel):
    """Data for PASSWORD_RESET_REQUESTED event version 1"""

    # No additional data needed for password reset request


class PasswordResetRequestedV1(EventDTO[PasswordResetRequestedDataV1]):
    """PASSWORD_RESET_REQUESTED event version 1"""

    event_type: EventType = Field(
        default=EventType.PASSWORD_RESET_REQUESTED,
        description="Password reset requested event",
    )
    version: str = Field(default="1", description="Schema version")
    data: PasswordResetRequestedDataV1 = Field(
        ..., description="Password reset request data"
    )
