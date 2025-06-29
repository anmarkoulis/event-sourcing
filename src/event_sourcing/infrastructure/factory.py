import logging
from typing import Any, Optional

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
        self._projection_manager: Optional[Any] = None
        self._salesforce_client: Optional[Any] = None

    @property
    def database_manager(self) -> DatabaseManager:
        """Get or create database manager"""
        if self._database_manager is None:
            logger.info("Creating database manager")
            self._database_manager = DatabaseManager(self.database_url)
        return self._database_manager

    @property
    def read_model(self) -> PostgreSQLReadModel:
        """Get or create read model"""
        if self._read_model is None:
            logger.info("Creating read model")
            self._read_model = PostgreSQLReadModel(self.database_manager)
        return self._read_model

    @property
    def salesforce_client(self) -> Optional[Any]:
        """Get Salesforce client (returns None if not configured)"""
        # In a real implementation, this would create and configure a Salesforce client
        # For now, return None to indicate it's not available
        return self._salesforce_client

    @property
    def projection_manager(self) -> Any:
        """Get or create projection manager"""
        if self._projection_manager is None:
            logger.info("Creating projection manager")
            from event_sourcing.application.projections.projection_manager import (
                ProjectionManager,
            )

            self._projection_manager = ProjectionManager(
                read_model=self.read_model,
                event_publisher=self.event_publisher,
            )
        return self._projection_manager

    @property
    def event_store(self) -> PostgreSQLEventStore:
        """Get or create event store with projection manager"""
        if self._event_store is None:
            logger.info("Creating event store with projection manager")
            self._event_store = PostgreSQLEventStore(
                self.database_manager, self.projection_manager
            )
        return self._event_store

    @property
    def event_publisher(self) -> EventBridgePublisher:
        """Get or create event publisher"""
        if self._event_publisher is None:
            logger.info("Creating event publisher")
            self._event_publisher = EventBridgePublisher(
                self.eventbridge_region
            )
        return self._event_publisher

    async def close(self) -> None:
        """Close all infrastructure components"""
        logger.info("Closing infrastructure components")

        if self._database_manager:
            await self._database_manager.close()
            self._database_manager = None

        self._event_store = None
        self._read_model = None
        self._event_publisher = None
        self._projection_manager = None

        logger.info("Infrastructure components closed")
