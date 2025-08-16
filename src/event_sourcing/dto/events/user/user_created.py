from pydantic import Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.dto.events.base import EventDTO
from event_sourcing.enums import EventType, HashingMethod, Role


class UserCreatedDataV1(ModelConfigBaseModel):
    """Data for USER_CREATED event version 1"""

    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    password_hash: str = Field(..., description="Hashed password")
    hashing_method: HashingMethod = Field(
        ..., description="Hashing method used"
    )
    role: Role = Field(default=Role.USER, description="User role")


class UserCreatedV1(EventDTO[UserCreatedDataV1]):
    """USER_CREATED event version 1"""

    event_type: EventType = Field(
        default=EventType.USER_CREATED, description="User created event"
    )
    version: str = Field(default="1", description="Schema version")
    data: UserCreatedDataV1 = Field(..., description="User creation data")
