from typing import Dict, Any, Callable
from collections import namedtuple
from abc import ABC, abstractmethod

MappedField = namedtuple("MappedField", ["value", "operation"])


class BaseMappings(ABC):
    """Base class for all entity mappings"""
    
    @staticmethod
    @abstractmethod
    def get_mappings() -> Dict[str, MappedField]:
        """Return field mappings for the entity"""
        pass


def get_date_time(raw_data: dict, field_name: str) -> Any:
    """Convert string to datetime if possible"""
    value = raw_data.get(field_name)
    if isinstance(value, str):
        try:
            from datetime import datetime
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value
    return value


def get_date(raw_data: dict, field_name: str) -> Any:
    """Convert string to date if possible"""
    value = raw_data.get(field_name)
    if isinstance(value, str):
        try:
            from datetime import date
            return date.fromisoformat(value)
        except ValueError:
            return value
    return value


def get_list_from_string(raw_data: dict, field_name: str) -> Any:
    """Convert semicolon-separated string to list"""
    value = raw_data.get(field_name)
    if isinstance(value, str) and ';' in value:
        return [item.strip() for item in value.split(';') if item.strip()]
    return value 