from enum import Enum


class EventSourceEnum(str, Enum):
    """Enum for event sources"""

    SALESFORCE = "SALESFORCE"
