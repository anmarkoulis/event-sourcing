from typing import Annotated, Any

from fastapi import Depends

from event_sourcing.application.commands.handlers.async_process_salesforce_event import (
    AsyncProcessSalesforceEventCommandHandler,
)
from event_sourcing.application.commands.handlers.process_salesforce_event import (
    ProcessSalesforceEventCommandHandler,
)
from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.infrastructure.factory import InfrastructureFactory


class DependencyService:
    """Service for providing command handlers and other dependencies"""

    @staticmethod
    def get_process_salesforce_event_command_handler(
        infrastructure_factory: Annotated[
            InfrastructureFactory, Depends(get_infrastructure_factory)
        ],
    ) -> ProcessSalesforceEventCommandHandler:
        """Get ProcessSalesforceEventCommandHandler with all dependencies"""
        event_store = infrastructure_factory.event_store
        read_model = infrastructure_factory.read_model
        event_publisher = infrastructure_factory.event_publisher

        return ProcessSalesforceEventCommandHandler(
            event_store=event_store,
            read_model=read_model,
            event_publisher=event_publisher,
        )

    @staticmethod
    def get_async_process_salesforce_event_command_handler() -> (
        AsyncProcessSalesforceEventCommandHandler
    ):
        """Get AsyncProcessSalesforceEventCommandHandler (no dependencies needed)"""
        return AsyncProcessSalesforceEventCommandHandler()

    @staticmethod
    def get_read_model(
        infrastructure_factory: Annotated[
            InfrastructureFactory, Depends(get_infrastructure_factory)
        ],
    ) -> Any:
        """Get read model from infrastructure factory"""
        return infrastructure_factory.read_model
