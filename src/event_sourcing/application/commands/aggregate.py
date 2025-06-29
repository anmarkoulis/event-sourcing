from typing import Any, ClassVar, Dict, Optional, cast

from pydantic import BaseModel

from .base import Command


class ReconstructAggregateCommandData(BaseModel):
    """Data for reconstructing an aggregate from events"""

    aggregate_id: str
    aggregate_type: str
    entity_name: str  # Salesforce entity name for mappings


class ReconstructAggregateCommand(Command):
    """Command to reconstruct an aggregate from events"""

    COMMAND_TYPE: ClassVar[str] = "ReconstructAggregate"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ReconstructAggregateCommand":
        """Create a reconstruct aggregate command"""
        return cast(
            "ReconstructAggregateCommand",
            super().create(data=data, metadata=metadata),
        )


class AsyncReconstructAggregateCommandData(BaseModel):
    """Data for asynchronously reconstructing an aggregate from events"""

    aggregate_id: str
    aggregate_type: str
    entity_name: str  # Salesforce entity name for mappings


class AsyncReconstructAggregateCommand(Command):
    """Command to asynchronously reconstruct an aggregate from events via Celery"""

    COMMAND_TYPE: ClassVar[str] = "AsyncReconstructAggregate"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AsyncReconstructAggregateCommand":
        """Create an async reconstruct aggregate command"""
        return cast(
            "AsyncReconstructAggregateCommand",
            super().create(data=data, metadata=metadata),
        )


class UpdateReadModelCommandData(BaseModel):
    """Data for updating read model with aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]


class UpdateReadModelCommand(Command):
    """Command to update read model with aggregate snapshot"""

    COMMAND_TYPE: ClassVar[str] = "UpdateReadModel"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "UpdateReadModelCommand":
        """Create an update read model command"""
        return cast(
            "UpdateReadModelCommand",
            super().create(data=data, metadata=metadata),
        )


class AsyncUpdateReadModelCommandData(BaseModel):
    """Data for asynchronously updating read model with aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]


class AsyncUpdateReadModelCommand(Command):
    """Command to asynchronously update read model with aggregate snapshot via Celery"""

    COMMAND_TYPE: ClassVar[str] = "AsyncUpdateReadModel"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AsyncUpdateReadModelCommand":
        """Create an async update read model command"""
        return cast(
            "AsyncUpdateReadModelCommand",
            super().create(data=data, metadata=metadata),
        )


class PublishSnapshotCommandData(BaseModel):
    """Data for publishing aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]
    event_type: str  # Created, Updated, Deleted


class PublishSnapshotCommand(Command):
    """Command to publish aggregate snapshot to external systems"""

    COMMAND_TYPE: ClassVar[str] = "PublishSnapshot"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PublishSnapshotCommand":
        """Create a publish snapshot command"""
        return cast(
            "PublishSnapshotCommand",
            super().create(data=data, metadata=metadata),
        )


class AsyncPublishSnapshotCommandData(BaseModel):
    """Data for asynchronously publishing aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]
    event_type: str  # Created, Updated, Deleted


class AsyncPublishSnapshotCommand(Command):
    """Command to asynchronously publish aggregate snapshot to external systems via Celery"""

    COMMAND_TYPE: ClassVar[str] = "AsyncPublishSnapshot"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AsyncPublishSnapshotCommand":
        """Create an async publish snapshot command"""
        return cast(
            "AsyncPublishSnapshotCommand",
            super().create(data=data, metadata=metadata),
        )
