# Architecture Options for Event Sourcing & CQRS System

## System Context & Goals

### 🎯 Core Objectives
Our system is designed to handle Salesforce CDC (Change Data Capture) events with the following architectural principles:

1. **Raw Event Preservation**: CDC events are ingested and persisted as-is without normalization
2. **Deferred Processing**: Projection and normalization happen during read model updates, not at ingestion
3. **Event-Driven Design**: The system is built around events as first-class citizens
4. **Auditability**: Complete history is preserved and replayable
5. **Scalability**: Async processing with eventual consistency
6. **Flexibility**: Support for schema evolution and business rule changes

### 🏗️ Current Implementation
- **Architecture**: Explicit CQRS with Event Sourcing (Missing Aggregates)
- **Write Model**: Event store using DynamoDB
- **Read Model**: OpenSearch for optimized queries
- **Processing**: Celery tasks for async projection and broadcasting
- **Messaging**: EventBridge for event broadcasting
- **CQRS**: Explicit command and query service interfaces

### 🔄 Data Flow
1. Raw Salesforce CDC events ingested
2. Events stored in DynamoDB event store
3. Celery tasks trigger projection to OpenSearch
4. Normalization applied during projection
5. Events broadcast via EventBridge for downstream consumers
6. Queries served from optimized read model (OpenSearch)

---

## Architecture Options Analysis

### 🔸 Option 1: Layered Architecture (Classic)
**Current State** - What we started with

**Characteristics:**
- CQRS: ❌ (No explicit separation)
- Event Sourcing: ❌ (Traditional CRUD)
- Aggregates: ❌ (No domain modeling)

**How it works:**
- API → Service → DAO pattern
- All business logic in service layer
- Events normalized early in the process
- Traditional database operations

**Pros:**
- Familiar and well-understood
- Easy to implement initially
- Good for simple CRUD operations

**Cons:**
- Tight coupling between layers
- Poor auditability
- Difficult to evolve business rules
- No support for event replay

**When to use:** Simple applications with stable business rules

---

### 🔸 Option 2: Explicit CQRS (Commands/Queries Separation)
**Evolution Step** - Better separation of concerns

**Characteristics:**
- CQRS: ✅ (Explicit command/query separation)
- Event Sourcing: ❌ (Still traditional storage)
- Aggregates: ⚠️ (Optional, not enforced)

**How it works:**
- Commands handle write operations and orchestration
- Queries talk directly to optimized read databases
- Write model typically RDBMS or NoSQL
- No event-based storage

**Pros:**
- Clear separation of read/write concerns
- Can optimize read and write models independently
- Better scalability for read-heavy workloads

**Cons:**
- Doesn't support raw event storage
- Limited auditability
- No event replay capability
- Complex data synchronization

**When to use:** Systems with different read/write patterns but no need for event history

---

### 🔸 Option 3: Full CQRS + Event Sourcing + Aggregates (Book Architecture)
**Target State** - Ideal evolution of our system

**Characteristics:**
- CQRS: ✅ (Explicit commands and queries)
- Event Sourcing: ✅ (Raw event storage)
- Aggregates: ✅ (Domain-driven design)
- Explicit Commands & Queries: ✅

**How it works:**
- Raw CDC events stored in EventStore (write model)
- Aggregates (ClientAggregate, ProjectAggregate) mutate state from events
- Normalization logic applied in projection layer
- Commands orchestrate: write to store, dispatch Celery for projection
- Queries go to Elasticsearch (read model)
- Optional full state replay from EventStore for audits/rebuilds
- Celery tasks project to read DB, broadcast via SNS

**Structure:**
```
api/
application/
  commands/
  queries/
  mappers/
domain/
  aggregates/
  events/
infrastructure/
  event_store/
  read_model/  # Elasticsearch
  messaging/   # SNS
celery_tasks/
```

**Flow:**
1. Raw event ingested
2. Command validates + stores raw event
3. Event store persists as-is
4. Celery task triggers projection:
   - Aggregate loaded (mutate from events)
   - Normalization mapping happens
   - Indexed into Elasticsearch
5. Optional: Celery task broadcasts to SNS
6. Queries fetch from Elasticsearch

**Pros:**
- Complete audit trail
- Full event replay capability
- Clear domain modeling
- Flexible business rule evolution
- Excellent testability
- Supports complex business logic

**Cons:**
- Higher complexity
- Learning curve for team
- More moving parts
- Requires careful aggregate design

**When to use:** Complex domains with evolving business rules and audit requirements

---

### 🔸 Option 4: Explicit CQRS + Event Sourcing (Missing Aggregates)
**Current Implementation** - What we actually built

**Characteristics:**
- CQRS: ✅ (Explicit command/query service interfaces)
- Event Sourcing: ✅ (DynamoDB event store with event replay)
- Aggregates: ❌ (No domain aggregates, business logic in services)

**How it works:**
- **Command Service Interface**: `CrmCommandServiceInterface` with `process_event()`, `backfill_entity_type()`, `get_events()`
- **Query Service Interface**: `CrmQueryServiceInterface` with entity-specific query methods
- **Event Store**: DynamoDB with entity-based partitioning (`entity_name#entity_id`)
- **Read Model**: OpenSearch with denormalized documents
- **Event Processing**: Raw events stored, aggregate reconstruction via `_reconstruct_from_events()`
- **Projection**: Event replay → normalization → OpenSearch update → EventBridge broadcast

**Structure:**
```
application/
  services/
    interfaces/
      CrmCommandServiceInterface
      CrmQueryServiceInterface
    implementations/
      SalesForceCommandService
      DatabaseService
  dao/
    interfaces/
      EventDaoInterface
      EntityDaoInterface
    implementations/
      DynamoDBEventDao
      OpenSearchEntityDao
```

**Flow:**
1. Salesforce CDC event received
2. `SalesForceCommandService.process_event()` parses and validates
3. Raw event stored in DynamoDB via `DynamoDBEventDao`
4. `_compute_aggregate()` replays events for entity
5. `_normalize_event()` applies field mappings
6. Normalized event persisted to OpenSearch via `OpenSearchEntityDao`
7. Event broadcast via EventBridge
8. Queries served by `DatabaseService` from OpenSearch

**Key Features:**
- **Event Replay**: `_reconstruct_from_events()` builds current state from event history
- **Field Mappings**: Centralized mapping functions for each entity type
- **Validation Logic**: `_is_event_valid()` ensures event ordering and consistency
- **Backfill Support**: `backfill_entity_type()` for historical data ingestion
- **Async Processing**: Celery tasks for event processing and projection

**Pros:**
- ✅ Explicit CQRS separation via service interfaces
- ✅ Full event sourcing with DynamoDB
- ✅ Event replay capability for state reconstruction
- ✅ Scalable read model with OpenSearch
- ✅ Event broadcasting for downstream consumers
- ✅ Comprehensive field mapping system
- ✅ Production-ready with validation and error handling

**Cons:**
- ❌ Business logic scattered in service layer
- ❌ No domain aggregates for encapsulation
- ❌ Complex service methods handling multiple responsibilities
- ❌ Difficult to test business rules in isolation
- ❌ Tight coupling between event processing and business logic

**When to use:** Systems that need event sourcing and CQRS but can tolerate business logic in services

---

### 🔸 Option 5: Commands-as-Services (No Traditional Service Layer)
**Alternative Approach** - Command-focused design

**Characteristics:**
- CQRS: ✅ (Explicit commands)
- Event Sourcing: ⚠️ (Optional, can be added)
- Aggregates: ⚠️ (Optional, can be added)

**How it works:**
- Write classes like `StoreClientCommand` and call `command.execute()`
- Internal orchestration can include event storage
- Gives command/query encapsulation without service layer
- Can evolve into full CQRS+ES

**Pros:**
- Clear command boundaries
- Easy to test individual commands
- Can start simple and evolve
- Good for microservices

**Cons:**
- May not provide full event sourcing benefits
- Requires careful command design
- Can become complex with many commands

**When to use:** Systems where commands are the primary concern

---

### 🔸 Option 6: Python Event Sourcing Library
**Framework Approach** - Using existing libraries

**Characteristics:**
- CQRS: ⚠️ (Implicit in library design)
- Event Sourcing: ✅ (Built into library)
- Aggregates: ✅ (Library enforces pattern)

**How it works:**
- Aggregates defined with `mutate(event)` pattern
- Application class acts as service + repository
- Commands are just method calls
- Library handles event storage and replay

**Pros:**
- Mutate pattern is clean and clear
- Aggregate clarity and consistency
- Good naming conventions
- Handles boilerplate

**Cons:**
- Implicit commands/queries
- Difficult FastAPI integration
- Feels too magical/hacky
- Less control over architecture

**When to use:** When you want event sourcing without building it from scratch

---

### 🔸 Option 7: Custom CQRS + Event Sourcing + Aggregates (Idealized Vision)
**Our Target Architecture** - Full control and clarity

**Characteristics:**
- CQRS: ✅ (Explicit classes)
- Event Sourcing: ✅ (Raw event storage)
- Aggregates: ✅ (Mutates from events)
- Mapping/Projection: ✅ (Deferred to projection layer)
- Broadcast: ✅ (SNS via Celery)

**Structure:**
```
api/
application/
  commands/
  queries/
  mappers/
domain/
  aggregates/
  events/
infrastructure/
  event_store/
  read_model/  # Elasticsearch
  messaging/   # SNS
celery_tasks/
```

**Flow:**
1. Raw event ingested
2. Command called: validates + stores raw event
3. Event store persists as-is
4. Celery task triggers projection:
   - Aggregate loaded (mutate from events)
   - Normalization mapping happens
   - Indexed into Elasticsearch
5. Optional: Celery task broadcasts to SNS
6. Queries fetch from Elasticsearch

**Pros:**
- Complete control over architecture
- Clear separation of concerns
- Excellent testability
- Full audit trail
- Flexible evolution
- Perfect fit for our use case

**Cons:**
- Highest complexity
- Requires careful design
- More code to maintain
- Team needs to understand patterns

**When to use:** Complex domains where you need full control and maximum flexibility

---

## Recommendation for PyCon Presentation

### 🎯 Recommended Focus: Option 3 (Full CQRS + Event Sourcing + Aggregates)

**Why this option for the presentation:**

1. **Educational Value**: Shows the complete evolution from sophisticated to ideal
2. **Real-World Applicability**: Builds on your actual sophisticated implementation
3. **Pattern Clarity**: Demonstrates the final piece (aggregates) to complete the architecture
4. **Python Ecosystem**: Shows how FastAPI + Celery can handle enterprise architecture
5. **Audience Appeal**: Software engineers will appreciate seeing the evolution from a working system

### 📊 Presentation Structure:

1. **Current State** (3 min): Show Option 4 (your sophisticated implementation)
2. **What's Working** (2 min): Highlight the strengths of current approach
3. **The Missing Piece** (3 min): Why aggregates are the final evolution
4. **Target Architecture** (10 min): Deep dive into Option 3 with aggregates
5. **Implementation** (8 min): Code examples and migration patterns
6. **Benefits & Trade-offs** (2 min): When this makes sense

### 🔑 Key Messages:

- **You already have most of it**: Your current system is sophisticated and production-ready
- **Aggregates complete the picture**: Domain-driven design is the final piece
- **Python is capable**: Your implementation proves FastAPI + Celery can handle complex architecture
- **Evolution is natural**: Moving from services to aggregates is a natural progression

### 💡 Why Not Other Options:

- **Option 1**: Too basic, doesn't showcase your sophisticated work
- **Option 2**: Missing the event sourcing you already have
- **Option 4**: What you have, but not the complete picture
- **Option 5**: Good alternative but less comprehensive
- **Option 6**: Too framework-specific, less educational
- **Option 7**: Same as Option 3, just emphasizing custom implementation

The presentation should focus on **Option 3** as the target architecture, using your current **Option 4** implementation as the sophisticated foundation to show how aggregates complete the picture. This tells a compelling story of architectural evolution from a working, production-ready system to the ideal domain-driven design. 