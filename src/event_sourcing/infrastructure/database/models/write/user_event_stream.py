from event_sourcing.infrastructure.database.models.write.event_stream import (
    EventStream,
)


class UserEventStream(EventStream):
    """Concrete implementation of EventStream for User aggregate events"""
