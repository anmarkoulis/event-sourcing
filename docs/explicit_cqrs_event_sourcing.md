# Explicit CQRS + Event Sourcing Architecture

## Overview

This document describes the **Option 4: Explicit CQRS + Event Sourcing (Missing Aggregates)** architecture that we actually implemented in production. This is a sophisticated event sourcing system that handles Salesforce CDC events with explicit command/query separation, full event replay capability, and production-ready infrastructure.

## 🎯 Architecture Goals

1. **Explicit CQRS**: Clear separation between commands (write) and queries (read) via service interfaces
2. **Event Sourcing**: Raw events stored as-is in DynamoDB, state reconstructed through replay
3. **Production Infrastructure**: Scalable, reliable, and maintainable system
4. **Field Mapping System**: Centralized transformation of Salesforce data to domain models
5. **Event Broadcasting**: Downstream integration via EventBridge
6. **Auditability**: Complete history preserved and replayable

## 🏗️ Current Architecture Structure

```
src/client_management_service/
├── application/
│   ├── services/
│   │   ├── interfaces/
│   │   │   ├── CrmCommandServiceInterface
│   │   │   └── CrmQueryServiceInterface
│   │   └── implementations/
│   │       ├── SalesForceCommandService
│   │       └── DatabaseService
│   ├── dao/
│   │   ├── interfaces/
│   │   │   ├── EventDaoInterface
│   │   │   └── EntityDaoInterface
│   │   └── implementations/
│   │       ├── DynamoDBEventDao
│   │       └── OpenSearchEntityDao
│   ├── clients/
│   │   ├── SalesforceClient
│   │   ├── AsyncEventBridgeClient
│   │   └── AsyncOpenSearchClient
│   └── tasks/
│       └── process_single_entity_task
├── dto/
│   ├── events/
│   │   ├── event.py
│   │   ├── salesforce.py
│   │   └── aggregated.py
│   ├── client.py
│   ├── contract.py
│   ├── deal.py
│   └── ...
├── utils/
│   └── salesforce/
│       └── mappings.py
└── main.py
```

## 🔄 Data Flow Architecture

### 1. Event Ingestion Flow
```
Salesforce CDC Event → EventBridge → Lambda → API Endpoint → Celery Task → Command Service → DynamoDB → Projection → OpenSearch + EventBridge Broadcast
```

**Detailed Steps:**
1. **Salesforce CDC Event** generated
2. **EventBridge** receives the CDC event
3. **Lambda** processes the event and calls API
4. **API Endpoint** receives event from Lambda
5. **Celery Task** triggered to process the event
6. **SalesForceCommandService** orchestrates the processing
7. **DynamoDB** persists raw event via `DynamoDBEventDao`
8. **Projection** reconstructs aggregate and applies mappings
9. **OpenSearch** updated with normalized data via `OpenSearchEntityDao`
10. **EventBridge** broadcasts normalized entity to downstream consumers

### 2. Query Flow
```
API Request → Query Service → OpenSearch → Response
```

### 3. Aggregate Reconstruction Flow
```
DynamoDB → Event Replay → Apply Mappings → Aggregate State
```

**Detailed Steps:**
1. **DynamoDB** retrieves all events for entity using `entity_name#entity_id` partition key
2. **Event Replay** applies events in chronological order via `_reconstruct_from_events()`
3. **Apply Mappings** transforms raw Salesforce data to domain model via `_normalize_event()`
4. **Aggregate State** represents current business state as `AggregatedData`

## 📋 Detailed Component Design

### Application Services Layer (`application/services/`)

#### Command Service Interface (`application/services/interfaces/CrmCommandServiceInterface`)
**Purpose**: Define contract for command operations

**Interface Methods**:
- `process_event(event: Any)` - Process raw Salesforce CDC events
- `backfill_entity_type(entity_name: str)` - Trigger backfill for entity type
- `get_events(entity: str, entity_id: str)` - Retrieve events for entity

#### SalesForceCommandService (`application/services/implementations/SalesForceCommandService`)
**Purpose**: Orchestrate event processing and state reconstruction

**Responsibilities**:
- Parse and validate Salesforce CDC events
- Store raw events in DynamoDB
- Reconstruct aggregate state from events
- Apply field mappings for normalization
- Persist normalized data to OpenSearch
- Broadcast events via EventBridge
- Handle backfill operations

**Key Methods**:
- `process_event(event: Any)` - Main event processing pipeline
- `_parse_events(serialized_event: str)` - Parse Salesforce CDC format
- `_compute_aggregate(entity_id: str, entity_name: str)` - Reconstruct state
- `_reconstruct_from_events(events: List[Event])` - Event replay logic
- `_normalize_event(event: Event)` - Apply field mappings
- `_is_event_valid(event: Event)` - Validate event ordering
- `backfill_entity_type(entity_name: str)` - Historical data ingestion

**Event Processing Pipeline**:
```python
async def process_event(self, event: Any) -> None:
    # 1. Parse Salesforce CDC event
    parsed_events = self._parse_events(event)
    
    for parsed_event in parsed_events:
        # 2. Validate event ordering
        if not await self._is_event_valid(parsed_event):
            continue
            
        # 3. Store raw event
        await self._persist_event(parsed_event)
        
        # 4. Reconstruct aggregate state
        full_model = await self._compute_aggregate(
            parsed_event.data.id, parsed_event.entity_name
        )
        
        # 5. Apply mappings and normalize
        normalized_event = self._normalize_event(full_model)
        
        # 6. Broadcast and persist
        await self.publish_normalized_event(normalized_event)
        await self.persist_normalized_event(normalized_event)
```

#### Query Service Interface (`application/services/interfaces/CrmQueryServiceInterface`)
**Purpose**: Define contract for query operations

**Interface Methods**:
- Entity-specific query methods (`get_clients()`, `get_contracts()`, etc.)
- Generic entity queries (`get_entities()`, `get_entity()`)
- Pagination, filtering, and sorting support

#### DatabaseService (`application/services/implementations/DatabaseService`)
**Purpose**: Execute queries against read model

**Responsibilities**:
- Query OpenSearch for entity data
- Handle pagination, filtering, and sorting
- Transform results to DTOs
- Provide generic entity query capabilities

**Key Methods**:
- `get_clients()`, `get_contracts()`, `get_deals()`, etc. - Entity-specific queries
- `get_entities(entity: str)` - Generic entity queries
- `_get()` - Generic query implementation with pagination
- `_get_one()` - Single entity retrieval
- `_compute_next_previous()` - Pagination URL generation

### Data Access Layer (`application/dao/`)

#### Event DAO Interface (`application/dao/interfaces/EventDaoInterface`)
**Purpose**: Abstract event storage operations

**Interface Methods**:
- `save_event(event: Event)` - Store event
- `get_events(entity_id: str, entity_name: str)` - Retrieve events

#### DynamoDBEventDao (`application/dao/implementations/DynamoDBEventDao`)
**Purpose**: Persist and retrieve events from DynamoDB

**Key Features**:
- **Partition Strategy**: `entity_name#entity_id` for efficient queries
- **Event Storage**: Raw events stored as DynamoDB items
- **Event Retrieval**: Query by partition key with optional time filtering
- **Concurrency**: Optimistic locking via version numbers

**Implementation Details**:
```python
class DynamoDBEventDao(EventDaoInterface):
    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        self.table_name = table_name
        self.region_name = region_name
    
    async def save_event(self, event: Event) -> None:
        # Store event with entity-based partitioning
        entity_key = self._create_entity_key(event.entity_name, event.data.id)
        item = event.to_dynamodb_compatible()
        item["entity_key"] = entity_key
        await table.put_item(Item=item)
    
    async def get_events(self, entity_id: str, entity_name: str) -> List[Event]:
        # Query events by partition key
        entity_key = self._create_entity_key(entity_name, entity_id)
        key_condition = Key("entity_key").eq(entity_key)
        response = await table.query(KeyConditionExpression=key_condition)
        return [Event(**item) for item in response.get("Items", [])]
    
    def _create_entity_key(self, entity_name: str, entity_id: str) -> str:
        return f"{entity_name}#{entity_id}"
```

#### Entity DAO Interface (`application/dao/interfaces/EntityDaoInterface`)
**Purpose**: Abstract read model operations

**Interface Methods**:
- `save_entity_from_event(event: Event)` - Persist normalized entity
- `get(entity: str, dto: Type[BaseModel], filters, sort, page, page_size)` - Query entities
- `get_one(entity: str, obj_id: str, dto: Type[BaseModel])` - Get single entity
- `count(entity: str, filters, sort)` - Count entities

#### OpenSearchEntityDao (`application/dao/implementations/OpenSearchEntityDao`)
**Purpose**: Manage read model in OpenSearch

**Key Features**:
- **Index Management**: Auto-create indices with proper mappings
- **Document Storage**: Denormalized entity documents
- **Query Building**: Dynamic query construction from filters and sorts
- **Pagination**: Efficient pagination with from/size parameters

**Implementation Details**:
```python
class OpenSearchEntityDao(EntityDaoInterface):
    def __init__(self, opensearch_client: AsyncOpenSearchClient, domain_name: str):
        self.opensearch_client = opensearch_client
        self.domain_name = domain_name
    
    async def save_entity_from_event(self, event: Event) -> None:
        # Store normalized entity in OpenSearch
        index_name = f"{event.entity_name.lower()}_index"
        document_id = event.entity_id
        document = event.to_eventbridge_compatible()
        await self.opensearch_client.index_document(
            index_name, document_id, document["data"]["values"]
        )
    
    async def get(self, entity_name: str, output_schema: Type[BaseModel], 
                  filters=None, sort=None, page=1, page_size=10) -> List[BaseModel]:
        # Query with pagination, filtering, and sorting
        index_name = f"{entity_name.lower()}_index"
        query = self.build_query(filters, sort, page, page_size)
        results = await self.opensearch_client.search_documents(index_name, query)
        return [output_schema(**hit["_source"]) for hit in results["hits"]["hits"]]
    
    def build_query(self, filters, sort, page=1, page_size=10, count=False):
        # Build complex OpenSearch queries from filters and sorts
        query = {"query": {"bool": {"must": []}}}
        if not count:
            query["from"] = (page - 1) * page_size
            query["size"] = page_size
        # Add filter and sort logic...
        return query
```

### Field Mapping System (`utils/salesforce/mappings.py`)

**Purpose**: Transform Salesforce data to domain models

**Key Features**:
- **Centralized Mappings**: One mapping function per entity type
- **Flexible Operations**: Lambda functions for complex transformations
- **Error Handling**: Graceful handling of missing fields
- **Type Safety**: Strongly typed mapping operations

**Mapping Structure**:
```python
MappedField = namedtuple("MappedField", ["value", "operation"])

def get_client_mappings() -> Dict[str, MappedField]:
    return {
        "id": MappedField("Id", lambda rec, _: rec["Id"]),
        "name": MappedField("Name", lambda rec, _: rec["Name"]),
        "parent_id": MappedField("ParentId", lambda rec, _: rec.get("ParentId", None)),
        "business_types": MappedField("Business_Type__c", get_list_from_string),
        "status": MappedField("Account_Status__c", lambda rec, _: rec.get("Account_Status__c")),
        "currency": MappedField("CurrencyIsoCode", lambda rec, _: rec.get("CurrencyIsoCode")),
        "billing_country": MappedField("BillingCountry", lambda rec, _: rec.get("BillingCountry")),
        "priority": MappedField("Account_Priority__c", lambda rec, _: rec.get("Account_Priority__c")),
        "sso_id": MappedField("Orfium_SSO_ID_Comp__c", lambda rec, _: rec.get("Orfium_SSO_ID_Comp__c") or rec.get("Orfium_SSO_ID_SR__c")),
        "description": MappedField("Description", lambda rec, _: rec.get("Description")),
        "is_deleted": MappedField("IsDeleted", lambda rec, _: rec.get("IsDeleted")),
        "last_modified_date": MappedField("LastModifiedDate", get_date_time),
        "system_modified_stamp": MappedField("SystemModstamp", get_date_time),
        "last_activity_date": MappedField("LastActivityDate", get_date),
        "created_date": MappedField("CreatedDate", get_date_time),
    }
```

**Mapping Application**:
```python
def _normalize_event(self, event: Event) -> Event:
    entity, mappings = self._get_normalized_entity_and_mappings(event.entity_name)
    changed_values = event.data.values
    normalized_data = {}

    for key, mapping in mappings().items():
        try:
            normalized_data[key] = (
                mapping.operation(changed_values, mapping.value)
                if callable(mapping.operation)
                else mapping.value
            )
        except KeyError:
            continue
    
    return Event(
        event_id=event.event_id,
        entity_name=entity,
        entity_id=event.entity_id,
        event_type=event.event_type,
        timestamp=event.timestamp,
        version=event.version,
        data=AggregatedData(values=normalized_data),
    )
```

### External Clients (`application/clients/`)

#### SalesforceClient
**Purpose**: Interface with Salesforce API

**Key Features**:
- **Entity Retrieval**: Get entities by type with pagination
- **Single Entity**: Retrieve specific entity by ID
- **Authentication**: Handle Salesforce authentication
- **Rate Limiting**: Respect API limits

#### AsyncEventBridgeClient
**Purpose**: Publish events to EventBridge

**Key Features**:
- **Event Publishing**: Send normalized events to EventBridge
- **Error Handling**: Handle publishing failures gracefully
- **Async Operations**: Non-blocking event publishing

#### AsyncOpenSearchClient
**Purpose**: Interface with OpenSearch

**Key Features**:
- **Document Operations**: Index, search, and retrieve documents
- **Index Management**: Create and manage indices
- **Query Execution**: Execute complex search queries
- **Connection Management**: Handle OpenSearch connections

## 🔄 Event Processing Pipeline

### 1. Raw Event Ingestion
```
Salesforce CDC Event → EventBridge → Lambda → API → Celery Task → SalesForceCommandService → DynamoDB
```

**Steps**:
1. **Salesforce** generates CDC event
2. **EventBridge** receives and routes event
3. **Lambda** processes event and calls API
4. **API endpoint** receives event from Lambda
5. **Celery task** triggered for async processing
6. **SalesForceCommandService.process_event()** orchestrates processing:
   - Parse Salesforce CDC format via `_parse_events()`
   - Validate event ordering via `_is_event_valid()`
   - Store raw event in DynamoDB via `DynamoDBEventDao`
   - Trigger aggregate reconstruction
7. Return success acknowledgment

### 2. Event Projection & Broadcasting
```
DynamoDB → Event Replay → Apply Mappings → OpenSearch Update → EventBridge Broadcast
```

**Steps**:
1. **Event replay** triggered by event persistence
2. **Load events** for affected entity from DynamoDB
3. **Reconstruct aggregate** by replaying events via `_reconstruct_from_events()`
4. **Apply mappings** to transform raw Salesforce data via `_normalize_event()`
5. **Update OpenSearch** with normalized data via `OpenSearchEntityDao`
6. **Broadcast normalized entity** via EventBridge to downstream consumers
7. **Log completion** for monitoring

### 3. Query Processing
```
API Request → DatabaseService → OpenSearch → Response
```

**Steps**:
1. Receive API request
2. **DatabaseService** method called (e.g., `get_clients()`)
3. **OpenSearchEntityDao** executes query against OpenSearch
4. Transform results to DTOs
5. Return paginated response

## 📊 Data Models

### Event Models (`dto/events/`)

#### Base Event (`dto/events/event.py`)
```python
class Event(BaseModel):
    event_id: str
    entity_name: str
    entity_id: str
    event_type: EventType
    timestamp: datetime
    version: str
    data: Union[SalesforceEventData, AggregatedData]
```

#### Salesforce Event Data (`dto/events/salesforce.py`)
```python
class ChangeEventHeader(BaseModel):
    changeOrigin: str
    changeType: str
    changedFields: List[str]
    commitNumber: int
    commitTimestamp: int
    commitUser: str
    entityName: str
    recordIds: List[str]
    sequenceNumber: float
    transactionKey: str
    changedValues: Dict[str, Any]

class Payload(BaseModel):
    ChangeEventHeader: ChangeEventHeader

class SalesforceEventData(BaseModel):
    payload: Payload
    id: str
    schemaId: str
```

#### Aggregated Data (`dto/events/aggregated.py`)
```python
class AggregatedData(BaseModel):
    values: Dict[str, Any]
```

### Entity DTOs (`dto/`)

#### Client DTO (`dto/client.py`)
```python
class ClientDTO(BaseModel):
    id: str | None = None
    name: str | None = None
    parent_id: str | None = None
    business_types: List[str] | None = None
    status: str | None = None
    currency: str | None = None
    billing_country: str | None = None
    priority: str | None = None
    sso_id: str | None = None
    sso_id_c: str | None = None
    sso_id_r: str | None = None
    description: str | None = None
    is_deleted: bool | None = None
    last_modified_date: datetime | None = None
    system_modified_stamp: datetime | None = None
    last_activity_date: datetime | None = None
    created_date: datetime | None = None
```

### Query Models

#### Page DTO (`dto/page.py`)
```python
class PageDTO(BaseModel):
    results: List[Any]
    count: int
    next: Optional[str]
    previous: Optional[str]
```

#### Filter DTO (`dto/filter.py`)
```python
class FilterDTO(BaseModel):
    field: str
    operator: OperatorEnum
    value: Any
```

#### Sort DTO (`dto/sort.py`)
```python
class SortDTO(BaseModel):
    field: str
    order: SortOrderEnum
```

## 🧪 Testing Strategy

### Unit Tests
- **Service Tests**: Test command and query service logic
- **DAO Tests**: Test data access layer operations
- **Mapping Tests**: Test field mapping transformations
- **Event Processing Tests**: Test event parsing and validation

### Integration Tests
- **DynamoDB Tests**: Test event storage and retrieval
- **OpenSearch Tests**: Test read model operations
- **EventBridge Tests**: Test event publishing
- **End-to-End Tests**: Test complete workflows

### Test Data
- **Event Fixtures**: Predefined Salesforce CDC events
- **Entity Fixtures**: Predefined entity states
- **Mapping Fixtures**: Test data for field mappings

## 🔧 Implementation Phases

### Phase 1: Foundation (Completed)
1. ✅ Set up service interfaces and implementations
2. ✅ Implement DynamoDB event store
3. ✅ Create OpenSearch read model
4. ✅ Set up field mapping system
5. ✅ Implement event processing pipeline

### Phase 2: Event Processing (Completed)
1. ✅ Implement Salesforce CDC event parsing
2. ✅ Create event validation logic
3. ✅ Set up event replay mechanism
4. ✅ Add normalization and mapping
5. ✅ Implement EventBridge broadcasting

### Phase 3: Query Layer (Completed)
1. ✅ Implement query service interface
2. ✅ Create OpenSearch query builder
3. ✅ Add pagination and filtering
4. ✅ Implement entity-specific queries
5. ✅ Add generic entity queries

### Phase 4: Integration (Completed)
1. ✅ Create FastAPI endpoints
2. ✅ Implement Celery tasks
3. ✅ Add EventBridge integration
4. ✅ Set up monitoring and logging
5. ✅ Implement Lambda integration

### Phase 5: Production Optimization (Completed)
1. ✅ Optimize DynamoDB queries
2. ✅ Fine-tune OpenSearch performance
3. ✅ Add error handling and retries
4. ✅ Implement backfill capabilities
5. ✅ Add comprehensive logging

## 🎯 Benefits of This Architecture

### 1. **Auditability**
- ✅ Complete event history in DynamoDB
- ✅ Immutable event log with versioning
- ✅ Full audit trail for all changes
- ✅ Event replay capability for state reconstruction

### 2. **Scalability**
- ✅ DynamoDB auto-scaling for event storage
- ✅ OpenSearch distributed search capabilities
- ✅ EventBridge for decoupled event publishing
- ✅ Async processing with Celery

### 3. **Flexibility**
- ✅ Field mappings can be updated without data migration
- ✅ New entity types can be added easily
- ✅ Event processing logic is centralized
- ✅ Query layer supports complex filtering and sorting

### 4. **Production Ready**
- ✅ Comprehensive error handling
- ✅ Event validation and ordering
- ✅ Backfill support for historical data
- ✅ Monitoring and logging throughout

### 5. **Maintainability**
- ✅ Clear separation of concerns via interfaces
- ✅ Centralized field mapping system
- ✅ Consistent patterns across entities
- ✅ Well-defined data models

## 🚨 Considerations & Trade-offs

### Complexity
- **Service layer complexity**: Business logic scattered across services
- **Event processing complexity**: Multiple responsibilities in single service
- **Mapping complexity**: Field mappings need careful maintenance
- **Infrastructure complexity**: Multiple AWS services to manage

### Performance
- **Event replay overhead**: Reconstructing state from events can be expensive
- **DynamoDB query costs**: Event retrieval by partition key
- **OpenSearch indexing**: Real-time indexing of normalized data
- **EventBridge latency**: Asynchronous event publishing

### Operational
- **DynamoDB management**: Table provisioning and monitoring
- **OpenSearch management**: Index management and optimization
- **EventBridge monitoring**: Event publishing success/failure tracking
- **Celery task management**: Worker scaling and monitoring

### Limitations
- **No domain aggregates**: Business logic not encapsulated in domain objects
- **Service coupling**: Tight coupling between event processing and business logic
- **Testing complexity**: Business logic difficult to test in isolation
- **Evolution challenges**: Business rules changes require service modifications

## 📈 Evolution Path

### Current State (Option 4)
- ✅ Explicit CQRS via service interfaces
- ✅ Full event sourcing with DynamoDB
- ✅ Event replay capability
- ✅ Production-ready infrastructure
- ✅ Comprehensive field mapping system

### Target State (Option 3)
- 🔄 Extract domain logic into aggregates
- 🔄 Create explicit command/query objects
- 🔄 Separate business logic from infrastructure
- 🔄 Improve testability of business rules
- 🔄 Enable easier business rule evolution

### Migration Strategy
1. **Parallel implementation** of domain aggregates
2. **Gradual migration** of business logic
3. **Feature flags** for new vs old code
4. **Data synchronization** during transition
5. **Complete switch** once stable

This architecture provides a solid, production-ready foundation for event sourcing and CQRS patterns, with the infrastructure and patterns in place to evolve toward domain-driven design when needed. 