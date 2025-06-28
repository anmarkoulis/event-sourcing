from typing import Dict, Type

from .base import BaseMappings
from .client import ClientMappings


class MappingRegistry:
    """Central registry for all entity mappings"""

    _mappings: Dict[str, Type[BaseMappings]] = {
        "Account": ClientMappings,
        # Add other entity mappings as they are implemented
        # "Platform__c": PlatformMappings,
        # "Contract": ContractMappings,
        # "Opportunity": DealMappings,
        # "OpportunityLineItem": ServiceMappings,
        # "Product2": SubserviceMappings,
    }

    @classmethod
    def get_mappings(cls, entity_name: str) -> Type[BaseMappings]:
        """Get mappings class for entity name"""
        return cls._mappings.get(entity_name)

    @classmethod
    def get_normalized_entity_name(cls, entity_name: str) -> str:
        """Get normalized entity name from Salesforce entity name"""
        normalization_dict = {
            "Account": "client",
            "Platform__c": "platform",
            "Contract": "contract",
            "Opportunity": "deal",
            "OpportunityLineItem": "service",
            "Product2": "subservice",
        }
        return normalization_dict.get(entity_name, entity_name.lower())

    @classmethod
    def register_mappings(
        cls, entity_name: str, mappings_class: Type[BaseMappings]
    ) -> None:
        """Register new mappings for an entity"""
        cls._mappings[entity_name] = mappings_class

    @classmethod
    def list_entities(cls) -> list:
        """List all registered entity names"""
        return list(cls._mappings.keys())
