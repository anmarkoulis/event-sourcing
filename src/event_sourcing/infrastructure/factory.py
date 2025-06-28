import logging
from typing import Optional

from .database.session import DatabaseManager
from .event_store import PostgreSQLEventStore
from .messaging import EventBridgePublisher
from .read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class InfrastructureFactory:
    """Factory for creating infrastructure components"""

    def __init__(
        self, database_url: str, eventbridge_region: str = "us-east-1"
    ):
        self.database_url = database_url
        self.eventbridge_region = eventbridge_region
        self._database_manager: Optional[DatabaseManager] = None
        self._event_store: Optional[PostgreSQLEventStore] = None
        self._read_model: Optional[PostgreSQLReadModel] = None
        self._event_publisher: Optional[EventBridgePublisher] = None

    @property
    def database_manager(self) -> DatabaseManager:
        """Get or create database manager"""
        if self._database_manager is None:
            logger.info("Creating database manager")
            self._database_manager = DatabaseManager(self.database_url)
        return self._database_manager

    @property
    def event_store(self) -> PostgreSQLEventStore:
        """Get or create event store"""
        if self._event_store is None:
            logger.info("Creating event store")
            self._event_store = PostgreSQLEventStore(self.database_manager)
        return self._event_store

    @property
    def read_model(self) -> PostgreSQLReadModel:
        """Get or create read model"""
        if self._read_model is None:
            logger.info("Creating read model")
            self._read_model = PostgreSQLReadModel(self.database_manager)
        return self._read_model

    @property
    def event_publisher(self) -> EventBridgePublisher:
        """Get or create event publisher"""
        if self._event_publisher is None:
            logger.info("Creating event publisher")
            self._event_publisher = EventBridgePublisher(
                self.eventbridge_region
            )
        return self._event_publisher

    async def close(self):
        """Close all infrastructure components"""
        logger.info("Closing infrastructure components")

        if self._database_manager:
            await self._database_manager.close()
            self._database_manager = None

        self._event_store = None
        self._read_model = None
        self._event_publisher = None

        logger.info("Infrastructure components closed")
