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

<!-- _class: lead -->
# How I Learned to Stop Worrying and Love Raw Events

## Event Sourcing & CQRS with FastAPI and Celery

**PyCon Athens 2025**

---

<!-- _class: lead -->
# 1. Intro & Motivation (3-4 min)

- Who am I?
- What are raw events? And why would anyone love them?
- The pain points of traditional architectures
- Quick teaser: what does an "audited-by-design" system look like?

---

# Who Am I?

- **Staff Engineer** with 10+ years in Python
- Built systems handling **millions of events** daily
- **Event sourcing evangelist** (recovering from traditional architectures)
- Love for **immutable data** and **audit trails**

---

# What Are Raw Events?

## Instead of storing current state...

```python
# Traditional approach
class UserService:
    def update_user(self, user_id: int, data: dict):
        user = self.db.get_user(user_id)
        user.name = data['name']  # Mutate state
        user.email = data['email']
        self.db.save(user)  # Overwrite history
```

## We store **every change** as an immutable event

```python
# Event sourcing approach
class UserCreated:
    user_id: int
    name: str
    email: str
    timestamp: datetime

class UserNameChanged:
    user_id: int
    old_name: str
    new_name: str
    timestamp: datetime
    reason: str
```

---

# Why Would Anyone Love Raw Events?

## The superpowers you get:

- **Complete audit trail** - every action is recorded
- **Time travel** - replay any point in history
- **Debugging superpowers** - see exactly what happened
- **Data integrity** - no more "lost" changes
- **Scalability** - separate read and write concerns

---

# Pain Points of Traditional Architectures

## What we're used to:

- **Tight coupling** between read and write
- **Poor auditability** - who changed what when?
- **Mutable state** - data corruption risks
- **Scaling challenges** - read/write conflicts

## The result: systems that can't explain themselves

---

# Quick Teaser: Audited-by-Design System

## What does it look like?

```python
# Every action is an event
UserCreated(user_id=123, name="John", email="john@example.com")
UserNameChanged(user_id=123, old_name="John", new_name="Johnny")
UserEmailChanged(user_id=123, old_email="john@example.com", new_email="johnny@example.com")
```

## Benefits:
- **Complete history** - nothing is ever lost
- **Temporal queries** - "what was the state at 3pm?"
- **Event replay** - rebuild state from scratch
- **Audit by design** - every change is recorded

---

<!-- _class: lead -->
# 2. Core Concepts (5-6 min)

- Event Sourcing: Store every change as an immutable event
- System state = the result of replaying events
- CQRS: Separate write model (commands/events) from read model (queries)
- Benefits: auditability, modularity, scalability
- Misconception bust: You don't need Kafka to do this

---

# Event Sourcing: The Fundamental Idea

## The core equation:

> **System state = The result of replaying all events**

```python
# Instead of: current_state = database.get()
# We have: current_state = replay_all_events()
```

## Key principles:
- **Store every change** as an immutable event
- **Never update or delete** events
- **Replay events** to build current state
- **Events are the source of truth**

---

# Event Sourcing in Practice

```python
class UserAggregate:
    def __init__(self):
        self.id = None
        self.name = None
        self.email = None
        self.version = 0
    
    def apply(self, event: Event):
        if isinstance(event, UserCreated):
            self.id = event.user_id
            self.name = event.name
            self.email = event.email
        elif isinstance(event, UserNameChanged):
            self.name = event.new_name
        
        self.version += 1

def build_user_state(user_id: str) -> UserAggregate:
    events = event_store.get_stream(f"user-{user_id}")
    user = UserAggregate()
    
    for event in events:
        user.apply(event)
    
    return user
```

---

# CQRS: Command Query Responsibility Segregation

## Separation of concerns:

### Commands (Write Model)
```python
class CreateUserCommand:
    name: str
    email: str

class ChangeUserNameCommand:
    user_id: int
    new_name: str
    reason: str
```

### Queries (Read Model)
```python
class UserQuery:
    def get_user_by_id(self, user_id: int) -> UserDTO:
        # Optimized for reading
        return self.read_db.get_user(user_id)
```

---

# CQRS Benefits

## Why this separation matters:

- **Auditability** - commands emit events, queries are optimized
- **Modularity** - different models for different concerns
- **Scalability** - read/write workloads differ
- **Technology flexibility** - different DBs for different needs

## **You don't need Kafka to start!**

---

<!-- _class: lead -->
# 3. Architecture Walkthrough (10-12 min)

- High-level flow: External event → queue → processing → publish → read model
- Tools & layers: Celery, FastAPI, Internal Event Bus
- Key components: Raw event ingestion, Event store, Replaying events, Read DB
- Design flexibility: Services + repositories, Async + decoupling

---

# High-Level Architecture Flow

```
External Request → Command → Event Store → Event Bus → Read Model
```

## Key components:
- **FastAPI** - API surface (commands + queries)
- **Celery** - async event processing
- **Event Store** - append-only event log
- **Read Model** - optimized for queries
- **Event Bus** - pub/sub communication

---

# FastAPI: The Command Interface

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class CreateUserCommand(BaseModel):
    name: str
    email: str

@app.post("/users")
async def create_user(command: CreateUserCommand):
    # Validate command
    # Emit event
    # Return immediately (async)
    event = UserCreated(
        user_id=generate_id(),
        name=command.name,
        email=command.email
    )
    
    await event_store.append(event)
    await event_bus.publish(event)
    
    return {"user_id": event.user_id, "status": "processing"}
```

---

# Celery: Async Task Runner & Scalable Workers

```python
from celery import Celery

celery_app = Celery('event_processor')

@celery_app.task
def process_user_created(event: UserCreated):
    # Business logic here
    user = User(
        id=event.user_id,
        name=event.name,
        email=event.email,
        created_at=event.timestamp
    )
    
    # Update read model
    read_model.save_user(user)
    
    # Send welcome email
    email_service.send_welcome(event.email)

@celery_app.task
def process_user_name_changed(event: UserNameChanged):
    # Update read model
    read_model.update_user_name(event.user_id, event.new_name)
    
    # Notify other services
    notification_service.notify_name_change(event)
```

---

# Event Store: The Source of Truth

```python
class EventStore:
    def __init__(self, db: Database):
        self.db = db
    
    async def append(self, event: Event):
        # Append-only operation
        await self.db.execute("""
            INSERT INTO events (stream_id, event_type, data, version)
            VALUES ($1, $2, $3, $4)
        """, event.stream_id, event.__class__.__name__, 
             event.model_dump(), event.version)
    
    async def get_stream(self, stream_id: str, from_version: int = 0):
        # Get all events for a stream
        rows = await self.db.fetch("""
            SELECT * FROM events 
            WHERE stream_id = $1 AND version > $2
            ORDER BY version
        """, stream_id, from_version)
        
        return [deserialize_event(row) for row in rows]
```

---

# Read Model: Search-Optimized Database

```python
class UserReadModel:
    def __init__(self, db: Database):
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> UserDTO:
        # Fast, direct query
        row = await self.db.fetchrow("""
            SELECT id, name, email, created_at, updated_at
            FROM users WHERE id = $1
        """, user_id)
        
        return UserDTO(**row) if row else None
    
    async def search_users(self, name_pattern: str) -> List[UserDTO]:
        # Optimized search
        rows = await self.db.fetch("""
            SELECT id, name, email, created_at
            FROM users 
            WHERE name ILIKE $1
            ORDER BY created_at DESC
        """, f"%{name_pattern}%")
        
        return [UserDTO(**row) for row in rows]
```

---

# Design Flexibility: Services + Repositories

## Command side:
```python
class UserCommandService:
    def __init__(self, event_store: EventStore, event_bus: EventBus):
        self.event_store = event_store
        self.event_bus = event_bus
    
    async def create_user(self, command: CreateUserCommand):
        event = UserCreated(user_id=generate_id(), **command.dict())
        await self.event_store.append(event)
        await self.event_bus.publish(event)
        return event.user_id
```

## Query side:
```python
class UserQueryService:
    def __init__(self, read_model: UserReadModel):
        self.read_model = read_model
    
    async def get_user(self, user_id: int) -> UserDTO:
        return await self.read_model.get_user_by_id(user_id)
```

---

# Async + Decoupling for Scale

## Benefits of this architecture:

- **High availability** - commands return immediately
- **Independent scaling** - read/write workloads differ
- **Resilience** - failures don't cascade
- **Technology flexibility** - different DBs for different needs
- **Eventual consistency** - a feature, not a bug

---

<!-- _class: lead -->
# 4. Real-World Patterns & Gotchas (6-7 min)

- Eventual consistency: why it's a feature, not a bug
- Snapshots for performance on replay
- Initial backfill: bootstrapping from source APIs
- Fixes by reprocessing history — no manual data patching
- Debugging & testing in an immutable world

---

# Eventual Consistency: Feature, Not Bug

## Why eventual consistency is powerful:

```python
# Command side - immediate response
@app.post("/users/{user_id}/name")
async def change_name(user_id: int, new_name: str):
    event = UserNameChanged(user_id, new_name)
    await event_store.append(event)
    await event_bus.publish(event)
    
    return {"status": "processing"}  # Immediate response

# Query side - eventually consistent
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # May not reflect latest changes yet
    return await read_model.get_user_by_id(user_id)
```

## Benefits:
- **High availability** - system stays responsive
- **Scalability** - independent read/write scaling
- **Resilience** - failures don't cascade

---

# Snapshots for Performance on Replay

## The replay problem:

```python
# Without snapshots - slow for old aggregates
def build_user_state(user_id: str) -> UserAggregate:
    events = event_store.get_stream(f"user-{user_id}")  # Could be 1000s of events
    user = UserAggregate()
    
    for event in events:  # Expensive!
        user.apply(event)
    
    return user
```

## With snapshots:

```python
def build_user_state(user_id: str) -> UserAggregate:
    # Try to get latest snapshot
    snapshot = snapshot_store.get_latest(f"user-{user_id}")
    
    if snapshot:
        user = snapshot.state
        # Only replay events after snapshot
        events = event_store.get_stream(f"user-{user_id}", snapshot.version)
    else:
        user = UserAggregate()
        events = event_store.get_stream(f"user-{user_id}")
    
    for event in events:
        user.apply(event)
    
    return user
```

---

# Initial Backfill: Bootstrapping from Source APIs

## How to migrate existing data:

```python
@celery_app.task
def backfill_user_events():
    # Get users from existing system
    users = legacy_db.get_all_users()
    
    for user in users:
        # Create events for existing state
        event = UserCreated(
            user_id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at
        )
        
        # Store in event store
        event_store.append(event)
        event_bus.publish(event)
        
        # Update read model
        read_model.save_user(user)
```

---

# Fixes by Reprocessing History

## Instead of manual data patches:

```python
# Traditional approach - scary!
UPDATE users SET name = 'correct_name' WHERE id = 123;

# Event sourcing approach - safe!
@celery_app.task
def fix_user_name(user_id: int, correct_name: str):
    # Emit correction event
    event = UserNameCorrected(
        user_id=user_id,
        old_name=get_current_name(user_id),
        new_name=correct_name,
        reason="Data correction"
    )
    
    await event_store.append(event)
    await event_bus.publish(event)
    
    # All projections will be updated automatically
```

---

# Debugging in an Immutable World

## The debugging superpowers:

```python
# See exactly what happened
async def debug_user_issue(user_id: int, timestamp: datetime):
    # Get all events for the user
    events = await event_store.get_stream(f"user-{user_id}")
    
    # Replay to any point in time
    user_state = UserAggregate()
    for event in events:
        if event.timestamp <= timestamp:
            user_state.apply(event)
        else:
            break
    
    return user_state

# Compare states at different times
state_3pm = await debug_user_issue(user_id, datetime(2025, 1, 1, 15, 0))
state_4pm = await debug_user_issue(user_id, datetime(2025, 1, 1, 16, 0))
```

---

# Testing in an Immutable World

## Testing strategies:

```python
class TestUserAggregate:
    def test_user_creation(self):
        # Given
        events = [
            UserCreated(user_id=1, name="John", email="john@example.com")
        ]
        
        # When
        user = UserAggregate()
        for event in events:
            user.apply(event)
        
        # Then
        assert user.name == "John"
        assert user.email == "john@example.com"

class TestEventStore:
    async def test_event_append_and_retrieve(self):
        # Given
        event = UserCreated(user_id=1, name="John", email="john@example.com")
        
        # When
        await event_store.append(event)
        retrieved_events = await event_store.get_stream("user-1")
        
        # Then
        assert len(retrieved_events) == 1
        assert retrieved_events[0].name == "John"
```

---

<!-- _class: lead -->
# 5. Key Takeaways & Reflections (2-3 min)

- Raw events are scary — until you realize how powerful they are
- Python + Celery + FastAPI are more than capable for serious architecture
- Event sourcing is a mindset shift, not a silver bullet — but it's fun
- The system you build today should be able to explain itself 6 months from now

---

# Key Takeaways

## What you should remember:

1. **Raw events are powerful** - complete audit trail, time travel, debugging superpowers
2. **Python ecosystem is ready** - FastAPI + Celery + async/await = perfect combination
3. **Start simple** - you don't need Kafka or complex infrastructure to begin
4. **Event sourcing is a mindset** - think in terms of "what happened" not "what is"
5. **Your system should explain itself** - 6 months from now, you'll thank yourself

---

# Questions to Challenge Your Architecture

## Before your next project, ask:

- **What if I stored every change instead of just current state?**
- **How would I debug this if I could replay every action?**
- **What would it mean to have complete audit trails?**
- **Could I separate my read and write concerns?**
- **What if my data was immutable?**

---

<!-- _class: lead -->
# Thank You!

## Questions & Discussion

**Slides & Code**: [GitHub Link]

**Twitter**: @yourhandle

**Email**: your.email@example.com

---

<!-- _class: lead -->
# Resources

## Further Reading:

- **Event Sourcing** by Martin Fowler
- **CQRS** by Greg Young
- **Domain-Driven Design** by Eric Evans
- **Building Event-Driven Microservices** by Adam Bellemare

## Tools & Libraries:

- **FastAPI** - Modern Python web framework
- **Celery** - Distributed task queue
- **Pydantic** - Data validation
- **SQLAlchemy** - Database ORM
- **Redis** - Event store & caching