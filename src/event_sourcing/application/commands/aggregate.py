import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel

from .base import Command


class ReconstructAggregateCommandData(BaseModel):
    """Data for reconstructing an aggregate from events"""

    aggregate_id: str
    aggregate_type: str
    entity_name: str  # Salesforce entity name for mappings


class ReconstructAggregateCommand(Command):
    """Command to reconstruct an aggregate from events"""

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        aggregate_type: str,
        entity_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ReconstructAggregateCommand":
        """Create a reconstruct aggregate command"""
        data = ReconstructAggregateCommandData(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            entity_name=entity_name,
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="ReconstructAggregate",
            timestamp=datetime.utcnow(),
            data=data.dict(),
            metadata=metadata or {},
        )


class AsyncReconstructAggregateCommandData(BaseModel):
    """Data for asynchronously reconstructing an aggregate from events"""

    aggregate_id: str
    aggregate_type: str
    entity_name: str  # Salesforce entity name for mappings


class AsyncReconstructAggregateCommand(Command):
    """Command to asynchronously reconstruct an aggregate from events via Celery"""

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        aggregate_type: str,
        entity_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AsyncReconstructAggregateCommand":
        """Create an async reconstruct aggregate command"""
        data = AsyncReconstructAggregateCommandData(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            entity_name=entity_name,
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="AsyncReconstructAggregate",
            timestamp=datetime.utcnow(),
            data=data.dict(),
            metadata=metadata or {},
        )


class UpdateReadModelCommandData(BaseModel):
    """Data for updating read model with aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]


class UpdateReadModelCommand(Command):
    """Command to update read model with aggregate snapshot"""

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        aggregate_type: str,
        snapshot: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "UpdateReadModelCommand":
        """Create an update read model command"""
        data = UpdateReadModelCommandData(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot=snapshot,
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="UpdateReadModel",
            timestamp=datetime.utcnow(),
            data=data.dict(),
            metadata=metadata or {},
        )


class AsyncUpdateReadModelCommandData(BaseModel):
    """Data for asynchronously updating read model with aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]


class AsyncUpdateReadModelCommand(Command):
    """Command to asynchronously update read model with aggregate snapshot via Celery"""

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        aggregate_type: str,
        snapshot: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AsyncUpdateReadModelCommand":
        """Create an async update read model command"""
        data = AsyncUpdateReadModelCommandData(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot=snapshot,
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="AsyncUpdateReadModel",
            timestamp=datetime.utcnow(),
            data=data.dict(),
            metadata=metadata or {},
        )


class PublishSnapshotCommandData(BaseModel):
    """Data for publishing aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]
    event_type: str  # Created, Updated, Deleted


class PublishSnapshotCommand(Command):
    """Command to publish aggregate snapshot to external systems"""

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        aggregate_type: str,
        snapshot: Dict[str, Any],
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PublishSnapshotCommand":
        """Create a publish snapshot command"""
        data = PublishSnapshotCommandData(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot=snapshot,
            event_type=event_type,
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="PublishSnapshot",
            timestamp=datetime.utcnow(),
            data=data.dict(),
            metadata=metadata or {},
        )


class AsyncPublishSnapshotCommandData(BaseModel):
    """Data for asynchronously publishing aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]
    event_type: str  # Created, Updated, Deleted


class AsyncPublishSnapshotCommand(Command):
    """Command to asynchronously publish aggregate snapshot to external systems via Celery"""

    @classmethod
    def create(
        cls,
        aggregate_id: str,
        aggregate_type: str,
        snapshot: Dict[str, Any],
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AsyncPublishSnapshotCommand":
        """Create an async publish snapshot command"""
        data = AsyncPublishSnapshotCommandData(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot=snapshot,
            event_type=event_type,
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="AsyncPublishSnapshot",
            timestamp=datetime.utcnow(),
            data=data.dict(),
            metadata=metadata or {},
        )
