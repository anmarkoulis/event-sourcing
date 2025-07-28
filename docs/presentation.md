---
marp: true
theme: beam
class: invert
paginate: true
header: "PyCon Athens 2025"
footer: "Event Sourcing & CQRS with FastAPI and Celery"
style: |
  section {
    font-size: 1.3em;
    background-color: #1E1E1E;
    color: #E0E0E0;
    line-height: 1.4;
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
    font-size: 0.8em;
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
  /* Target the specific event-sourcing-flow image */
  img[src*="event-sourcing-flow"] {
    transform: scale(1.4) !important;
    transform-origin: center !important;
    margin: 2em 0 !important;
    margin-left: 9em !important;
  }
---

# How I Learned to Stop Worrying and Love Raw Events

## Event Sourcing & CQRS with FastAPI and Celery

**PyCon Athens 2025**

---

# My Journey: From Celestial Chaos to System Chaos

- **Senior Staff Engineer** @ Orfium
- **10+ years** Python experience
- **Background**: Physics → Computational Physics → Software Engineering
- **Now**: Debugging real-world system chaos
- **Philosophy**: Right architecture for each problem

<!--
Hello everybody! I'm super excited to be presenting at PyCon Athens. This is the first one, both for PyCon in Greece but also for me so it's extra important. That's why I'd like to thank the committee for having me here - it's truly an honor to be part of this inaugural event.

I'm Antonis Markoulis, Senior Staff Engineer at Orfium. I've been coding in Python for over 10 years and I absolutely love it. I initially started working professionally with C++, but with Python I loved the way that I didn't have to deal with the low-level stuff and could actually focus on solving the problem rather than following a dangling pointer.

My journey started in Physics, specifically computational physics and simulation software. I have worked a lot with celestial dynamics simulating chaotic trajectories. Turns out, production systems are way more chaotic than comets.

I'm passionate about keeping things simple and using the right architecture for each problem. There's no one-size-fits-all solution - unless you count unicorns, but those don't exist in real architecture, do they? The same applies with event sourcing, it is not for everybody but hopefully after today's presentation it will be added as an option.

When it comes to the title of the presentation, last year I discovered Stanley Kubrick's 'Dr. Strangelove: Or How I Learned to Stop Worrying and Love the Bomb' for the first time - yes, I know, I'm late to the party! But I can see the analogies. The bomb are the complex systems and I am worrying too much about production issues on them. Hopefully after the end of the presentation you will also stop worrying about debugging production systems.
-->

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

# The Nightmare: "Who Deleted My User?"

## A real debugging story:

```python
def delete_user(user_id: int):
    db.delete_user(user_id)
```

## The problem:
**Monday 3:47 PM**: "Sarah's account is missing!"
**Tuesday 9:15 AM**: "When was it deleted? Who did it? Why?"

## What we can't answer:
- ❌ **When** was the user deleted?
- ❌ **Who** deleted the user?
- ❌ **Why** was it deleted?

## **The system has no memory of what happened**

---

# Enter Event Sourcing: The System That Remembers

## We store every change as an immutable event:

```python
UserDeleted(
    event_id=uuid4(),
    aggregate_id="user_123",
    revision=5,
    version=1,
    timestamp=datetime.now(),
    event_type="USER_DELETED",
    data={ "deleted_by": "admin_456", "reason": "Account closure request" }
)
```

## Now we can answer everything:
- ✅ **When**: March 15, 3:47 PM
- ✅ **Who**: Admin ID 456
- ✅ **Why**: Account closure request

## **Every action becomes a permanent record**

---



# Core Concepts: Events

## Immutable Facts

**Events are immutable facts** that represent state changes in the system.

## Example:
**User Created Event** - John Doe, john@example.com, March 15

## Key characteristics:
- **Immutable**: Once created, events never change
- **Facts**: They represent what actually happened
- **Complete**: Each event contains all necessary data
- **Revisioned**: Events have sequence numbers for ordering
- **Versioned**: Events have schema versions for serialization

## Key principle: **Events are immutable facts** - they never change

---

# Core Concepts: Event Streams

## Ordered Sequences

**Event streams are ordered sequences** of events for a specific aggregate.

## Example:
![Event Stream Sequence](../diagrams/generated/event-stream-sequence.png)

## Key characteristics:
- **Ordered**: Events have strict chronological ordering
- **Complete**: Contains the full history of an aggregate
- **Replayable**: Can rebuild any point in time
- **Source of truth**: The definitive record of what happened

## **The stream is the source of truth** - rebuild any point in time

---

# Core Concepts: Commands

## Intent to Change

**Commands represent the intent** to change the system state.

## Example:
**"Create a new user account"**

## Key characteristics:
- **Intent**: They express what we want to happen
- **Validation**: Can be validated before execution
- **Idempotent**: Safe to retry if needed
- **Entry point**: The starting point for all changes

## **Commands are the entry point** - they represent what we want to do

---

# Core Concepts: Queries

## Intent to Read (CQRS Separation)

**Queries represent the intent** to read data from the system.

## Example:
**"Show me user John Doe's profile"**

## Key characteristics:
- **Read-only**: They never change system state
- **Optimized**: Designed for specific read patterns
- **Separate models**: Different from command models (CQRS)
- **Fast**: Optimized for quick data retrieval

## **Queries are separate from commands** - different models for different purposes

---

# Core Concepts: Aggregates

## Domain Logic

**Aggregates contain domain logic** and apply business rules to create events.

## Example:
- User email must be unique
- Cannot delete already deleted user

## Key characteristics:
- **Business rules**: Enforce domain-specific validation
- **State management**: Maintain current state from events
- **Event creation**: Generate new events based on commands
- **Consistency**: Ensure business invariants are maintained

## **Aggregates apply business logic** and create events

---

# Core Concepts: Event Store

## Source of Truth

**Event Store is the append-only storage** for all events in the system.

## Example:
**User John Doe's Event Stream**
- **Event 1**: User Created (March 15, 2:30 PM)
- **Event 2**: Email Changed (March 16, 10:15 AM)

## Key characteristics:
- **Append-only**: Events are never modified or deleted
- **Immutable**: Once written, events are permanent
- **Stream management**: Organizes events by aggregate
- **Optimistic concurrency**: Prevents conflicting writes

## **Event Store is append-only** - events never change or delete

---

# Core Concepts: Projections

## Building Read Models

**Projections build optimized read models** from events for fast querying.

## Example:
- Event: User Created → Action: Create user record
- Event: Email Changed → Action: Update email field

## Key characteristics:
- **Event-driven**: Triggered by new events
- **Read-optimized**: Designed for specific query patterns
- **Denormalized**: Optimized for performance, not normalization
- **Eventually consistent**: Updated asynchronously

## **Projections handle business logic and update read models from events**

---

# How Everything Works Together

## The complete flow:

![Event Sourcing Flow](../diagrams/generated/event-sourcing-flow.png)

## **Each interaction follows this pattern** - from command to projection

---







# FastAPI: The Command Interface

## Real implementation with Pydantic:

```python
@router.post("/users")
async def create_user(
    user_data: dict,
    handler: CreateUserCommandHandler = Depends(InfraFactory.create_user_command_handler)
):
    # Create command with validation
    command = CreateUserCommand(
        name=user_data["name"],
        email=user_data["email"]
    )

    # Process command
    await handler.handle(command)

    # Return immediately (event stored successfully) or catch exceptions via middleware
    return {"user_id": command.user_id}
```

## **FastAPI commands accept requests and return immediately after event storage**

---

# Command Handlers: Business Logic

## How we structure command processing:

```python
class CreateUserCommandHandler:
    async def handle(self, command: CreateUserCommand) -> None:
        # Retrieve all events for this aggregate
        events = await self.event_store.get_stream(command.user_id)

        # Create empty aggregate and replay events
        user = UserAggregate(command.user_id)
        for event in events:
            user.apply(event)

        # Call domain method and get new events
        new_events = user.create_user(command.name, command.email)

        # Persist and dispatch events using unit of work
        async with self.uow:
            await self.event_store.append_to_stream(command.user_id, new_events)
            await self.event_handler.dispatch(new_events)
```

## **Command Handler orchestrates: Event Store + Event Handler with Unit of Work**

---

# Event Handler: Celery Integration

## How events are dispatched to Celery tasks:

```python
class CeleryEventHandler:
    def __init__(self):
        # Map event types to Celery tasks
        self.event_handlers = {
            "USER_CREATED": [
                "process_user_created_task",
                "send_welcome_email_task"
            ],
            # ... other event types
        }

    async def dispatch(self, events: List[Event]) -> None:
        for event in events:
            if event.event_type in self.event_handlers:
                for task_name in self.event_handlers[event.event_type]:
                    # All tasks receive the same event payload structure
                    celery_app.send_task(task_name, kwargs={"event": event.model_dump()})
```

## **Event Handler dispatches to message queues, Celery tasks handle messages and call projections**

---

# Celery Tasks: Event Processing

## How Celery tasks process events and call projections:

```python
@app.task(name="process_user_created_task")
def process_user_created_task(event: Dict[str, Any]) -> None:
    # Convert async function to sync for Celery
    process_user_created_async_sync = async_to_sync(process_user_created_async)

    # Execute the async projection
    process_user_created_async_sync(event=event)

async def process_user_created_async(event: EventDTO) -> None:
    # Get projection and call it
    projection = UserProjection(read_model, event_publisher)
    await projection.handle_user_created(event)
```

## **Celery tasks are wrappers that call the appropriate projection handlers**

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
```

## **Projections build optimized read models from events for fast querying**


---

# FastAPI: Query Interface

## How we expose read models:

```python
@users_router.get("/{user_id}/")
async def get_user(
    user_id: str,
    query_handler: GetUserQueryHandler = Depends(InfraFactory.create_get_user_query_handler)
) -> Dict[str, Any]:
    return {"user": (await query_handler.handle(GetUserQuery(user_id=user_id))).dict()}

@users_router.get("/{user_id}/{timestamp}/")
async def get_user_at_timestamp(
    user_id: str,
    timestamp: datetime = Query(..., description="ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ"),
    query_handler: GetUserAtTimestampQueryHandler = Depends(InfraFactory.create_get_user_at_timestamp_query_handler)
):
    return {"user": (await query_handler.handle(GetUserAtTimestampQuery(user_id=user_id, timestamp=timestamp))).dict()}
```

## **FastAPI queries expose read models with dependency injection**

---

# The Aftermath: Real-World Patterns & Gotchas

## What happens when you actually build this?

- **Eventual consistency**: How to handle the delay between write and read
- **Error handling & retries**: Different strategies for commands vs projections
- **Performance with snapshots**: When replaying becomes slow
- **Debugging superpowers**: What debugging looks like in an immutable world

## **Let's talk about the real challenges**

---

# Eventual Consistency: The Real Challenge

## The story: "Update user's first name"

```python
# User updates first name
POST /users/123/ {"first_name": "John"}
# API returns success immediately
# But read model might not be updated yet
```

## Two approaches to handle this:

### 1. Optimistic Updates (Naive)
- Frontend updates UI immediately
- Refresh might show old data
- Depends on read model update time

### 2. Outbox Pattern (Advanced)
- Store events in outbox table with job status
- Track processing status (pending, processing, completed, failed)
- Create views of unprocessed events
- Clear visibility into what's been processed vs pending

## **Eventual consistency requires thoughtful UI design**

---

# Performance with Snapshots

## The performance challenge:

```python
    async def handle(self, command: CreateUserCommand) -> None:
        events = await self.event_store.get_stream(command.user_id)  # 10,000 events!
        user = UserAggregate(command.user_id)
        for event in events:
            user.apply(event)  # Takes 5 seconds 😱
        # ... rest of command handler logic
```

## The solution: Snapshots in Command Handler

```python
    async def handle(self, command: CreateUserCommand) -> None:
        try:
            snapshot = await self.snapshot_store.get_latest_snapshot(command.user_id)
            recent_events = await self.event_store.get_events_since_snapshot(command.user_id, snapshot.revision)
            # Rebuild aggregate from snapshot
            user = UserAggregate.from_snapshot(snapshot)
            for event in recent_events:
                user.apply(event)
        except SnapshotNotFound:
            # Fallback to previous code
```

## **Snapshots require aggregate changes** - rebuild state efficiently

---

# Error Handling & Retries: Two Different Worlds

## Commands (Synchronous) - API Failures:

```python
# Unit of Work ensures atomicity
async with self.uow:
    await self.event_store.append_to_stream(user_id, new_events)
    await self.event_handler.dispatch(new_events)
# Either succeeds or fails - API gets 500
```

## Projections (Asynchronous) - Celery Retries:

```python
# Celery handles retries with late acknowledgment
@app.task(bind=True, max_retries=3)
def process_user_created_task(self, event: Dict[str, Any]) -> None:
    try:
        # Process event
        projection.handle_user_created(event)
    except Exception as exc:
        # Celery retries automatically
        raise self.retry(countdown=60, exc=exc)

# Idempotence is critical - same message can arrive multiple times
```

## **Different strategies for different failure modes**

---

# Debugging Superpowers: Testing Business Logic

## The story: "What was the user's state at 3:47 PM?"

![Debugging Superpowers](../diagrams/generated/debugging-superpowers.png)

```python
# Rebuild state at specific point in time
def debug_incident(user_id: str, incident_time: datetime):
    events = event_store.get_events_before(user_id, incident_time)
    user = UserAggregate(user_id)

    # Rebuild exact state at incident time
    for event in events:
        user.apply(event)

    # Apply the problematic event that caused the issue
    user.apply(UserSuspendedEvent(user_id, reason="fraud_detected"))
```

## **Test business logic with real production data**

---

# Real-World Trade-offs & Key Takeaways

## When NOT to use Event Sourcing:

- **Simple CRUD with basic audit needs** - traditional logging suffices
- **High-frequency trading systems** - immediate consistency required
- **Teams without distributed systems experience** - steep learning curve
- **Systems with simple, predictable business rules** - overkill

## What you gain vs what you lose:

| ✅ **Gain** | ❌ **Lose** |
|-------------|-------------|
| Complete audit trail | Simplicity |
| Time travel capabilities | Immediate consistency |
| Debugging superpowers | Storage overhead |
| Scalability | Learning curve |

## **Event sourcing + Python ecosystem solve even the most complex distributed systems challenges**

---

# Thank You!

## Q & A

**Let's Connect!**

**GitHub**: github.com/anmarkoulis
**LinkedIn**: linkedin.com/in/anmarkoulis
**Dev.to**: dev.to/markoulis
