from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variables for queries and results
QueryType = TypeVar("QueryType")
ResultType = TypeVar("ResultType")


class QueryHandler(ABC, Generic[QueryType, ResultType]):
    """Base interface for query handlers"""

    @abstractmethod
    async def handle(self, query: QueryType) -> ResultType:
        """Handle a query and return the result"""
