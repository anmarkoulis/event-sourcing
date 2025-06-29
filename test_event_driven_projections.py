#!/usr/bin/env python3
"""
Test script to verify event-driven projection flow.
"""

import asyncio
import logging

from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.domain.events.client import ClientCreatedEvent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_event_driven_projections() -> None:
    """Test the event-driven projection flow"""

    # Get infrastructure factory
    infrastructure_factory = get_infrastructure_factory()
    event_store = infrastructure_factory.event_store
    read_model = infrastructure_factory.read_model

    # Create a test event
    test_event = ClientCreatedEvent.create(
        aggregate_id="test-client-123",
        data={
            "Name": "Test Client",
            "ParentId": "parent-456",
            "Status__c": "Active",
        },
        metadata={"source": "test", "test_run": True},
    )

    logger.info(f"Created test event: {test_event.event_id}")

    # Save event (this should automatically trigger projections)
    await event_store.save_event(test_event)
    logger.info("Event saved to event store")

    # Wait a moment for async processing
    await asyncio.sleep(2)

    # Check if read model was updated
    client = await read_model.get_client("test-client-123")
    if client:
        logger.info(f"✅ Read model updated successfully: {client}")
    else:
        logger.error("❌ Read model was not updated")

    # Clean up
    await infrastructure_factory.close()


if __name__ == "__main__":
    asyncio.run(test_event_driven_projections())
