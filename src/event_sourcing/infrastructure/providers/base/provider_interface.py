from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from event_sourcing.dto.event import EventDTO


class CRMProviderInterface(ABC):
    """Abstract interface for CRM providers"""

    @abstractmethod
    async def get_entity(
        self, entity_id: str, entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch entity from CRM"""

    @abstractmethod
    def create_event_dto(self, raw_event: Dict[str, Any]) -> EventDTO:
        """Create EventDTO directly from raw CRM event"""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider"""

    def set_client(self, client: Any) -> None:
        """Set the CRM client (optional method for providers that need it)"""
