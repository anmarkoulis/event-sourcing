import logging
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Optional, Type

logger = logging.getLogger(__name__)


class BaseUnitOfWork(ABC):
    """Abstract Unit of Work for transaction management"""

    async def __aenter__(self) -> "BaseUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if exc:
            logger.warning(f"Caught exception {exc}")
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> Any:  # pragma nocover
        ...

    @abstractmethod
    async def rollback(self) -> Any:  # pragma nocover
        ...
