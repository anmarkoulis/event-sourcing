# Infrastructure Layer

This directory contains the infrastructure implementation for the event sourcing system, providing concrete implementations of the abstract interfaces defined in the domain and application layers.

## Structure

```
infrastructure/
├── database/                 # Database infrastructure
│   ├── __init__.py
│   ├── base.py              # Base model and declarative base
│   ├── session.py           # Database session management
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── event.py         # Event model for event store
│   │   └── client.py        # Client model for read model
│   └── alembic/             # Database migrations
│       ├── __init__.py
│       ├── env.py           # Alembic environment
│       ├── alembic.ini      # Alembic configuration
│       ├── script.py.mako   # Migration template
│       └── versions/        # Migration files
│           ├── __init__.py
│           └── 0001_initial.py
├── event_store.py           # PostgreSQL event store implementation
├── read_model.py            # PostgreSQL read model implementation
├── messaging.py             # EventBridge messaging implementation
├── factory.py               # Infrastructure component factory
└── README.md               # This file
```

## Database Models

### Event Model
The `Event` model stores domain events with the following key fields:
- `event_id`: Unique identifier for the event
- `aggregate_id`: ID of the aggregate that produced the event
- `aggregate_type`: Type of aggregate (e.g., "Client")
- `event_type`: Type of event (e.g., "ClientCreated")
- `timestamp`: When the event occurred
- `version`: Event version for schema evolution
- `data`: JSON payload containing event data
- `metadata`: Additional metadata (user, source, etc.)
- `validation_info`: Validation metadata
- `source`: Source system (e.g., "salesforce", "backfill")

### Client Model
The `Client` model represents the denormalized read model for clients:
- `aggregate_id`: Unique identifier for the client aggregate
- `salesforce_id`: Original Salesforce ID
- `name`, `status`, `priority`: Basic client information
- `business_types`: Array of business types
- `sso_id*`: SSO-related fields
- `is_deleted`: Soft delete flag
- `version`: Event sourcing version
- `raw_data`: Original Salesforce data for debugging

## Database Management

### Session Management
The `DatabaseManager` class provides:
- Async database engine creation
- Session factory with proper configuration
- Connection pooling and health checks
- Graceful shutdown

### Context Manager
The `AsyncDBContextManager` provides:
- Automatic session lifecycle management
- Proper cleanup on exceptions
- Async context manager support

## Infrastructure Components

### Event Store
The `PostgreSQLEventStore` implements:
- Event persistence with validation metadata
- Aggregate event retrieval with time filtering
- Event type and source-based queries
- Efficient indexing for performance

### Read Model
The `PostgreSQLReadModel` implements:
- Client data persistence and updates
- Search functionality with filtering
- Pagination support
- Status and country-based queries

### Event Publisher
The `EventBridgePublisher` implements:
- Event broadcasting to AWS EventBridge
- Event normalization and transformation
- Error handling and retry logic

## Factory Pattern

The `InfrastructureFactory` provides:
- Centralized component creation
- Dependency injection support
- Resource lifecycle management
- Configuration management

## Database Migrations

### Alembic Setup
- Configured for async PostgreSQL
- Automatic model discovery
- Migration generation and execution
- Rollback support

### Initial Migration
The `0001_initial.py` migration creates:
- `event` table with all necessary indexes
- `client` table with optimized indexes
- Composite indexes for efficient querying
- JSONB columns for flexible data storage

## Usage Example

```python
from event_sourcing.infrastructure.factory import InfrastructureFactory

# Create factory
factory = InfrastructureFactory(
    database_url="postgresql+asyncpg://user:pass@localhost/event_sourcing",
    eventbridge_region="us-east-1"
)

# Get components
event_store = factory.event_store
read_model = factory.read_model
event_publisher = factory.event_publisher

# Use components
await event_store.save_event(domain_event)
clients = await read_model.search_clients(search_query)
await event_publisher.publish_event(normalized_event)

# Clean up
await factory.close()
```

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `EVENTBRIDGE_REGION`: AWS region for EventBridge
- `AWS_ACCESS_KEY_ID`: AWS access key (for production)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (for production)

### Database Configuration
- Connection pooling with health checks
- Async support with SQLAlchemy 2.0
- JSONB for flexible data storage
- Optimized indexes for query performance

## Performance Considerations

### Indexing Strategy
- Composite indexes for common query patterns
- Separate indexes for individual fields
- Covering indexes for read-heavy operations
- Partial indexes for filtered queries

### Connection Management
- Connection pooling to reduce overhead
- Health checks to detect stale connections
- Proper cleanup to prevent resource leaks
- Async operations for better concurrency

## Monitoring and Observability

### Logging
- Structured logging with correlation IDs
- Performance metrics for database operations
- Error tracking with context information
- Audit trail for data changes

### Metrics
- Database connection pool metrics
- Query performance monitoring
- Event processing latency
- Error rates and retry counts
