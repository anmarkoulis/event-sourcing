from typing import Annotated
from fastapi import Depends

from ...infrastructure.factory import InfrastructureFactory
from ...config.settings import settings
from ..commands.handlers.process_salesforce_event import ProcessSalesforceEventCommandHandler
from ..services.backfill import BackfillService


def get_infrastructure_factory() -> InfrastructureFactory:
    """Get infrastructure factory instance"""
    return InfrastructureFactory(
        database_url=settings.DATABASE_URL,
        eventbridge_region=getattr(settings, "EVENTBRIDGE_REGION", "us-east-1")
    )


class DependencyService:
    """Service for providing command handlers and other dependencies"""
    
    @staticmethod
    def get_process_salesforce_event_command_handler(
        infrastructure_factory: Annotated[InfrastructureFactory, Depends(get_infrastructure_factory)]
    ) -> ProcessSalesforceEventCommandHandler:
        """Get ProcessSalesforceEventCommandHandler with all dependencies"""
        event_store = infrastructure_factory.event_store
        read_model = infrastructure_factory.read_model
        event_publisher = infrastructure_factory.event_publisher
        
        # Create backfill service (Salesforce client would be injected in real app)
        backfill_service = BackfillService(None, event_store)
        
        return ProcessSalesforceEventCommandHandler(
            event_store=event_store,
            read_model=read_model,
            event_publisher=event_publisher,
            backfill_service=backfill_service
        )
    
    @staticmethod
    def get_read_model(
        infrastructure_factory: Annotated[InfrastructureFactory, Depends(get_infrastructure_factory)]
    ):
        """Get read model from infrastructure factory"""
        return infrastructure_factory.read_model 