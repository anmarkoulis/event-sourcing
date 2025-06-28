import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from event_sourcing.domain.events.base import DomainEvent

logger = logging.getLogger(__name__)


class BaseAggregate(ABC):
    """Base aggregate interface for all domain aggregates"""

    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None

    @abstractmethod
    def apply(self, event: DomainEvent) -> None:
        """Apply a domain event to the aggregate state"""

    @abstractmethod
    def get_snapshot(self) -> Dict[str, Any]:
        """Return current state snapshot"""

    @abstractmethod
    def validate_event_ordering(self, event: DomainEvent) -> bool:
        """Validate event ordering and consistency"""

    def increment_version(self) -> None:
        """Increment aggregate version"""
        self.version += 1
        self.updated_at = datetime.utcnow()

    def set_created_at(self, timestamp: datetime) -> None:
        """Set creation timestamp"""
        if not self.created_at:
            self.created_at = timestamp
