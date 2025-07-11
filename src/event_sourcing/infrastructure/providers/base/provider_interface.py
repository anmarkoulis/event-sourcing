from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from event_sourcing.domain.events.base import DomainEvent


class CRMProviderInterface(ABC):
    """Abstract interface for CRM providers"""

    @abstractmethod
    async def get_entity(
        self, entity_id: str, entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch entity from CRM"""

    @abstractmethod
    def parse_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CRM-specific event format to common format"""

    @abstractmethod
    def translate_to_domain_event(
        self, parsed_event: Dict[str, Any]
    ) -> DomainEvent:
        """Transform parsed event to domain event"""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider"""

    def set_client(self, client: Any) -> None:
        """Set the CRM client (optional method for providers that need it)"""
