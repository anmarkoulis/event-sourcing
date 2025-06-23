# Full CQRS + Event Sourcing + Aggregates Architecture

## Overview

This document describes the target architecture for implementing **Option 3: Full CQRS + Event Sourcing + Aggregates** in our event sourcing system. We'll focus on the client model as our primary example, showing how to evolve from the current layered architecture to a clean, domain-driven design with comprehensive production capabilities.

## 🎯 Architecture Goals

1. **Explicit CQRS**: Clear separation between commands (write) and queries (read)
2. **Event Sourcing**: Raw events stored as-is, state reconstructed through replay
3. **Domain Aggregates**: Business logic encapsulated in domain objects
4. **Clean Architecture**: Clear boundaries between layers
5. **Testability**: Easy to test business logic in isolation
6. **Evolvability**: Business rules can change without data migration
7. **Event Validation**: Comprehensive validation and ordering logic
8. **Backfill Support**: Historical data ingestion and processing
9. **Production Infrastructure**: Scalable, reliable, and maintainable system
10. **Field Mapping System**: Centralized transformation of Salesforce data to domain models

## 🏗️ Target Architecture Structure

```
src/event_sourcing/
├── api/                    # FastAPI endpoints (queries only)
├── application/            # Application services & orchestration
│   ├── commands/          # Command handlers
│   ├── queries/           # Query handlers
│   ├── mappers/           # Data transformation
│   ├── services/          # Application services
│   └── validators/        # Event validation logic
├── domain/                # Business logic & domain models
│   ├── aggregates/        # Domain aggregates
│   ├── events/            # Domain events
│   ├── entities/          # Domain entities
│   ├── value_objects/     # Value objects
│   └── mappings/          # Field mapping system
├── infrastructure/        # External concerns
│   ├── event_store/       # Event persistence
│   ├── read_model/        # Read model storage
│   ├── messaging/         # Event publishing
│   ├── repositories/      # Repository implementations
│   └── backfill/          # Backfill processing
└── shared/                # Shared utilities
    ├── dto/               # Data transfer objects
    └── exceptions/        # Custom exceptions
```

## 🔄 Data Flow Architecture

### 1. Event Ingestion Flow
```
Salesforce CDC Event → EventBridge → Lambda → API Endpoint → Celery Task → Command Handler → Validation → Event Store → Aggregate Reconstruction → Projection → Read Model + Event Publishing
```

**Detailed Steps:**
1. **Salesforce CDC Event** generated
2. **EventBridge** receives the CDC event
3. **Lambda** processes the event and calls API
4. **API Endpoint** receives event from Lambda
5. **Celery Task** triggered to process the event
6. **Command Handler** orchestrates the processing
7. **Event Validation** ensures proper ordering and consistency
8. **Event Store** persists raw event
9. **Aggregate Reconstruction** replays events and applies mappings
10. **Projection** updates read model with normalized data
11. **Event Publisher** broadcasts normalized entity to downstream consumers

### 2. Query Flow
```
API Request → Query Handler → Read Model (PostgreSQL) → Response
```

### 3. Aggregate Reconstruction Flow
```
Event Store → Aggregate Loader → Event Replay → Apply Mappings → Aggregate State
```

**Detailed Steps:**
1. **Event Store** retrieves all events for aggregate ID
2. **Aggregate Loader** creates empty aggregate
3. **Event Replay** applies events in chronological order
4. **Apply Mappings** transforms raw Salesforce data to domain model
5. **Aggregate State** represents current business state

### 4. Backfill Flow
```
Salesforce API → Batch Processing → Creation Commands → Command Processing Pipeline
```

**Detailed Steps:**
1. **Backfill Service** queries Salesforce API for historical data
2. **Batch Processing** handles pagination and rate limiting
3. **Creation Commands** generated for each historical entity
4. **Command Processing Pipeline** processes each creation command
5. **Event Validation** ensures proper event ordering
6. **Aggregate Reconstruction** builds current state from events

## 📋 Detailed Component Design

### Domain Layer (`domain/`)

#### Client Aggregate (`domain/aggregates/client.py`)
**Purpose**: Encapsulate client business logic and state transitions

**Responsibilities**:
- Apply domain events to mutate state
- Enforce business rules
- Generate new domain events
- Maintain aggregate consistency
- Apply mappings during reconstruction
- Validate event ordering and consistency
- Handle backfill scenarios

**Key Methods**:
- `apply(event: DomainEvent)` - Apply event to aggregate state
- `create_client(command: CreateClientCommand)` - Create new client
- `update_client(command: UpdateClientCommand)` - Update client
- `delete_client(command: DeleteClientCommand)` - Mark client as deleted
- `get_snapshot()` - Return current state snapshot
- `apply_mappings(raw_data: dict)` - Apply field mappings to raw data
- `validate_event_ordering(event: DomainEvent)` - Validate event ordering
- `handle_backfill_scenario(event: DomainEvent)` - Handle backfill scenarios

**State Management**:
- Aggregate maintains current state
- State changes only through event application
- Immutable event history
- Version tracking for concurrency control
- Mappings applied during state reconstruction
- Event validation ensures consistency

**Event Validation Logic**:
```python
class ClientAggregate:
    def validate_event_ordering(self, event: DomainEvent) -> bool:
        """Validate event ordering and consistency"""
        if event.event_type == "Created":
            # Creation event should be first
            if self.version > 0:
                logger.warning(f"Creation event received for existing client {self.client_id}")
                return False
            return True
        else:
            # Non-creation events require existing client
            if self.version == 0:
                logger.warning(f"Non-creation event received for non-existent client {self.client_id}")
                return False
            return True

    def handle_backfill_scenario(self, event: DomainEvent) -> None:
        """Handle backfill scenarios by triggering backfill"""
        if not self.validate_event_ordering(event):
            logger.info(f"Triggering backfill for client {self.client_id}")
            # Trigger backfill command
            backfill_command = BackfillClientCommand(
                client_id=self.client_id,
                entity_name="Account",
                trigger_event=event
            )
            # Publish backfill command
            self.event_publisher.publish(backfill_command)
```

#### Domain Events (`domain/events/`)
**Purpose**: Represent business events that have occurred

**Generic Event Structure**:
```python
class DomainEvent(BaseModel):
    event_id: str
    aggregate_id: str
    aggregate_type: str  # "client", "project", etc.
    event_type: str      # "Created", "Updated", "Deleted"
    timestamp: datetime
    version: str
    data: Dict[str, Any]  # Generic event data
    metadata: Dict[str, Any]  # User, source, etc.
    validation_info: Optional[Dict[str, Any]] = None  # Validation metadata
```

**Event Types**:
- `ClientCreatedEvent`
- `ClientUpdatedEvent`
- `ClientDeletedEvent`
- `ClientBackfillTriggeredEvent`

#### Domain Entities (`domain/entities/`)
**Purpose**: Core business objects

**Client Entity** (Simplified for Demo):
- Business identity (ID)
- Business attributes (name, parent_id, status, created_at, updated_at)
- Business methods
- Invariants and validation

#### Field Mapping System (`domain/mappings/`)
**Purpose**: Centralized field mapping for all entities

**Mapping Structure**:
```python
MappedField = namedtuple("MappedField", ["value", "operation"])

class ClientMappings:
    @staticmethod
    def get_mappings() -> Dict[str, MappedField]:
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
            "sso_id_c": MappedField("Orfium_SSO_ID_Comp__c", lambda rec, _: rec.get("Orfium_SSO_ID_Comp__c")),
            "sso_id_r": MappedField("Orfium_SSO_ID_SR__c", lambda rec, _: rec.get("Orfium_SSO_ID_SR__c")),
            "description": MappedField("Description", lambda rec, _: rec.get("Description")),
            "is_deleted": MappedField("IsDeleted", lambda rec, _: rec.get("IsDeleted")),
            "last_modified_date": MappedField("LastModifiedDate", get_date_time),
            "system_modified_stamp": MappedField("SystemModstamp", get_date_time),
            "last_activity_date": MappedField("LastActivityDate", get_date),
            "created_date": MappedField("CreatedDate", get_date_time),
        }

class MappingRegistry:
    """Central registry for all entity mappings"""
    
    _mappings = {
        "Account": ClientMappings,
        "Platform__c": PlatformMappings,
        "Contract": ContractMappings,
        "Opportunity": DealMappings,
        "OpportunityLineItem": ServiceMappings,
        "Product2": SubserviceMappings,
    }
    
    @classmethod
    def get_mappings(cls, entity_name: str) -> Type[BaseMappings]:
        return cls._mappings.get(entity_name)
    
    @classmethod
    def get_normalized_entity_name(cls, entity_name: str) -> str:
        normalization_dict = {
            "Account": "client",
            "Platform__c": "platform",
            "Contract": "contract",
            "Opportunity": "deal",
            "OpportunityLineItem": "service",
            "Product2": "subservice",
        }
        return normalization_dict.get(entity_name, entity_name.lower())
```

### Application Layer (`application/`)

#### Commands (`application/commands/`)
**Purpose**: Represent intentions to change system state

**Command Types**:
- `CreateClientCommand`
- `UpdateClientCommand`
- `DeleteClientCommand`
- `BackfillClientCommand`
- `ProcessSalesforceEventCommand`
- `BackfillEntityTypeCommand`

**Command Structure**:
- Command ID
- Target aggregate ID
- Command data
- Metadata (user, timestamp)
- Validation context

#### Command Handlers (`application/commands/handlers/`)
**Purpose**: Orchestrate command execution

**Responsibilities**:
- Validate commands
- Load aggregates from event store
- Execute business logic
- Persist events
- Trigger projection and broadcasting
- Apply mappings during aggregate reconstruction
- Handle event validation and ordering
- Manage backfill operations

**Handler Pattern**:
```python
class ProcessSalesforceEventCommandHandler:
    def __init__(self, event_store, client_repository, projection_service, event_publisher, backfill_service):
        self.event_store = event_store
        self.client_repository = client_repository
        self.projection_service = projection_service
        self.event_publisher = event_publisher
        self.backfill_service = backfill_service
    
    async def handle(self, command: ProcessSalesforceEventCommand):
        logger.info(f"Processing Salesforce event: {command.data.raw_event}")
        
        # 1. Parse and validate raw event
        parsed_events = self._parse_salesforce_event(command.data.raw_event)
        
        for parsed_event in parsed_events:
            # 2. Validate event ordering and consistency
            is_valid = await self._validate_event_ordering(parsed_event)
            if not is_valid:
                logger.warning(f"Event validation failed: {parsed_event}")
                continue
            
            # 3. Store raw event
            await self.event_store.save_event(parsed_event)
            
            # 4. Reconstruct aggregate with mappings
            client = await self._reconstruct_aggregate(parsed_event.aggregate_id)
            
            # 5. Update read model
            await self.projection_service.project_client(client)
            
            # 6. Publish normalized entity
            await self.event_publisher.publish(client.get_snapshot())
    
    async def _validate_event_ordering(self, event: DomainEvent) -> bool:
        """Validate event ordering and consistency"""
        existing_events = await self.event_store.get_events(event.aggregate_id, event.aggregate_type)
        
        if event.event_type == "Created":
            if existing_events:
                logger.warning(f"Creation event received for existing aggregate {event.aggregate_id}")
                return False
        else:
            if not existing_events:
                logger.warning(f"Non-creation event received for non-existent aggregate {event.aggregate_id}")
                # Trigger backfill
                await self.backfill_service.trigger_backfill(event.aggregate_id, event.aggregate_type)
                return False
        
        return True
    
    async def _reconstruct_aggregate(self, aggregate_id: str) -> ClientAggregate:
        """Reconstruct aggregate from events with mappings applied"""
        events = await self.event_store.get_events(aggregate_id, "client")
        client = ClientAggregate(aggregate_id)
        
        for event in events:
            # Apply mappings during reconstruction
            mapped_data = self._apply_mappings(event.data, "Account")
            event.data = mapped_data
            client.apply(event)
        
        return client
    
    def _apply_mappings(self, raw_data: dict, entity_name: str) -> dict:
        """Apply field mappings to raw data"""
        mappings_class = MappingRegistry.get_mappings(entity_name)
        if not mappings_class:
            return raw_data
        
        mappings = mappings_class.get_mappings()
        mapped_data = {}
        
        for key, mapping in mappings.items():
            try:
                mapped_data[key] = (
                    mapping.operation(raw_data, mapping.value)
                    if callable(mapping.operation)
                    else mapping.value
                )
            except KeyError:
                continue
        
        return mapped_data
```

#### Backfill Service (`application/services/backfill_service.py`)
**Purpose**: Handle historical data ingestion and processing

**Responsibilities**:
- Query Salesforce API for historical data
- Generate creation commands for historical entities
- Handle batch processing and pagination
- Manage rate limiting and quotas
- Coordinate backfill operations
- Monitor backfill progress

**Implementation**:
```python
class BackfillService:
    def __init__(self, salesforce_client, command_bus, event_store):
        self.salesforce_client = salesforce_client
        self.command_bus = command_bus
        self.event_store = event_store
    
    async def backfill_entity_type(self, entity_name: str) -> None:
        """Backfill all entities of a specific type"""
        logger.info(f"Starting backfill for entity type: {entity_name}")
        
        page = 1
        page_size = 50
        
        while True:
            has_next = await self._backfill_page(entity_name, page, page_size)
            if not has_next:
                break
            page += 1
        
        logger.info(f"Completed backfill for entity type: {entity_name}")
    
    async def _backfill_page(self, entity_name: str, page: int, page_size: int) -> bool:
        """Process a single page of entities for backfill"""
        logger.debug(f"Fetching {entity_name} from Salesforce, page {page}")
        
        entities_page = await self.salesforce_client.get_entities(
            entity=entity_name, page=page, page_size=page_size
        )
        
        if not entities_page.results:
            logger.debug("No more entities to fetch")
            return False
        
        for entity in entities_page.results:
            # Generate creation command for each entity
            creation_command = self._create_creation_command(entity, entity_name)
            await self.command_bus.send(creation_command)
        
        return bool(entities_page.next)
    
    async def trigger_backfill(self, aggregate_id: str, aggregate_type: str) -> None:
        """Trigger backfill for a specific aggregate"""
        logger.info(f"Triggering backfill for {aggregate_type} {aggregate_id}")
        
        # Get entity from Salesforce
        entity = await self.salesforce_client.get_entity(aggregate_id, aggregate_type)
        if entity:
            creation_command = self._create_creation_command(entity, aggregate_type)
            await self.command_bus.send(creation_command)
    
    def _create_creation_command(self, entity: dict, entity_name: str) -> Command:
        """Create a creation command from entity data"""
        normalized_entity_name = MappingRegistry.get_normalized_entity_name(entity_name)
        
        if normalized_entity_name == "client":
            return CreateClientCommand(
                client_id=entity["Id"],
                data=entity,
                metadata={"source": "backfill", "entity_name": entity_name}
            )
        # Add other entity types as needed
    
    async def get_backfill_status(self, entity_type: str) -> Dict[str, Any]:
        """Get status of backfill operation"""
        # Implementation for tracking backfill progress
        pass
```

#### Event Validators (`application/validators/`)
**Purpose**: Validate events and ensure consistency

**Validation Types**:
- Event ordering validation
- Data consistency validation
- Business rule validation
- Schema validation

**Implementation**:
```python
class EventValidator:
    """Validate events before processing"""
    
    @staticmethod
    async def validate_event(event: DomainEvent, existing_events: List[DomainEvent]) -> ValidationResult:
        """Validate event ordering and consistency"""
        validation_result = ValidationResult()
        
        # Check event ordering
        if not EventValidator._validate_ordering(event, existing_events):
            validation_result.add_error("Event ordering violation")
        
        # Check data consistency
        if not EventValidator._validate_consistency(event, existing_events):
            validation_result.add_error("Data consistency violation")
        
        # Check business rules
        if not EventValidator._validate_business_rules(event):
            validation_result.add_error("Business rule violation")
        
        return validation_result
    
    @staticmethod
    def _validate_ordering(event: DomainEvent, existing_events: List[DomainEvent]) -> bool:
        """Validate event ordering"""
        if event.event_type == "Created":
            return len(existing_events) == 0
        else:
            return len(existing_events) > 0
    
    @staticmethod
    def _validate_consistency(event: DomainEvent, existing_events: List[DomainEvent]) -> bool:
        """Validate data consistency"""
        # Implementation for data consistency checks
        return True
    
    @staticmethod
    def _validate_business_rules(event: DomainEvent) -> bool:
        """Validate business rules"""
        # Implementation for business rule validation
        return True

class ValidationResult:
    """Result of event validation"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
```

#### Queries (`application/queries/`)
**Purpose**: Read-only operations against read model

**Query Types**:
- `GetClientQuery`
- `SearchClientsQuery`
- `GetClientHistoryQuery`
- `GetBackfillStatusQuery`

#### Query Handlers (`application/queries/handlers/`)
**Purpose**: Execute queries against read model

**Responsibilities**:
- Translate queries to read model operations
- Handle pagination, filtering, sorting
- Return DTOs (not domain objects)
- Support complex query operations

#### Mappers (`application/mappers/`)
**Purpose**: Transform between different data representations

**Mapping Types**:
- `SalesforceToDomainMapper` - Raw Salesforce data to domain events
- `DomainToReadModelMapper` - Domain state to read model
- `DomainToDTOMapper` - Domain objects to API DTOs
- `ClientMappings` - Field mappings for client entity

### Infrastructure Layer (`infrastructure/`)

#### Event Store (`infrastructure/event_store/`)
**Purpose**: Persist and retrieve domain events

**Responsibilities**:
- Store events atomically
- Retrieve events by aggregate ID
- Support event versioning
- Handle concurrency control
- Support time-based queries
- Provide event validation metadata

**Implementation**:
```python
class PostgreSQLEventStore:
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    async def save_event(self, event: DomainEvent) -> None:
        """Save event with validation metadata"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO events (
                    event_id, aggregate_id, aggregate_type, event_type,
                    timestamp, version, data, metadata, validation_info
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, (
                event.event_id, event.aggregate_id, event.aggregate_type,
                event.event_type, event.timestamp, event.version,
                json.dumps(event.data), json.dumps(event.metadata),
                json.dumps(event.validation_info or {})
            ))
    
    async def get_events(self, aggregate_id: str, aggregate_type: str, 
                        start_time: Optional[datetime] = None, 
                        end_time: Optional[datetime] = None) -> List[DomainEvent]:
        """Get events with optional time filtering"""
        query = """
            SELECT * FROM events 
            WHERE aggregate_id = $1 AND aggregate_type = $2
        """
        params = [aggregate_id, aggregate_type]
        
        if start_time:
            query += " AND timestamp >= $3"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= $4"
            params.append(end_time)
        
        query += " ORDER BY timestamp ASC"
        
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *params)
            return [DomainEvent(**row) for row in rows]
```

#### Read Model (`infrastructure/read_model/`)
**Purpose**: Optimized data for queries

**Responsibilities**:
- Store denormalized data
- Support complex queries
- Handle eventual consistency
- Provide search capabilities
- Support pagination and filtering

**Implementation**:
```python
class PostgreSQLReadModel:
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    async def save_client(self, client: ClientReadModel) -> None:
        """Save client to read model"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO clients (
                    id, name, parent_id, status, created_at, updated_at,
                    business_types, currency, billing_country, priority,
                    sso_id, sso_id_c, sso_id_r, description, is_deleted
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    parent_id = EXCLUDED.parent_id,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    business_types = EXCLUDED.business_types,
                    currency = EXCLUDED.currency,
                    billing_country = EXCLUDED.billing_country,
                    priority = EXCLUDED.priority,
                    sso_id = EXCLUDED.sso_id,
                    sso_id_c = EXCLUDED.sso_id_c,
                    sso_id_r = EXCLUDED.sso_id_r,
                    description = EXCLUDED.description,
                    is_deleted = EXCLUDED.is_deleted
            """, (
                client.id, client.name, client.parent_id, client.status,
                client.created_at, client.updated_at, client.business_types,
                client.currency, client.billing_country, client.priority,
                client.sso_id, client.sso_id_c, client.sso_id_r,
                client.description, client.is_deleted
            ))
    
    async def search_clients(self, query: SearchClientsQuery) -> List[ClientDTO]:
        """Search clients with filtering and pagination"""
        sql_query = "SELECT * FROM clients WHERE 1=1"
        params = []
        param_count = 1
        
        if query.search_term:
            sql_query += f" AND (name ILIKE ${param_count} OR description ILIKE ${param_count})"
            params.append(f"%{query.search_term}%")
            param_count += 1
        
        if query.status:
            sql_query += f" AND status = ${param_count}"
            params.append(query.status)
            param_count += 1
        
        # Add pagination
        offset = (query.page - 1) * query.page_size
        sql_query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([query.page_size, offset])
        
        async with self.get_connection() as conn:
            rows = await conn.fetch(sql_query, *params)
            return [ClientDTO(**row) for row in rows]
```

#### Messaging (`infrastructure/messaging/`)
**Purpose**: Handle external messaging and broadcasting

**Components**:
- **Abstract Event Publisher**: Interface for publishing events
- **SNS Publisher**: SNS implementation
- **EventBridge Publisher**: EventBridge implementation
- **Local Publisher**: For testing/development

**Publisher Interface**:
```python
class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: NormalizedEntityEvent) -> None:
        pass

class EventBridgePublisher(EventPublisher):
    async def publish(self, event: NormalizedEntityEvent) -> None:
        """Publish normalized entity to EventBridge"""
        try:
            eventbridge_client = boto3.client('events')
            response = await eventbridge_client.put_events(
                Entries=[{
                    'Source': 'event-sourcing-system',
                    'DetailType': f'{event.aggregate_type}Changed',
                    'Detail': json.dumps(event.dict()),
                    'EventBusName': 'default'
                }]
            )
            logger.info(f"Published event to EventBridge: {event.event_id}")
        except Exception as e:
            logger.error(f"Failed to publish event to EventBridge: {e}")
            raise EventPublishException(f"Failed to publish event: {e}")
```

#### Repositories (`infrastructure/repositories/`)
**Purpose**: Abstract data access

**Repository Types**:
- `EventRepository` - Event storage and retrieval
- `ClientRepository` - Client aggregate persistence and read model access

**Repository Interface**:
```python
class EventRepository(ABC):
    @abstractmethod
    async def save_event(self, event: DomainEvent) -> None:
        pass
    
    @abstractmethod
    async def get_events(self, aggregate_id: str, aggregate_type: str, 
                        start_time: Optional[datetime] = None, 
                        end_time: Optional[datetime] = None) -> List[DomainEvent]:
        pass

class ClientRepository(ABC):
    @abstractmethod
    async def save_client(self, client: Client) -> None:
        pass
    
    @abstractmethod
    async def get_client(self, client_id: str) -> Optional[Client]:
        pass
    
    @abstractmethod
    async def search_clients(self, query: SearchClientsQuery) -> List[ClientDTO]:
        pass
```

### API Layer (`api/`)

#### Event Ingestion Endpoints (`api/routers/`)
**Purpose**: Receive events from Lambda and trigger processing

**Endpoints**:
- `POST /events/salesforce/` - Receive Salesforce CDC events
- `POST /events/backfill/{entity_type}/` - Trigger backfill operations (e.g., `/events/backfill/clients/`)
- `GET /events/backfill/{entity_type}/status/` - Get backfill status

**Flow**:
1. Receive event from Lambda
2. Validate event format
3. Trigger Celery task for processing
4. Return acknowledgment

#### Query Endpoints (`api/routers/`)
**Purpose**: Expose read operations

**Endpoints**:
- `GET /clients/{client_id}/` - Get client details
- `GET /clients/` - Search clients
- `GET /clients/{client_id}/history/` - Get client event history (with optional date query param)

**Characteristics**:
- Read-only operations
- Fast response times
- Caching support
- Pagination and filtering

## 🔄 Event Processing Pipeline

### 1. Raw Event Ingestion
```
Salesforce CDC Event → EventBridge → Lambda → API → Celery Task → Command Handler → Validation → Event Store
```

**Steps**:
1. **Salesforce** generates CDC event
2. **EventBridge** receives and routes event
3. **Lambda** processes event and calls API
4. **API endpoint** receives event from Lambda
5. **Celery task** triggered for async processing
6. **Command handler** orchestrates processing:
   - Parse and validate Salesforce CDC event
   - Validate event ordering and consistency
   - Handle backfill scenarios if needed
   - Store raw event in event store
   - Trigger aggregate reconstruction
7. Return success acknowledgment

### 2. Event Projection & Broadcasting
```
Event Store → Aggregate Reconstruction → Apply Mappings → Read Model Update → Event Publishing
```

**Steps**:
1. **Celery projection task** triggered by event persistence
2. **Load events** for affected aggregate from event store
3. **Reconstruct aggregate** by replaying events with mappings applied
4. **Apply field mappings** to transform raw Salesforce data to domain model
5. **Update read model** (PostgreSQL) with normalized data
6. **Publish normalized entity** via event publisher to downstream consumers
7. **Log completion** for monitoring

### 3. Query Processing
```
API Request → Query Handler → Read Model → Response
```

**Steps**:
1. Receive API request
2. Create appropriate query object
3. Execute query against read model
4. Transform results to DTOs
5. Return response

### 4. Backfill Processing
```
Salesforce API → Batch Processing → Creation Commands → Command Processing Pipeline
```

**Steps**:
1. **Backfill triggered** for entity type
2. **Salesforce API** queried with pagination
3. **Batch processing** handles rate limiting and pagination
4. **Creation commands** generated for each historical entity
5. **Command processing pipeline** processes each creation command
6. **Event validation** ensures proper ordering
7. **Aggregate reconstruction** builds current state from events

## 📊 Data Models

### Domain Events
```python
class ClientCreatedEvent(DomainEvent):
    event_type: str = "Created"
    aggregate_type: str = "client"
    data: Dict[str, Any]  # Contains client creation data

class ClientUpdatedEvent(DomainEvent):
    event_type: str = "Updated"
    aggregate_type: str = "client"
    data: Dict[str, Any]  # Contains client update data

class ClientDeletedEvent(DomainEvent):
    event_type: str = "Deleted"
    aggregate_type: str = "client"
    data: Dict[str, Any]  # Contains client deletion data

class ClientBackfillTriggeredEvent(DomainEvent):
    event_type: str = "BackfillTriggered"
    aggregate_type: str = "client"
    data: Dict[str, Any]  # Contains backfill trigger data
```

### Commands
```python
class ProcessSalesforceEventCommand(Command):
    command_type: str = "ProcessSalesforceEvent"
    data: ProcessSalesforceEventCommandData

class ProcessSalesforceEventCommandData(BaseModel):
    raw_event: dict  # Raw Salesforce CDC event
    entity_name: str
    change_type: str

class BackfillEntityTypeCommand(Command):
    command_type: str = "BackfillEntityType"
    data: BackfillEntityTypeCommandData

class BackfillEntityTypeCommandData(BaseModel):
    entity_name: str
    page: int = 1
    page_size: int = 50
```

### Queries
```python
class GetClientQuery(Query):
    client_id: str

class SearchClientsQuery(Query):
    search_term: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20

class GetClientHistoryQuery(Query):
    client_id: str
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

class GetBackfillStatusQuery(Query):
    entity_type: str
```

### Read Model Documents
```python
class ClientReadModel(BaseModel):
    id: str
    name: str
    parent_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    business_types: Optional[List[str]]
    currency: Optional[str]
    billing_country: Optional[str]
    priority: Optional[str]
    sso_id: Optional[str]
    sso_id_c: Optional[str]
    sso_id_r: Optional[str]
    description: Optional[str]
    is_deleted: bool
```

### Normalized Entity (Event Publishing)
```python
class NormalizedEntityEvent(BaseModel):
    event_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]  # Normalized entity data
    version: str
    validation_info: Optional[Dict[str, Any]] = None
```

## 🧪 Testing Strategy

### Unit Tests
- **Aggregate Tests**: Test business logic in isolation
- **Command Handler Tests**: Test command orchestration
- **Query Handler Tests**: Test query execution
- **Mapper Tests**: Test data transformations
- **Mapping Tests**: Test field mappings
- **Validation Tests**: Test event validation logic
- **Backfill Tests**: Test backfill processing

### Integration Tests
- **Event Store Tests**: Test event persistence and retrieval
- **Read Model Tests**: Test projection and querying
- **Event Publisher Tests**: Test publishing functionality
- **Backfill Integration Tests**: Test historical data ingestion
- **End-to-End Tests**: Test complete workflows

### Test Data
- **Event Fixtures**: Predefined events for testing
- **Aggregate Fixtures**: Predefined aggregate states
- **Command Fixtures**: Predefined commands for testing
- **Mapping Fixtures**: Test data for field mappings
- **Validation Fixtures**: Test scenarios for event validation
- **Backfill Fixtures**: Test data for historical processing

## 🔧 Implementation Phases

### Phase 1: Foundation
1. Set up domain layer structure
2. Implement basic Client aggregate
3. Create generic domain events
4. Set up PostgreSQL event store infrastructure
5. Implement simplified field mappings

### Phase 2: Commands & Handlers
1. Implement command objects
2. Create command handlers
3. Set up command processing pipeline
4. Add validation and error handling
5. Implement aggregate reconstruction with mappings

### Phase 3: Queries & Read Model
1. Implement query objects
2. Create query handlers
3. Set up PostgreSQL read model
4. Implement projection logic
5. Add mapping application in projection

### Phase 4: API & Integration
1. Create FastAPI endpoints for event ingestion
2. Implement Celery tasks
3. Add event publisher integration
4. Set up monitoring and logging
5. Implement Lambda integration

### Phase 5: Migration & Optimization
1. Migrate existing data
2. Optimize performance
3. Add caching
4. Implement advanced features
5. Fine-tune mappings and projections

### Phase 6: Advanced Features
1. Event validation and ordering
2. Historical data backfill
3. Complex field mapping patterns
4. Production monitoring and alerting
5. Performance optimization

## 🎯 Benefits of This Architecture

### 1. **Auditability**
- Complete event history
- Immutable event log
- Full audit trail
- Replay capability
- Historical data backfill support

### 2. **Flexibility**
- Business rules can evolve
- Schema changes without migration
- New projections can be added
- Historical data analysis
- Field mappings can be updated

### 3. **Scalability**
- Read/write separation
- Independent scaling
- Event-driven processing
- Async operations
- Decoupled event publishing
- Batch processing for backfill

### 4. **Testability**
- Business logic isolated
- Easy to test aggregates
- Mock external dependencies
- Clear boundaries
- Mappings can be tested independently
- Validation logic can be tested in isolation

### 5. **Maintainability**
- Clear separation of concerns
- Domain-driven design
- Explicit patterns
- Reduced coupling
- Centralized mappings
- Comprehensive validation

### 6. **Production Ready**
- Event validation ensures data consistency
- Backfill support for historical data
- Error handling and retry mechanisms
- Monitoring and alerting
- Graceful degradation
- Data integrity checks

## 🚨 Considerations & Trade-offs

### Complexity
- **Higher initial complexity** compared to layered architecture
- **Learning curve** for team members
- **More moving parts** to manage
- **Mapping complexity** needs careful design
- **Validation complexity** requires thorough testing

### Performance
- **Event replay** can be expensive for large aggregates
- **Eventual consistency** in read model
- **Storage overhead** for event history
- **Mapping overhead** during reconstruction
- **Backfill processing** can be resource-intensive

### Operational
- **Event store management** requires careful planning
- **Projection failures** need handling
- **Debugging** can be more complex
- **Event publishing** adds operational overhead
- **Backfill monitoring** requires additional tooling

### Migration
- **Data migration** from existing system
- **Gradual transition** strategy needed
- **Backward compatibility** during transition
- **Mapping migration** strategy required
- **Validation migration** needs careful planning

## 📈 Evolution Path

### From Current State (Option 4)
1. **Extract domain logic** from service layer
2. **Create aggregates** for business entities
3. **Introduce commands** for write operations
4. **Separate queries** for read operations
5. **Implement event sourcing** gradually
6. **Centralize mappings** in domain layer
7. **Add validation logic** to aggregates
8. **Implement backfill capabilities**

### Migration Strategy
1. **Parallel implementation** of new architecture
2. **Gradual migration** of entities
3. **Feature flags** for new vs old code
4. **Data synchronization** during transition
5. **Complete switch** once stable
6. **Mapping migration** with backward compatibility
7. **Validation migration** with comprehensive testing

### Future Infrastructure Evolution
1. **Event Store**: PostgreSQL → DynamoDB (if needed)
2. **Read Model**: PostgreSQL → Elasticsearch (for search capabilities)
3. **Event Publishing**: SNS → EventBridge → Kafka (as scale demands)
4. **Validation**: Simple validation → Complex business rule validation
5. **Backfill**: Basic backfill → Advanced backfill with progress tracking

This architecture provides a solid foundation for building scalable, maintainable, and auditable systems while leveraging the power of event sourcing and CQRS patterns, with proper handling of field mappings, event validation, backfill capabilities, and normalized entity broadcasting in a domain-driven design approach. 