import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class EventPublisher(ABC):
    """Abstract event publisher interface"""

    @abstractmethod
    async def publish(self, event_data: Dict[str, Any]) -> None:
        """Publish event data"""


class EventBridgePublisher(EventPublisher):
    """EventBridge implementation of event publisher"""

    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name

    async def publish(self, event_data: Dict[str, Any]) -> None:
        """Publish normalized entity to EventBridge"""
        try:
            # In a real implementation, this would use boto3
            # eventbridge_client = boto3.client('events', region_name=self.region_name)
            # response = await eventbridge_client.put_events(
            #     Entries=[{
            #         'Source': 'event-sourcing-system',
            #         'DetailType': f'{event_data.get("entity_name")}Changed',
            #         'Detail': json.dumps(event_data),
            #         'EventBusName': 'default'
            #     }]
            # )

            logger.info(
                f"Published event to EventBridge: {event_data.get('aggregate_id')}"
            )
        except Exception as e:
            logger.error(f"Failed to publish event to EventBridge: {e}")
            raise EventPublishException(f"Failed to publish event: {e}")


class EventPublishException(Exception):
    """Raised when event publishing fails"""
