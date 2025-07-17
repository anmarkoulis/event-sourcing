import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select

from event_sourcing.application.queries.base import SearchClientsQuery
from event_sourcing.dto.client import ClientDTO
from event_sourcing.infrastructure.database.models.client import (
    Client as ClientModel,
)
from event_sourcing.infrastructure.database.session import (
    AsyncDBContextManager,
    DatabaseManager,
)

logger = logging.getLogger(__name__)


class ReadModel(ABC):
    """Abstract read model interface"""

    @abstractmethod
    async def save_client(self, client_data: Dict[str, Any]) -> None:
        """Save client to read model"""

    @abstractmethod
    async def search_clients(
        self, query: SearchClientsQuery
    ) -> List[ClientDTO]:
        """Search clients with filtering and pagination"""

    @abstractmethod
    async def get_client(self, client_id: str) -> Optional[ClientDTO]:
        """Get a specific client by ID"""

    @abstractmethod
    async def delete_client(self, client_id: str) -> None:
        """Delete client from read model"""


class PostgreSQLReadModel(ReadModel):
    """PostgreSQL implementation of read model"""

    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager

    async def save_client(self, client_data: Dict[str, Any]) -> None:
        """Save client to read model"""
        aggregate_id = client_data.get("aggregate_id")
        logger.info(f"Saving client {aggregate_id} to PostgreSQL")

        if not aggregate_id:
            logger.error(
                f"Cannot save client: aggregate_id is missing from data: {client_data}"
            )
            return

        async with AsyncDBContextManager(self.database_manager) as session:
            # Check if client exists
            existing_client = await session.execute(
                select(ClientModel).where(
                    ClientModel.aggregate_id == aggregate_id
                )
            )
            existing_client = existing_client.scalar_one_or_none()

            if existing_client:
                # Update existing client
                if client_data.get("name") is not None:
                    existing_client.name = client_data.get("name")
                if client_data.get("parent_id") is not None:
                    existing_client.parent_id = client_data.get("parent_id")
                if client_data.get("status") is not None:
                    existing_client.status = client_data.get("status")
                if client_data.get("external_id") is not None:
                    existing_client.external_id = client_data.get(
                        "external_id"
                    )
                existing_client.updated_at = datetime.utcnow()
            else:
                # Create new client
                client_model = ClientModel(
                    aggregate_id=aggregate_id,
                    external_id=client_data.get("external_id"),
                    name=client_data.get("name"),
                    parent_id=client_data.get("parent_id"),
                    status=client_data.get("status"),
                )
                session.add(client_model)

            await session.commit()
            logger.info(f"Client {aggregate_id} saved successfully")

    async def search_clients(
        self, query: SearchClientsQuery
    ) -> List[ClientDTO]:
        """Search clients with filtering and pagination"""
        logger.info(f"Searching clients with query: {query}")

        # Build base query
        base_query = select(ClientModel)

        # Add search filters
        if query.search_term:
            search_filter = or_(
                ClientModel.name.ilike(f"%{query.search_term}%")
            )
            base_query = base_query.where(search_filter)

        if query.status:
            base_query = base_query.where(ClientModel.status == query.status)

        # Add pagination
        offset = (query.page - 1) * query.page_size
        base_query = (
            base_query.order_by(ClientModel.created_at.desc())
            .offset(offset)
            .limit(query.page_size)
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(base_query)
            client_models = result.scalars().all()

            # Convert to DTOs
            client_dtos = []
            for client_model in client_models:
                client_dto = ClientDTO(
                    id=client_model.aggregate_id,
                    name=client_model.name,
                    parent_id=client_model.parent_id,
                    status=client_model.status,
                    created_at=client_model.created_at,
                    updated_at=client_model.updated_at,
                )
                client_dtos.append(client_dto)

            logger.info(f"Found {len(client_dtos)} clients")
            return client_dtos

    async def get_client(self, client_id: str) -> Optional[ClientDTO]:
        """Get a specific client by ID"""
        logger.info(f"Getting client {client_id}")

        query = select(ClientModel).where(
            ClientModel.aggregate_id == client_id
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(query)
            client_model = result.scalar_one_or_none()

            if not client_model:
                logger.info(f"Client {client_id} not found")
                return None

            client_dto = ClientDTO(
                id=client_model.aggregate_id,
                name=client_model.name,
                parent_id=client_model.parent_id,
                status=client_model.status,
                created_at=client_model.created_at,
                updated_at=client_model.updated_at,
            )

            logger.info(f"Retrieved client {client_id}")
            return client_dto

    async def delete_client(self, client_id: str) -> None:
        """Delete client from read model"""
        logger.info(f"Deleting client {client_id} from PostgreSQL")

        async with AsyncDBContextManager(self.database_manager) as session:
            # Find the client to delete
            result = await session.execute(
                select(ClientModel).where(
                    ClientModel.aggregate_id == client_id
                )
            )
            client_model = result.scalar_one_or_none()

            if client_model:
                # Delete the client
                await session.delete(client_model)
                await session.commit()
                logger.info(f"Client {client_id} deleted successfully")
            else:
                logger.warning(f"Client {client_id} not found for deletion")

    async def get_clients_by_status(
        self, status: str, limit: int = 100
    ) -> List[ClientDTO]:
        """Get clients by status"""
        logger.info(f"Getting {limit} clients with status {status}")

        query = (
            select(ClientModel)
            .where(ClientModel.status == status)
            .order_by(ClientModel.created_at.desc())
            .limit(limit)
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(query)
            client_models = result.scalars().all()

            client_dtos = []
            for client_model in client_models:
                client_dto = ClientDTO(
                    id=client_model.aggregate_id,
                    name=client_model.name,
                    parent_id=client_model.parent_id,
                    status=client_model.status,
                    created_at=client_model.created_at,
                    updated_at=client_model.updated_at,
                )
                client_dtos.append(client_dto)

            return client_dtos

    async def get_clients_by_parent(
        self, parent_id: str, limit: int = 100
    ) -> List[ClientDTO]:
        """Get clients by parent ID"""
        logger.info(f"Getting {limit} clients with parent {parent_id}")

        query = (
            select(ClientModel)
            .where(ClientModel.parent_id == parent_id)
            .order_by(ClientModel.created_at.desc())
            .limit(limit)
        )

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(query)
            client_models = result.scalars().all()

            client_dtos = []
            for client_model in client_models:
                client_dto = ClientDTO(
                    id=client_model.aggregate_id,
                    name=client_model.name,
                    parent_id=client_model.parent_id,
                    status=client_model.status,
                    created_at=client_model.created_at,
                    updated_at=client_model.updated_at,
                )
                client_dtos.append(client_dto)

            return client_dtos
