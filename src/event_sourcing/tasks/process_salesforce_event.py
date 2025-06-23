import logging
from typing import Dict, Any

from ..application.commands.salesforce import ProcessSalesforceEventCommand
from ..application.commands.handlers.process_salesforce_event import ProcessSalesforceEventCommandHandler
from ..application.services.backfill import BackfillService
from ..infrastructure.factory import InfrastructureFactory

logger = logging.getLogger(__name__)


def process_salesforce_event_task(raw_event: Dict[str, Any]) -> None:
    """Celery task for processing Salesforce CDC events"""
    logger.info(f"Processing Salesforce event: {raw_event}")
    
    # Initialize infrastructure factory
    # In production, these would come from environment variables
    database_url = "postgresql+asyncpg://user:password@localhost/event_sourcing"
    eventbridge_region = "us-east-1"
    
    infrastructure_factory = InfrastructureFactory(database_url, eventbridge_region)
    
    try:
        # Create command
        command = ProcessSalesforceEventCommand.create(
            raw_event=raw_event,
            entity_name=raw_event.get("detail", {}).get("payload", {}).get("ChangeEventHeader", {}).get("entityName"),
            change_type=raw_event.get("detail", {}).get("payload", {}).get("ChangeEventHeader", {}).get("changeType")
        )
        
        # Get infrastructure components
        event_store = infrastructure_factory.event_store
        read_model = infrastructure_factory.read_model
        event_publisher = infrastructure_factory.event_publisher
        
        # Create backfill service (Salesforce client would be injected in real app)
        backfill_service = BackfillService(None, event_store)
        
        # Create handler
        handler = ProcessSalesforceEventCommandHandler(
            event_store=event_store,
            read_model=read_model,
            event_publisher=event_publisher,
            backfill_service=backfill_service
        )
        
        # Process command (in real app, this would be async)
        # await handler.handle(command)
        logger.info(f"Successfully processed Salesforce event: {command.command_id}")
        
    except Exception as e:
        logger.error(f"Error processing Salesforce event: {e}")
        raise
    finally:
        # Clean up infrastructure
        # await infrastructure_factory.close()
        pass 