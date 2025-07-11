# Event Sourcing System - Full CQRS + Aggregates Architecture

This directory contains the implementation of **Option 3: Full CQRS + Event Sourcing + Aggregates** architecture.

## 🏗️ Directory Structure

```
src/event_sourcing/
├── domain/                    # Business logic & domain models
│   ├── aggregates/           # Domain aggregates
│   │   ├── base.py          # Base aggregate ABC
│   │   ├── salesforce.py    # Salesforce-specific base aggregate
│   │   └── client.py        # Client aggregate implementation
│   ├── events/              # Domain events
│   │   ├── base.py          # Base domain event
│   │   └── client.py        # Client-specific events
│   └── mappings/            # Field mapping system
│       ├── base.py          # Base mapping structure
│       ├── client.py        # Client field mappings
│       └── registry.py      # Mapping registry
├── application/              # Application services & orchestration
│   ├── commands/            # Commands (write operations)
│   │   ├── base.py          # Base command structure
│   │   ├── salesforce.py    # Salesforce-specific commands
│   │   └── handlers/        # Command handlers
│   │       └── process_crm_event.py
│   ├── queries/             # Queries (read operations)
│   │   └── base.py          # Query definitions
│   └── services/            # Application services
│       └── backfill.py      # Backfill service
├── infrastructure/           # External concerns
│   ├── event_store.py       # Event persistence
│   ├── read_model.py        # Read model storage
│   └── messaging.py         # Event publishing
├── dto/                     # Data transfer objects
│   ├── base.py              # Base DTO
│   └── client.py            # Client DTO
├── tasks/                   # Celery tasks
│   └── process_crm_event.py
└── README.md               # This file
```

## 🎯 Key Design Decisions

### 1. **Base Aggregate Hierarchy**
- `BaseAggregate`: Abstract base with `apply()` method
- `SalesforceAggregate`: Salesforce-specific base with field mapping capabilities
- `ClientAggregate`: Concrete implementation for Client entity

### 2. **Command Input Design**
**Answer: NO** - Aggregates do NOT take commands as input. Commands are application layer concerns.
- Aggregates take raw data and apply business logic
- Command handlers orchestrate the process and call aggregate methods
- This maintains clean separation of concerns

### 3. **Event Design**
- Removed `ClientBackfillTriggeredEvent` as it's internal
- Use same event types (`Created`, `Updated`, `Deleted`) with source metadata
- Backfill events are marked with `source: "backfill"` in metadata

### 4. **Field Mapping System**
- Centralized in domain layer
- Registry pattern for entity mappings
- Applied during aggregate reconstruction
- Supports complex transformations and fallback logic

## 🔄 Data Flow

### Event Processing
1. **Salesforce CDC Event** → EventBridge → Lambda → API
2. **API** → Celery Task → Command Handler
3. **Command Handler** → Event Validation → Event Store
4. **Event Store** → Aggregate Reconstruction → Read Model
5. **Read Model** → Event Publishing → EventBridge

### Backfill Processing
1. **Backfill Trigger** → Backfill Service → Salesforce API
2. **Salesforce API** → Creation Commands → Command Processing Pipeline
3. **Command Pipeline** → Event Validation → Event Store
4. **Event Store** → Aggregate Reconstruction → Read Model

## 🚀 Next Steps

1. **Implement Infrastructure**: Complete PostgreSQL and EventBridge implementations
2. **Add More Aggregates**: Platform, Contract, Deal, Service, Subservice
3. **Add Query Handlers**: Implement query processing logic
4. **Add API Endpoints**: FastAPI endpoints for event ingestion and queries
5. **Add Tests**: Unit and integration tests for all components
6. **Add Monitoring**: Logging, metrics, and alerting

## 📝 Notes

- All components are designed to be testable in isolation
- Business logic is encapsulated in domain aggregates
- Infrastructure concerns are abstracted behind interfaces
- Field mappings can be updated without data migration
- Event validation ensures data consistency
- Backfill support handles historical data ingestion
