"""Session manager for database session lifecycle."""

import logging
from typing import Any, Optional

from event_sourcing.infrastructure.database.session import DatabaseManager

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages database session creation and lifecycle"""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager = database_manager
        self._session: Optional[Any] = None

    async def get_session(self) -> Any:
        """Get or create a database session"""
        if self._session is None:
            self._session = await self.database_manager.get_session()
        return self._session

    async def close_session(self) -> None:
        """Close the current session"""
        if self._session:
            await self._session.close()
            self._session = None
