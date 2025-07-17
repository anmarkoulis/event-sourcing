---
marp: true
theme: beam
class: invert
paginate: true
header: "PyCon Athens 2025"
footer: "Event Sourcing & CQRS with FastAPI and Celery"
style: |
  section {
    font-size: 1.5em;
    background-color: #1E1E1E;
    color: #E0E0E0;
  }
  h1 {
    font-size: 1.8em;
    color: #FFD43B;
    border-bottom: 2px solid #306998;
  }
  h2 {
    color: #306998;
  }
  code {
    font-size: 0.9em;
    background-color: #2D2D2D;
    color: #E0E0E0;
  }
  pre {
    background-color: #2D2D2D;
  }
  strong {
    color: #FFD43B;
  }
  a {
    color: #306998;
  }
  blockquote {
    border-left-color: #306998;
    color: #A0A0A0;
  }
  ul li::marker {
    color: #FFD43B;
  }
  ol li::marker {
    color: #FFD43B;
  }
  section.lead h1 {
    font-size: 2.5em;
  }
  section.lead h2 {
    font-size: 1.8em;
  }
  section.lead {
    text-align: center;
  }
---

# How I Learned to Stop Worrying and Love Raw Events

## Event Sourcing & CQRS with FastAPI and Celery

**PyCon Athens 2025**

---

# What We'll Discuss

## Core Principles
- **Event Sourcing**: Store every change as an immutable event
- **CQRS**: Separate read and write concerns

## Python Ecosystem Examples
- **FastAPI**: API surface for commands and queries
- **Celery**: Async event processing
- **Pydantic**: Data validation and modeling

## The Aftermath
- **Real-world patterns** and gotchas
- **Performance considerations**
- **Debugging and testing** in an immutable world

---

# Who Am I?

- **Staff Engineer** with 10+ years in Python
- Studied **Physics** → **Computational Physics** → **Software Engineering**
  - *"I went from calculating planet trajectories to debugging production systems. Turns out, both involve a lot of uncertainty!"*
- **Passionate about building systems** with quality

---

# Traditional Approach

## We store the current state:

```python
class UserService:
    def update_user(self, user_id: int, data: dict):
        user = self.db.get_user(user_id)
        user.name = data['name']      # Mutate state
        user.email = data['email']
        self.db.save(user)            # Overwrite history
```

## Problems:
- **History is lost** - we only see current state
- **No audit trail** - who changed what when?
- **Mutable state** - data corruption risks
- **Tight coupling** - read/write in same model

---

# Event Sourcing Approach

## We store what happened:

```python
class UserCreated:
    event_id: UUID
    aggregate_id: UUID
    timestamp: datetime
    event_type: str = "USER_CREATED"
    data: dict  # What actually happened
```

## Benefits:
- **Complete history** - every change is recorded
- **Audit trail** - see exactly what happened
- **Immutable events** - data integrity
- **Time travel** - replay any point in history

---

# Pain Points of Traditional Architectures

## What we're used to:

- **Tight coupling** between read and write
- **Poor auditability** - who changed what when?
- **Mutable state** - data corruption risks
- **Scaling challenges** - read/write conflicts

## The result: systems that can't explain themselves

---

# Why Event Sourcing?

## The superpowers you get:

- **Complete audit trail** - every action is recorded
- **Time travel** - replay any point in history
- **Debugging superpowers** - see exactly what happened
- **Data integrity** - no more "lost" changes
- **Scalability** - separate read and write concerns

---

# Quick Teaser: Audited-by-Design System

## What does it look like?

```
Every action becomes an event:
UserCreated → UserNameChanged → UserEmailChanged → UserStatusChanged
```

## Benefits:
- **Complete history** - nothing is ever lost
- **Temporal queries** - "what was the user state at 3pm?"
- **Event replay** - rebuild state from scratch
- **Audit by design** - every change is recorded

---

# 2. Core Concepts

- Events: The building blocks with their payload structure
- Aggregates: Domain logic that applies events
- Event Store: The append-only source of truth
- Projections: Building read models from events
- Event Bus: Communication layer between components
- CQRS: Commands vs Queries, separate databases

---

# Events: The Building Blocks

## Event structure in our system:

```python
class Event:
    event_id: UUID                    # Unique identifier
    aggregate_id: UUID                # Which aggregate this belongs to
    event_type: str                   # What happened (UserCreated, UserUpdated, etc.)
    timestamp: datetime               # When it happened
    version: int                      # Event version
    data: Dict[str, Any]              # The actual change data
```

## Key principle: **Events are immutable facts**

---

# Aggregates: Domain Models

## How we model business logic:

```python
class UserAggregate:
    def apply(self, event: Event) -> None:
        """Apply a domain event to build state"""
        # Update aggregate state based on event type
        pass

    def create_user(self, name: str, email: str) -> Event:
        """Domain method with validation"""
        # Validate business rules
        # Return new event
        pass
```

## **State = Result of applying all events**

---

# Event Store: The Source of Truth

## Interface examples:

```python
class EventStore:
    async def save_event(self, event: Event):
        """Store event - never update or delete"""
        # Implementation: PostgreSQL, EventStoreDB, DynamoDB, etc.
        pass

    async def get_events_by_aggregate(self, aggregate_id: UUID):
        """Get all events for an aggregate"""
        # Implementation: PostgreSQL, EventStoreDB, DynamoDB, etc.
        pass

    async def get_events_by_type(self, event_type: str):
        """Get all events of a specific type"""
        # Implementation: PostgreSQL, EventStoreDB, DynamoDB, etc.
        pass
```

## **Append-only, immutable, replayable**

---

# Projections: Building Read Models

## How we build optimized views:

```python
class UserProjection:
    async def handle_user_created(self, event: Event) -> None:
        """Transform event into read model"""
        user_data = {
            "aggregate_id": event.aggregate_id,
            "name": event.data.get("name"),
            "email": event.data.get("email"),
            "created_at": event.timestamp,
        }

        # Save to read-optimized database
        await self.read_model.save_user(user_data)
```

## **Triggered from event store, optimized for queries**

---

# Event Bus: Communication Layer

## How we publish events to other systems:

```python
class EventBus:
    async def publish(self, event: Event) -> None:
        """Publish event to subscribers"""
        # Implementation: RabbitMQ, Kafka, EventBridge, SNS, etc.
        pass

    async def subscribe(self, event_type: str, handler) -> None:
        """Subscribe to specific event types"""
        # Implementation: RabbitMQ, Kafka, EventBridge, SNS, etc.
        pass
```

## **Decoupled communication between components**

---

# CQRS: Command Query Responsibility Segregation

## Separate concerns with different databases:

**Commands** (Write Model):
- **Command Handlers** - Process commands, call aggregates
- **Aggregates** - Apply business logic, create events
- **Event Store** - Persist events (source of truth)
- **Event Bus** - Publish events to subscribers

**Queries** (Read Model):
- **Query Handlers** - Process queries, return data
- **Read Models** - Optimized for fast reads
- **Denormalized data** - Performance over consistency
- **Separate database** - No business logic

## **Different databases for different purposes**

---

# CQRS Benefits

## What you get:

- **Auditability** - commands emit events, queries are optimized
- **Modularity** - different models for different concerns
- **Scalability** - read/write workloads differ
- **Technology flexibility** - different DBs for different needs

## Key point: **You don't need Kafka to start with CQRS**

Start simple, evolve as needed!

---

# 3. Architecture Walkthrough

- High-level flow: External event → queue → processing → publish → read model
- Tools & layers: Celery, FastAPI, Event Bus
- Key components: Event ingestion, event store, replay, read DB
- Design flexibility: Services + repositories, async + decoupling

---

# High-Level Architecture Flow

## How the entities work together:

```
External Request → Command → Aggregate → Event → Event Store
                                        ↓
Read Model ← Event Bus ← Projections ← Event
```

## Core flow:
1. **Command** - Intent to change system state
2. **Aggregate** - Applies business logic, creates events
3. **Event Store** - Persists events (source of truth)
4. **Event Bus** - Publishes events to subscribers
5. **Projections** - Build read models from events
6. **Read Model** - Optimized for fast queries

---

# Python Ecosystem Solutions

## How we implement this in Python:

```
External Request → FastAPI → Command Handler → Aggregate → Event → Event Store
                                                                    ↓
Read Model ← Event Bus ← Celery Workers ← Projections ← Event
```

## Python tools:
- **FastAPI**: API surface for commands/queries
- **Celery**: Async task runner, scalable workers
- **Event Store**: PostgreSQL, EventStoreDB, DynamoDB
- **Event Bus**: RabbitMQ, Kafka, EventBridge, SNS

---

# FastAPI: The Command Interface

## Real implementation with Pydantic:

```python
@router.post("/users")
async def create_user(
    user_data: dict,
    infrastructure_factory: InfrastructureFactoryDep = None
):
    # Create command with validation
    command = CreateUserCommand(
        name=user_data["name"],
        email=user_data["email"]
    )

    # Get handler and process
    handler = infrastructure_factory.create_create_user_command_handler()
    await handler.handle(command)

    # Return immediately (async processing)
    return {"status": "accepted", "user_id": command.user_id}
```

---

# Command Handlers: Business Logic

## How we structure command processing:

```python
class CreateUserCommandHandler:
    def __init__(self, event_store: EventStore, event_bus: EventBus):
        self.event_store = event_store
        self.event_bus = event_bus

    async def handle(self, command: CreateUserCommand) -> None:
        # Create aggregate
        user = UserAggregate(uuid.uuid4())

        # Call domain method (validates and creates event)
        event = user.create_user(command.name, command.email)

        # Apply event to aggregate
        user.apply(event)

        # Command Handler: Store in event store
        await self.event_store.save_event(event)

        # Command Handler: Publish to event bus
        await self.event_bus.publish(event)
```

## **Command Handler orchestrates: Event Store + Event Bus**

---

# Celery: Async Task Runner & Scalable Workers

## Event processing tasks:

```python
@app.task(name="process_user_event")
def process_user_event_task(event_data: Dict[str, Any]) -> None:
    """Process user event via Celery task."""

    # Convert async function to sync for Celery
    process_user_event_async_sync = async_to_sync(process_user_event_async)

    # Execute the async function
    process_user_event_async_sync(event_data=event_data)

async def process_user_event_async(event_data: Dict[str, Any]) -> None:
    # Business logic
    event = Event(**event_data)
    handler = infrastructure_factory.create_user_event_handler()
    await handler.handle(event)
```

---

# Projections: Event-Driven Read Models

## How projections build read models:

```python
class UserProjection:
    async def handle_user_created(self, event: Event) -> None:
        # Build read model from event
        user_data = {
            "aggregate_id": event.aggregate_id,
            "name": event.data.get("name"),
            "email": event.data.get("email"),
            "status": event.data.get("status"),
            "created_at": event.timestamp,
        }

        # Save to read model
        await self.read_model.save_user(user_data)

        # Broadcast to EventBridge
        await self._publish_user_event("UserCreated", user_data, event)
```

---

# FastAPI: Query Interface

## How we expose read models:

```python
@users_router.get("/{user_id}")
async def get_user(
    user_id: str,
    infrastructure_factory: InfrastructureFactoryDep = None
) -> Dict[str, Any]:
    # Create query handler
    query_handler = infrastructure_factory.create_get_user_query_handler()

    # Create query object
    query = GetUserQuery(user_id=user_id)

    # Execute query
    user = await query_handler.handle(query)

    return {"status": "success", "user": user.dict()}

@users_router.get("/{user_id}/history")
async def get_user_history(user_id: str, from_date: Optional[str] = None):
    # Get event history from event store
    query_handler = infrastructure_factory.create_get_user_history_query_handler()
    query = GetUserHistoryQuery(user_id=user_id, from_date=from_date)
    events = await query_handler.handle(query)

    return {"status": "success", "events": [event.dict() for event in events]}
```

---

# Design Flexibility: Services + Repositories

## Clean separation of concerns:

```python
# Command side service
class UserCommandService:
    def __init__(self, event_store: EventStore, event_bus: EventBus):
        self.event_store = event_store
        self.event_bus = event_bus

    async def create_user(self, command: CreateUserCommand):
        # Business logic
        event = UserCreated(
            user_id=command.user_id,
            name=command.name,
            email=command.email
        )

        # Store and publish
        await self.event_store.append(event)
        await self.event_bus.publish(event)

# Query side service
class UserQueryService:
    def __init__(self, read_model: UserReadModel):
        self.read_model = read_model

    async def get_user(self, user_id: str) -> User:
        return await self.read_model.get_user(user_id)
```

---

# Async + Decoupling for Scale

## Benefits of this architecture:

- **High availability** - commands return immediately
- **Independent scaling** - read/write workloads differ
- **Resilience** - failures don't cascade
- **Technology flexibility** - different DBs for different needs
- **Eventual consistency** - a feature, not a bug

## Real performance:
Systems process external events with proper choreography and maintain complete audit trails.

---

# 4. Real-World Patterns & Gotchas (6-7 min)

- Eventual consistency: why it's a feature, not a bug
- Snapshots for performance on replay
- Initial backfill: bootstrapping from source APIs
- Fixes by reprocessing history — no manual data patching
- Debugging & testing in an immutable world

---

# Eventual Consistency: Feature, Not Bug

## Why it's powerful:

```
User creates account → Event stored → API returns success
                    ↓
              Event processing (async)
                    ↓
              Read model updated (eventually)
```

## Benefits:
- **High availability** - API responds immediately
- **Scalability** - processing can be distributed
- **Fault tolerance** - retry on failure
- **Performance** - no blocking operations

---

# Snapshots for Performance

## The replay problem:

```python
# Without snapshots - slow for long histories
def get_user_state(user_id: str, at_time: datetime):
    events = event_store.get_events(user_id, until=at_time)
    return replay_events(events)  # Could be thousands of events
```

## With snapshots:

```python
# With snapshots - fast state reconstruction
def get_user_state(user_id: str, at_time: datetime):
    snapshot = get_latest_snapshot(user_id, before=at_time)
    events = event_store.get_events(user_id, from_version=snapshot.version, until=at_time)
    return replay_events_from_snapshot(snapshot, events)  # Much faster
```

---



---

# Fixes by Reprocessing History

## No manual data patching:

```python
# Instead of: UPDATE users SET name = 'John' WHERE id = '123'

# We do: Reprocess all events with the fix
@celery_app.task
def reprocess_user_events(user_id: str):
    events = event_store.get_stream(user_id)

    # Clear read model
    read_model.delete_user(user_id)

    # Replay with fix
    for event in events:
        if event.type == "UserCreated":
            process_user_created.delay(event.dict())
        elif event.type == "UserNameChanged":
            process_user_name_changed.delay(event.dict())
```

---

# Debugging in an Immutable World

## What debugging looks like:

```python
# See exactly what happened
def debug_user_issue(user_id: str, timestamp: datetime):
    events = event_store.get_events(user_id, around=timestamp)

    print(f"User {user_id} events around {timestamp}:")
    for event in events:
        print(f"  {event.timestamp}: {event.type} - {event.data}")

    # Replay to see state
    state = replay_events(events)
    print(f"Final state: {state}")
```

## Benefits:
- **Complete visibility** - every change is recorded
- **Time travel** - see state at any point
- **No lost data** - nothing is ever overwritten

---

# Testing in an Immutable World

## Testing strategies:

```python
# Test aggregates by applying events
def test_user_aggregate():
    user = UserAggregate()

    # Apply events
    user.apply(UserCreated(user_id="123", name="John", email="john@example.com"))
    user.apply(UserNameChanged(user_id="123", old_name="John", new_name="Johnny"))

    # Assert final state
    assert user.name == "Johnny"
    assert user.email == "john@example.com"

# Test event store
def test_event_store():
    event = UserCreated(user_id="123", name="John", email="john@example.com")

    # Store and retrieve
    event_store.append(event)
    events = event_store.get_stream("123")

    assert len(events) == 1
    assert events[0].type == "UserCreated"
```

## Benefits:
- **Predictable testing** - immutability makes tests reliable
- **Event-based testing** - test business logic through events
- **Integration testing** - test full event processing pipeline

---

# Thank You!

## How I Learned to Stop Worrying and Love Raw Events

**Event Sourcing & CQRS with FastAPI and Celery**

**PyCon Athens 2025**

Questions? Let's discuss!
