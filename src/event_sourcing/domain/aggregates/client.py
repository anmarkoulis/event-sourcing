from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .salesforce import SalesforceAggregate
from ..events.base import DomainEvent
from ..events.client import ClientCreatedEvent, ClientUpdatedEvent, ClientDeletedEvent

logger = logging.getLogger(__name__)


class ClientAggregate(SalesforceAggregate):
    """Client domain aggregate - encapsulates client business logic"""
    
    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id, "Account")
        
        # Client-specific attributes
        self.name: Optional[str] = None
        self.parent_id: Optional[str] = None
        self.business_types: Optional[List[str]] = None
        self.status: Optional[str] = None
        self.currency: Optional[str] = None
        self.billing_country: Optional[str] = None
        self.priority: Optional[str] = None
        self.sso_id: Optional[str] = None
        self.sso_id_c: Optional[str] = None
        self.sso_id_r: Optional[str] = None
        self.description: Optional[str] = None
        self.last_modified_date: Optional[datetime] = None
        self.system_modified_stamp: Optional[datetime] = None
        self.last_activity_date: Optional[datetime] = None
    
    def apply(self, event: DomainEvent) -> None:
        """Apply a domain event to the client aggregate state"""
        if event.event_type == "Created":
            self._apply_created_event(event)
        elif event.event_type == "Updated":
            self._apply_updated_event(event)
        elif event.event_type == "Deleted":
            self._apply_deleted_event(event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")
        
        self.increment_version()
    
    def create_from_salesforce(self, data: dict) -> None:
        """Create client from Salesforce data"""
        mapped_data = self.apply_mappings(data)
        
        # Apply mapped data to aggregate state
        self.name = mapped_data.get("name")
        self.parent_id = mapped_data.get("parent_id")
        self.business_types = mapped_data.get("business_types")
        self.status = mapped_data.get("status")
        self.currency = mapped_data.get("currency")
        self.billing_country = mapped_data.get("billing_country")
        self.priority = mapped_data.get("priority")
        self.sso_id = mapped_data.get("sso_id")
        self.sso_id_c = mapped_data.get("sso_id_c")
        self.sso_id_r = mapped_data.get("sso_id_r")
        self.description = mapped_data.get("description")
        self.last_modified_date = mapped_data.get("last_modified_date")
        self.system_modified_stamp = mapped_data.get("system_modified_stamp")
        self.last_activity_date = mapped_data.get("last_activity_date")
        
        # Set creation timestamp
        created_date = mapped_data.get("created_date")
        if created_date:
            self.set_created_at(created_date)
        else:
            self.set_created_at(datetime.utcnow())
        
        self.increment_version()
    
    def update_from_salesforce(self, data: dict) -> None:
        """Update client from Salesforce data"""
        mapped_data = self.apply_mappings(data)
        
        # Update only provided fields
        if "name" in mapped_data:
            self.name = mapped_data["name"]
        if "parent_id" in mapped_data:
            self.parent_id = mapped_data["parent_id"]
        if "business_types" in mapped_data:
            self.business_types = mapped_data["business_types"]
        if "status" in mapped_data:
            self.status = mapped_data["status"]
        if "currency" in mapped_data:
            self.currency = mapped_data["currency"]
        if "billing_country" in mapped_data:
            self.billing_country = mapped_data["billing_country"]
        if "priority" in mapped_data:
            self.priority = mapped_data["priority"]
        if "sso_id" in mapped_data:
            self.sso_id = mapped_data["sso_id"]
        if "sso_id_c" in mapped_data:
            self.sso_id_c = mapped_data["sso_id_c"]
        if "sso_id_r" in mapped_data:
            self.sso_id_r = mapped_data["sso_id_r"]
        if "description" in mapped_data:
            self.description = mapped_data["description"]
        if "last_modified_date" in mapped_data:
            self.last_modified_date = mapped_data["last_modified_date"]
        if "system_modified_stamp" in mapped_data:
            self.system_modified_stamp = mapped_data["system_modified_stamp"]
        if "last_activity_date" in mapped_data:
            self.last_activity_date = mapped_data["last_activity_date"]
        
        self.increment_version()
    
    def delete_from_salesforce(self, data: dict) -> None:
        """Mark client as deleted from Salesforce data"""
        self.is_deleted = True
        self.increment_version()
    
    def _apply_created_event(self, event: DomainEvent) -> None:
        """Apply client created event"""
        data = event.data
        self.name = data.get("name")
        self.parent_id = data.get("parent_id")
        self.business_types = data.get("business_types")
        self.status = data.get("status")
        self.currency = data.get("currency")
        self.billing_country = data.get("billing_country")
        self.priority = data.get("priority")
        self.sso_id = data.get("sso_id")
        self.sso_id_c = data.get("sso_id_c")
        self.sso_id_r = data.get("sso_id_r")
        self.description = data.get("description")
        self.last_modified_date = data.get("last_modified_date")
        self.system_modified_stamp = data.get("system_modified_stamp")
        self.last_activity_date = data.get("last_activity_date")
        
        # Set creation timestamp
        created_date = data.get("created_date")
        if created_date:
            self.set_created_at(created_date)
        else:
            self.set_created_at(event.timestamp)
    
    def _apply_updated_event(self, event: DomainEvent) -> None:
        """Apply client updated event"""
        data = event.data
        # Update only provided fields (same logic as update_from_salesforce)
        if "name" in data:
            self.name = data["name"]
        if "parent_id" in data:
            self.parent_id = data["parent_id"]
        if "business_types" in data:
            self.business_types = data["business_types"]
        if "status" in data:
            self.status = data["status"]
        if "currency" in data:
            self.currency = data["currency"]
        if "billing_country" in data:
            self.billing_country = data["billing_country"]
        if "priority" in data:
            self.priority = data["priority"]
        if "sso_id" in data:
            self.sso_id = data["sso_id"]
        if "sso_id_c" in data:
            self.sso_id_c = data["sso_id_c"]
        if "sso_id_r" in data:
            self.sso_id_r = data["sso_id_r"]
        if "description" in data:
            self.description = data["description"]
        if "last_modified_date" in data:
            self.last_modified_date = data["last_modified_date"]
        if "system_modified_stamp" in data:
            self.system_modified_stamp = data["system_modified_stamp"]
        if "last_activity_date" in data:
            self.last_activity_date = data["last_activity_date"]
    
    def _apply_deleted_event(self, event: DomainEvent) -> None:
        """Apply client deleted event"""
        self.is_deleted = True
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Return current client state snapshot"""
        base_snapshot = super().get_snapshot()
        client_snapshot = {
            "name": self.name,
            "parent_id": self.parent_id,
            "business_types": self.business_types,
            "status": self.status,
            "currency": self.currency,
            "billing_country": self.billing_country,
            "priority": self.priority,
            "sso_id": self.sso_id,
            "sso_id_c": self.sso_id_c,
            "sso_id_r": self.sso_id_r,
            "description": self.description,
            "last_modified_date": self.last_modified_date,
            "system_modified_stamp": self.system_modified_stamp,
            "last_activity_date": self.last_activity_date,
        }
        return {**base_snapshot, **client_snapshot} 