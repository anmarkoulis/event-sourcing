from typing import Dict, Type, Optional
from .base import BaseAggregate
from .client import ClientAggregate
import logging

logger = logging.getLogger(__name__)


class AggregateRegistry:
    """Registry for aggregate classes"""
    
    _aggregates: Dict[str, Type[BaseAggregate]] = {
        "client": ClientAggregate,
        # Add more aggregates here as they are created
        # "order": OrderAggregate,
        # "product": ProductAggregate,
    }
    
    @classmethod
    def get_aggregate(cls, aggregate_type: str) -> Optional[Type[BaseAggregate]]:
        """Get aggregate class by type"""
        aggregate_class = cls._aggregates.get(aggregate_type)
        if not aggregate_class:
            logger.error(f"No aggregate class registered for type: {aggregate_type}")
            return None
        return aggregate_class
    
    @classmethod
    def register(cls, aggregate_type: str, aggregate_class: Type[BaseAggregate]) -> None:
        """Register an aggregate class"""
        cls._aggregates[aggregate_type] = aggregate_class
        logger.info(f"Registered aggregate class: {aggregate_type} -> {aggregate_class.__name__}")
    
    @classmethod
    def list_aggregates(cls) -> Dict[str, Type[BaseAggregate]]:
        """List all registered aggregates"""
        return cls._aggregates.copy() 