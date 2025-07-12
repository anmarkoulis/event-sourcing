# DDD + CQRS Implementation Improvements

This document outlines the improvements needed to achieve a proper Domain-Driven Design (DDD) and Command Query Responsibility Segregation (CQRS) architecture.

## Current Architecture

### API Endpoints
- `POST /events/salesforce/` - Process Salesforce events from AWS EventBridge
  - Accepts `SalesforceEventDTO` (AWS EventBridge format)
  - Maps to `EventWriteDTO` internally
  - Returns `EventReadDTO` with processing information
  - Triggers async Celery processing

### DTOs
- `EventWriteDTO` - Generic event write DTO with validation
- `EventReadDTO` - Extends EventWriteDTO with processed_at field
- `SalesforceEventDTO` - AWS EventBridge Salesforce event format
- `SalesforcePayload` - Salesforce-specific payload structure
- `SalesforceChangeEventHeader` - Salesforce change event metadata

### Event Processing Flow
1. AWS EventBridge sends Salesforce event to `/events/salesforce`
2. `SalesforceEventDTO` validates the AWS EventBridge format
3. DTO maps to `EventWriteDTO` with Salesforce-specific logic
4. `AsyncProcessCRMEventCommand` triggers Celery task
5. Event is processed asynchronously and stored in event store
6. `EventReadDTO` is returned with processing information

## 2. Aggregate Design Issues (Critical Priority)

### Current Issues
- Aggregates have provider-specific methods
- Business logic mixed with event processing
- Inconsistent aggregate behavior
- Fallback logic that doesn't make sense

### Specific Problems
1. **`process_crm_event()` method** in aggregates is provider-specific
2. **Aggregates should only consume events** not process them
3. **Fallback logic** `events = [domain_event]` is meaningless
4. **Aggregates should be pure** - no external dependencies
5. **Event processing logic** should be in application layer

### Improvements Needed
- **Remove `process_crm_event()`** from aggregates
- **Aggregates should only apply events** to state
- **Move event processing logic** to application services
- **Make aggregates pure** domain objects
- **Use event replay** for aggregate reconstruction

### Example Refactored Aggregate
```python
class ClientAggregate:
    def apply(self, event: DomainEvent) -> None:
        """Only method needed - apply events to state"""
        if event.event_type == "Created":
            self._apply_created_event(event)
        elif event.event_type == "Updated":
            self._apply_updated_event(event)
        elif event.event_type == "Deleted":
            self._apply_deleted_event(event)

    # Remove process_crm_event() - this should be in application service
```

## 3. Projection Management Issues (High Priority)

### Current Issues
- Projection manager tied to specific read models
- Optional typing with Any
- No generic projection support
- Celery dependencies in projection logic

### Specific Problems
1. **`projection_manager: Optional[Any] = None`** - poor typing
2. **ProjectionManager tied to Client** read model only
3. **No generic projection support** for multiple aggregates
4. **Celery dependencies** in projection logic
5. **Projections only triggered by PostgreSQL** event store

### Improvements Needed
- **Create generic ProjectionManagerInterface**
- **Implement proper typing** for projection managers
- **Support multiple aggregate types** in projections
- **Abstract Celery from projection logic**
- **Make projections work with any event store**

### Example Projection Manager Structure
```python
class ProjectionManagerInterface(ABC):
    @abstractmethod
    async def handle_event(self, event: DomainEvent) -> None:
        pass

class GenericProjectionManager(ProjectionManagerInterface):
    def __init__(self, event_handler: EventHandlerInterface):
        self.event_handler = event_handler

    async def handle_event(self, event: DomainEvent) -> None:
        # Generic projection logic that works with any aggregate
        projection_event = self._create_projection_event(event)
        await self.event_handler.dispatch(projection_event)
```

## 4. Domain Services (High Priority)

### Current Issues
- Complex business logic scattered across aggregates
- External API calls in aggregates
- Missing domain services for complex business rules
- Business logic scattered across aggregates and command handlers

### Specific Problems
1. **Missing CREATE event handling** is duplicated in both aggregate and command handler
2. **Broadcasting logic** is embedded in aggregate but should be domain service
3. **Event sequence validation** is mixed with business rules
4. **External API calls** (Salesforce client) are in aggregate
5. **Provider-specific logic** mixed with pure domain logic

### Improvements Needed
- **Create domain services** for complex business logic
- **Extract CRM API interactions** to domain services
- **Implement business rule engines**
- **Separate cross-aggregate logic**
- **Remove infrastructure concerns from aggregates**

### Example Domain Services
```python
class ClientDomainService:
    def handle_missing_create_event(self, aggregate_id: str, complete_state: dict) -> List[DomainEvent]
    def validate_client_status(self, client_data: dict) -> bool
    def determine_event_type(self, existing_client, new_data) -> EventType
    def should_broadcast_event(self, event: DomainEvent, client_state: dict) -> bool
    def validate_event_sequence(self, event: DomainEvent, existing_events: List[DomainEvent]) -> bool
    def process_crm_event(self, event: DomainEvent, aggregate: ClientAggregate) -> List[DomainEvent]
```

### Implementation Strategy
```python
# Move complex logic to domain service
class ClientDomainService:
    def __init__(self, provider_factory: CRMProviderFactory):
        self.provider_factory = provider_factory

    async def handle_missing_create_event(self, aggregate_id: str, provider: str, config: dict) -> List[DomainEvent]:
        """Handle missing CREATE event by fetching complete state"""
        provider_instance = self.provider_factory.create_provider(provider, config)
        complete_state = await provider_instance.get_entity(aggregate_id, "client")

        if not complete_state:
            raise ValueError(f"Entity not found: {aggregate_id}")

        return [self._create_missing_create_event(complete_state, aggregate_id)]

    def should_broadcast_event(self, event: DomainEvent, client_state: dict) -> bool:
        """Business logic: Determine if event should be broadcasted"""
        status = event.data.get("status")
        if status and status.lower() in ["inactive", "pending", "draft"]:
            return False
        return True

    def validate_event_sequence(self, event: DomainEvent, existing_events: List[DomainEvent]) -> bool:
        """Business logic: Validate event ordering"""
        if event.event_type == "Created" and existing_events:
            return False
        return True
```

## 5. Command Validation (High Priority)

### Current Issues
- Validation logic mixed with command handling
- No clear validation pipeline
- Missing business rule validation
- No cross-command validation

### Specific Problems
1. **No command validation** - commands are processed without validation
2. **Business rules validation** happens in aggregate instead of before processing
3. **No schema validation** for incoming events
4. **No cross-command validation** (e.g., check if client exists before update)
5. **Validation errors** are not properly handled

### Improvements Needed
- **Implement command validation pipeline**
- Create validation decorators or middleware
- Separate business validation from technical validation
- Implement cross-command validation
- Add comprehensive error handling for validation failures

### Example Validation Structure
```python
class CommandValidator:
    def validate(self, command: Command) -> ValidationResult:
        # Validate command structure and business rules
        pass

class ValidationMiddleware:
    def process(self, command: Command, handler: CommandHandler):
        # Apply validation before command execution
        pass

class BusinessRuleValidator:
    def validate_client_exists(self, client_id: str) -> bool
    def validate_event_ordering(self, event: DomainEvent) -> bool
    def validate_data_consistency(self, event: DomainEvent) -> bool
    def validate_provider_support(self, provider: str) -> bool
```

### Implementation Strategy
```python
class ProcessCRMEventValidator:
    def validate(self, command: ProcessCRMEventCommand) -> ValidationResult:
        result = ValidationResult()

        # Technical validation
        if not command.raw_event:
            result.add_error("Raw event is required")

        if not command.provider:
            result.add_error("Provider is required")

        # Business validation
        if not self._validate_provider_support(command.provider):
            result.add_error(f"Provider {command.provider} not supported")

        # Schema validation
        if not self._validate_event_schema(command.raw_event):
            result.add_error("Invalid event schema")

        return result

    def _validate_provider_support(self, provider: str) -> bool:
        return provider in ["salesforce", "hubspot", "pipedrive"]

    def _validate_event_schema(self, raw_event: dict) -> bool:
        # Validate event structure
        required_fields = ["id", "event_type", "data"]
        return all(field in raw_event for field in required_fields)

class ValidationMiddleware:
    def __init__(self, validators: Dict[str, CommandValidator]):
        self.validators = validators

    async def process(self, command: Command, handler: CommandHandler):
        # Get appropriate validator
        validator = self.validators.get(command.__class__.__name__)
        if validator:
            result = validator.validate(command)
            if not result.is_valid:
                raise ValidationError(result.errors)

        # Proceed with command execution
        return await handler.handle(command)
```

## 6. Event Store Improvements (Medium Priority)

### Current Issues
- Basic event store implementation
- Limited event versioning and concurrency control
- No optimistic concurrency control
- Missing event metadata and correlation IDs

### Specific Problems
1. **No version tracking** - events don't have proper versioning
2. **No concurrency control** - multiple updates can conflict
3. **Missing correlation IDs** - can't trace event chains
4. **No event replay capabilities** - limited aggregate reconstruction
5. **Basic error handling** - no retry mechanisms

### Improvements Needed
- **Implement optimistic concurrency control**
- Add event versioning and conflict resolution
- Implement event replay capabilities
- Add event metadata and correlation IDs
- Add comprehensive error handling and retry mechanisms

### Example Event Store Improvements
```python
class EventStore:
    async def save_event_with_version(self, event: DomainEvent, expected_version: int) -> None:
        # Implement optimistic concurrency control
        pass

    async def get_events_with_version(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        # Get events with version tracking
        pass

    async def add_correlation_id(self, event: DomainEvent, correlation_id: str) -> None:
        # Add correlation tracking
        pass

    async def save_events_with_retry(self, events: List[DomainEvent], max_retries: int = 3) -> None:
        # Implement retry mechanism
        pass
```

### Implementation Strategy
```python
class PostgreSQLEventStore(EventStore):
    async def save_event_with_version(self, event: DomainEvent, expected_version: int) -> None:
        """Save event with optimistic concurrency control"""
        async with AsyncDBContextManager(self.database_manager) as session:
            # Check current version
            current_version = await self._get_current_version(event.aggregate_id, session)

            if current_version != expected_version:
                raise ConcurrencyError(f"Version mismatch: expected {expected_version}, got {current_version}")

            # Save event with new version
            event.version = current_version + 1
            event_model = self._create_event_model(event)
            session.add(event_model)
            await session.commit()

    async def get_events_with_version(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """Get events with version tracking"""
        query = """
            SELECT * FROM events
            WHERE aggregate_id = $1 AND version > $2
            ORDER BY version
        """
        rows = await self.database_manager.fetch(query, aggregate_id, from_version)
        return [self._deserialize_event(row) for row in rows]

    async def add_correlation_id(self, event: DomainEvent, correlation_id: str) -> None:
        """Add correlation ID to event metadata"""
        if not event.metadata:
            event.metadata = {}
        event.metadata["correlation_id"] = correlation_id
```

## 7. Aggregate Purity Issues (High Priority)

### Current Issues
- Aggregates contain infrastructure concerns
- External API calls in aggregates
- Business logic mixed with technical concerns
- Provider-specific logic in domain aggregates

### Specific Problems in `ClientAggregate`:
1. **External API calls** in aggregates (should be in domain services)
2. **Provider-specific logic** mixed with pure domain logic
3. **Broadcasting decisions** are in aggregate but should be domain service
4. **Event transformation** logic is in aggregate
5. **External dependencies** in domain layer

### Improvements Needed
- **Remove infrastructure concerns from aggregates**
- **Move external API calls to domain services**
- **Extract provider-specific logic**
- **Keep aggregates pure and focused on business logic**
- **Separate technical concerns from domain logic**

### Example Refactoring
```python
# Before: Infrastructure concerns in aggregate
class ClientAggregate:
    def process_salesforce_event(self, salesforce_event: DomainEvent, salesforce_client: Any) -> List[DomainEvent]:
        # This calls external API - infrastructure concern!
        complete_state = salesforce_client.get_entity(self.aggregate_id, self.entity_name)
        # ... rest of logic

# After: Pure domain aggregate
class ClientAggregate:
    def process_crm_event(self, crm_event: DomainEvent) -> List[DomainEvent]:
        """Pure business logic only"""
        # Validate event sequence
        if not self._is_valid_event_sequence(crm_event):
            raise ValueError(f"Invalid event sequence: {crm_event.event_type}")

        # Apply business rules
        if not self._should_broadcast_event(crm_event):
            crm_event.metadata["broadcast"] = False
        else:
            crm_event.metadata["broadcast"] = True

        return [crm_event]

    def _is_valid_event_sequence(self, event: DomainEvent) -> bool:
        """Pure business logic: Validate event ordering"""
        if event.event_type == "Created" and self.events:
            return False
        return True

    def _should_broadcast_event(self, event: DomainEvent) -> bool:
        """Pure business logic: Determine if event should be broadcasted"""
        status = event.data.get("status")
        if status and status.lower() in ["inactive", "pending", "draft"]:
            return False
        return True
```

## 8. Command Handler Improvements (Medium Priority)

### Current Issues
- Command handlers contain too much business logic
- Missing validation pipeline
- No error handling strategy
- Complex orchestration logic

### Specific Problems in `ProcessCRMEventCommandHandler`:
1. **Missing CREATE event logic** is duplicated from aggregate
2. **No validation** before processing
3. **Complex orchestration** with multiple responsibilities
4. **No error handling** for provider failures
5. **Business logic** mixed with orchestration

### Improvements Needed
- **Simplify command handlers** to focus on orchestration
- **Add validation pipeline**
- **Implement comprehensive error handling**
- **Move business logic to domain services**
- **Add retry mechanisms for external calls**

### Example Refactored Command Handler
```python
class ProcessCRMEventCommandHandler:
    def __init__(
        self,
        event_store: EventStore,
        provider_factory: CRMProviderFactory,
        validator: ProcessCRMEventValidator,
        domain_service: ClientDomainService,
        error_handler: ErrorHandler
    ):
        self.event_store = event_store
        self.provider_factory = provider_factory
        self.validator = validator
        self.domain_service = domain_service
        self.error_handler = error_handler

    async def handle(self, command: ProcessCRMEventCommand) -> None:
        """Handle process CRM event command with proper validation and error handling"""
        try:
            # 1. Validate command
            validation_result = await self.validator.validate(command)
            if not validation_result.is_valid:
                raise ValidationError(validation_result.errors)

            # 2. Get provider and parse event
            provider = self.provider_factory.create_provider(command.provider, self.provider_config)
            parsed_event = await self._parse_event_with_retry(provider, command.raw_event)

            # 3. Transform to domain event
            domain_event = provider.translate_to_domain_event(parsed_event)

            # 4. Process through domain service (pure business logic)
            aggregate = await self._get_or_create_aggregate(domain_event.aggregate_id, domain_event.aggregate_type)
            events = await self.domain_service.process_crm_event(domain_event, aggregate, provider)

            # 5. Store events with retry
            await self._store_events_with_retry(events)

        except Exception as e:
            await self.error_handler.handle_error(e, command)
            raise

    async def _parse_event_with_retry(self, provider: Any, raw_event: dict) -> dict:
        """Parse event with retry mechanism"""
        for attempt in range(3):
            try:
                return provider.parse_event(raw_event)
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def _store_events_with_retry(self, events: List[DomainEvent]) -> None:
        """Store events with retry mechanism"""
        for event in events:
            await self.event_store.save_event_with_retry(event)
```

## 9. Event Processing Pipeline Issues (Medium Priority)

### Current Issues
- No clear validation pipeline
- Missing error handling
- Complex orchestration logic
- No retry mechanisms

### Improvements Needed
- **Implement clear event processing pipeline**
- **Add comprehensive error handling**
- **Implement retry mechanisms**
- **Simplify orchestration logic**
- **Add monitoring and observability**

### Example Event Processing Pipeline
```python
class EventProcessingPipeline:
    def __init__(self, validator, domain_service, event_store, error_handler):
        self.validator = validator
        self.domain_service = domain_service
        self.event_store = event_store
        self.error_handler = error_handler

    async def process_event(self, command: Command) -> None:
        try:
            # 1. Validate command
            await self.validator.validate(command)

            # 2. Process through domain service
            events = await self.domain_service.process_event(command)

            # 3. Store events with retry
            await self.event_store.save_events_with_retry(events)

        except Exception as e:
            await self.error_handler.handle_error(e, command)
            raise
```

## 10. Aggregate Identity Management

### Current Issues
- Aggregate IDs are set to the external Salesforce record ID
- No internal, stable aggregate identity
- Hard to support cross-provider or multi-source scenarios
- Risk of ID collisions or changes if external system changes

### Specific Problems
1. **Aggregate ID = Salesforce ID** — breaks aggregate isolation and internal consistency
2. **No UUIDs for aggregates** — not using best practice for unique, internal IDs
3. **No mapping layer** — can't relate external IDs to internal aggregates robustly
4. **Hard to migrate or merge** — if Salesforce changes, aggregates break
5. **No lookup logic** — can't find existing aggregate by external ID+source

### Improvements Needed
- **Generate internal UUIDs** for all aggregates
- **Maintain mapping** from (external_id, source) → aggregate_id
- **On event receipt:**
  - If (external_id, source) mapping exists, use mapped aggregate_id
  - Else, generate new UUID and create mapping
- **Never expose internal aggregate_id as external_id**
- **Support multiple sources/providers** for the same aggregate type

### Example Implementation
```python
class AggregateIdMapping(BaseModel):
    aggregate_id: UUID
    external_id: str
    source: str  # e.g. 'salesforce', 'hubspot'

# On event receipt:
def get_or_create_aggregate_id(external_id: str, source: str) -> UUID:
    mapping = mapping_store.get((external_id, source))
    if mapping:
        return mapping.aggregate_id
    new_id = uuid.uuid4()
    mapping_store[(external_id, source)] = AggregateIdMapping(
        aggregate_id=new_id, external_id=external_id, source=source
    )
    return new_id
```

## Implementation Priority

### Phase 1 (Critical - Do First)
- **Aggregate Design Issues** - Remove process_crm_event from aggregates

### Phase 2 (High Priority - Do Soon)
- **Projection Management Issues** - Create generic projection manager
- **Domain Services** - Extract complex business logic from aggregates
- **Command Validation** - Implement comprehensive validation pipeline
- **Aggregate Purity** - Remove infrastructure concerns from aggregates

### Phase 3 (Medium Priority - Do Later)
- **Event Store Improvements** - Add versioning and concurrency control
- **Command Handler Refactoring** - Simplify orchestration logic
- **Event Processing Pipeline** - Implement clear processing pipeline

### Phase 4 (Nice to Have)
- **Error Handling Strategy** - Comprehensive error handling
- **Testing Strategy** - Comprehensive test coverage

## Success Criteria

After implementing these improvements, the system should have:

- ✅ **Abstracted event dispatching** with Celery as implementation detail
- ✅ **Pure domain aggregates** that only apply events to state
- ✅ **Generic projection management** supporting multiple aggregate types
- ✅ **Domain services** for complex business logic
- ✅ **Comprehensive validation** pipeline
- ✅ **Clean command handlers** with proper separation of concerns
- ✅ **Testable business logic** in isolation
- ✅ **Proper error handling** and retry mechanisms
- ✅ **Clear event processing pipeline** with monitoring

## Notes

- Each improvement can be implemented incrementally
- Focus on one area at a time to avoid breaking changes
- Maintain backward compatibility during transitions
- Document architectural decisions and patterns
- Consider performance implications of each change
- Test thoroughly after each improvement
