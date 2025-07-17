# Speaker Notes: Event Sourcing & CQRS with FastAPI and Celery

## Section 1: What We'll Discuss

### Slide 1: Title Slide (30 seconds)
**Key Points:**
- Welcome everyone to PyCon Athens
- Mention this is about a mindset shift in how we think about data
- The title is a play on "Dr. Strangelove" - events can be scary but powerful
- Set expectation: 30 minutes, lots of code examples, interactive

**Speaking Notes:**
"Good morning everyone! I'm excited to be here at PyCon Athens. Today we're going to talk about something that might sound scary at first - raw events. But by the end of this talk, I hope you'll see why I've learned to love them. This is about a fundamental shift in how we think about data in our systems."

---

### Slide 2: What We'll Discuss (30 seconds)
**Key Points:**
- Introduce the structure and what will be covered
- Set expectations for the talk

**Speaking Notes:**
"Today we'll cover three main areas. First, the core principles of event sourcing and CQRS - how to store every change as an immutable event and separate read and write concerns. Second, how the Python ecosystem offers excellent solutions for this - FastAPI for APIs, Celery for async processing, and Pydantic for data validation. Finally, we'll look at the aftermath - real-world patterns, performance considerations, and how to debug and test in an immutable world."

---

### Slide 3: Who Am I? (45 seconds)
**Key Points:**
- Establish credibility as a staff engineer
- Show academic background with a joke
- Position as someone passionate about building systems with quality
- Keep it concise

**Speaking Notes:**
"I'm a staff engineer who's been working with Python for over a decade. I studied Physics, then Computational Physics, and then made the switch to software engineering. I went from calculating planet trajectories to debugging production systems - turns out, both involve a lot of uncertainty! I'm passionate about building systems with quality."

---

### Slide 4: Traditional Approach (1 minute)
**Key Points:**
- Show the problems with current state storage
- Highlight the issues with traditional approach
- Set up the motivation for event sourcing

**Speaking Notes:**
"Let's start with what we're used to - the traditional approach. We store the current state, we get a user, mutate their state, and save it back, overwriting history. This approach has several problems: history is lost - we only see current state, no audit trail - we can't answer who changed what when, mutable state creates data corruption risks, and tight coupling between read and write operations."

---

### Slide 5: Event Sourcing Approach (1 minute)
**Key Points:**
- Show the solution with immutable events
- Demonstrate the fundamental shift
- Highlight the benefits

**Speaking Notes:**
"Event sourcing is a fundamental shift. Instead of storing current state, we store what actually happened - immutable events. Here we have a UserCreated event with an event_id, aggregate_id, timestamp, event_type, and the actual data of what changed. This gives us complete history - every change is recorded, audit trail - we can see exactly what happened, immutable events ensure data integrity, and time travel - we can replay any point in history."

---

### Slide 6: Pain Points of Traditional Architectures (45 seconds)
**Key Points:**
- Show familiar problems that everyone recognizes
- Connect to real pain points developers face
- Set up the motivation for event sourcing

**Speaking Notes:**
"This is what we're used to with traditional architectures. Tight coupling between read and write - you can't scale them independently. Poor auditability - you can't answer 'who changed what when?' Mutable state - data corruption risks. And scaling challenges - read/write conflicts. The result is systems that can't explain themselves."

---

### Slide 7: Why Event Sourcing? (45 seconds)
**Key Points:**
- Highlight the superpowers this gives you
- Connect to real debugging scenarios
- Show business value
- Build excitement

**Speaking Notes:**
"When you store every change, you get these superpowers. Complete audit trail - every action is recorded. Time travel - you can replay any point in history. Debugging superpowers - you can see exactly what happened when something goes wrong. Data integrity - no more lost changes. And scalability - you can separate read and write concerns."

---

### Slide 8: Quick Teaser: Audited-by-Design System (45 seconds)
**Key Points:**
- Show what the end result looks like
- Demonstrate the power of events
- Build excitement for the solution

**Speaking Notes:**
"Here's what an audited-by-design system looks like. Every action is an event - UserCreated, UserNameChanged, UserEmailChanged. This gives us complete history - nothing is ever lost. We can do temporal queries - what was the state at 3pm? We can replay events to rebuild state from scratch. And we have audit by design - every change is recorded."

---

## Section 2: Core Concepts

### Slide 9: Section Overview (15 seconds)
**Key Points:**
- Introduce the core concepts section
- Set expectations

**Speaking Notes:**
"Now let's dive into the core concepts. I'll explain events as the building blocks, show you how aggregates work, introduce the event store, talk about projections, show the event bus, and explain CQRS with separate databases."

---

### Slide 10: Events: The Building Blocks (1 minute)
**Key Points:**
- Show the Event structure
- Explain each field's purpose
- Emphasize immutability
- Connect to standard patterns

**Speaking Notes:**
"Events are the building blocks of our system. Here's the Event structure we use. Each event has an event_id - a unique identifier, an aggregate_id - which aggregate this belongs to, an event_type - what happened like UserCreated or UserUpdated, a timestamp - when it happened, a version - for event versioning, and data - the actual change data. The key principle is that events are immutable facts - they never change once created."

---

### Slide 11: Aggregates: Domain Models (1 minute)
**Key Points:**
- Show the UserAggregate structure
- Demonstrate the apply method pattern
- Show domain methods with validation
- Emphasize the core equation

**Speaking Notes:**
"Aggregates are where we model our business logic. Here's our UserAggregate. It has an apply method that updates aggregate state based on event type, and domain methods like create_user that validate business rules and return new events. The core equation is: State equals the result of applying all events. This is how we build current state from the event stream."

---

### Slide 12: Event Store: The Source of Truth (1 minute)
**Key Points:**
- Show the EventStore interface
- Emphasize append-only nature
- Show technology agnostic approach
- Demonstrate immutability

**Speaking Notes:**
"The event store is our source of truth. It's append-only - we never update or delete events. Here's the interface with save_event, get_events_by_aggregate, and get_events_by_type methods. The implementation can be PostgreSQL, EventStoreDB, DynamoDB, or any other technology. The key is that it's append-only, immutable, and replayable."

---

### Slide 13: Projections: Building Read Models (1 minute)
**Key Points:**
- Show the UserProjection structure
- Demonstrate event-to-read-model transformation
- Show the optimization principle
- Connect to CQRS

**Speaking Notes:**
"Projections are how we build read models from events. Here's our UserProjection. When a user_created event comes in, we transform it into read model data with aggregate_id, name, email, and created_at. We save this to a read-optimized database. The key principle is that read models are optimized for queries, not consistency. They're triggered from the event store and optimized for queries."

---

### Slide 14: Event Bus: Communication Layer (1 minute)
**Key Points:**
- Show the EventBus interface
- Demonstrate publish/subscribe pattern
- Show technology options
- Emphasize decoupling

**Speaking Notes:**
"The event bus is our communication layer. It has publish and subscribe methods. We can implement it with RabbitMQ, Kafka, EventBridge, SNS, or other messaging technologies. The key benefit is decoupled communication between components - systems can communicate without tight coupling."

---

### Slide 15: CQRS: Command Query Responsibility Segregation (1 minute)
**Key Points:**
- Explain the separation with different databases
- Show command vs query responsibilities
- Emphasize the database separation
- Connect to scalability benefits

**Speaking Notes:**
"CQRS stands for Command Query Responsibility Segregation. We separate our write model - command handlers process commands and call aggregates, aggregates apply business logic and create events, event store persists events, and event bus publishes events - from our read model - query handlers process queries and return data, read models are optimized for fast reads, data is denormalized for performance, and we use a separate database. The key insight is that we use different databases for different purposes."

---

### Slide 16: CQRS Benefits (30 seconds)
**Key Points:**
- Reinforce the benefits
- Address common misconceptions
- Keep it practical

**Speaking Notes:**
"This separation gives us real benefits. Auditability - commands emit events, queries are optimized. Modularity - different models for different concerns. Scalability - read/write workloads differ. Technology flexibility - different DBs for different needs. And here's the key point: you don't need Kafka to start with CQRS. You can start simple with what you have."

---

## Section 3: Architecture Walkthrough

### Slide 17: Section Overview (15 seconds)
**Key Points:**
- Introduce the architecture section
- Set expectations for the deep dive

**Speaking Notes:**
"Now let's walk through the architecture. I'll show you the high-level flow, how the entities work together, and how the Python ecosystem implements these concepts."

---

### Slide 18: High-Level Architecture Flow (1 minute)
**Key Points:**
- Show the conceptual flow
- Introduce key components
- Keep it technology agnostic
- Set up for Python implementation

**Speaking Notes:**
"Here's how the entities work together. External request comes in, becomes a command, calls the aggregate, creates an event, stores it in the event store, publishes to event bus, triggers projections, and updates the read model. The core flow is: command, aggregate, event, event store, event bus, projections, read model."

---

### Slide 19: Python Ecosystem Solutions (1 minute)
**Key Points:**
- Show how Python tools implement the concepts
- Introduce FastAPI, Celery, and other tools
- Keep it practical

**Speaking Notes:**
"Here's how we implement this in Python. External request goes to FastAPI, which calls command handlers, which work with aggregates, create events, store them in event stores like PostgreSQL or EventStoreDB, publish to event buses like RabbitMQ or Kafka, trigger projections via Celery workers, and update read models. The Python ecosystem provides excellent tools for this architecture."

---

### Slide 20: FastAPI: The Command Interface (2 minutes)
**Key Points:**
- Show real FastAPI code
- Emphasize Pydantic validation
- Show immediate response pattern
- Keep it practical

**Speaking Notes:**
"Here's how we implement this with FastAPI. We define our endpoints to accept user data. We create commands using Pydantic models for validation. When a request comes in, we create a CreateUserCommand, get the appropriate handler from our infrastructure factory, and process the command. Notice we return immediately - we don't wait for the event to be processed. This gives us high availability and responsiveness."

---

### Slide 21: Command Handlers: Business Logic (2 minutes)
**Key Points:**
- Show the CreateUserCommandHandler
- Emphasize the handle method pattern
- Show aggregate creation and event application
- Demonstrate clean separation

**Speaking Notes:**
"Command handlers are where the business logic lives. Here's our CreateUserCommandHandler. It takes an event store and event bus in its constructor. The handle method is the key - it creates an aggregate, calls the domain method to validate and create an event, applies the event to the aggregate, stores it in the event store, and publishes it to the event bus. This gives us clean separation between business logic and infrastructure concerns."

---

### Slide 22: Celery: Async Task Runner & Scalable Workers (2 minutes)
**Key Points:**
- Show the Celery task
- Emphasize async processing
- Show the async_to_sync pattern
- Demonstrate flexibility

**Speaking Notes:**
"Celery is our async task runner and scalable workers. Here's how we implement it. We define a Celery task that takes event data. We use async_to_sync to convert our async function to sync for Celery. The async function creates an Event, gets the event handler, and processes it. Each task is independent and can be scaled separately. This gives us tremendous flexibility for processing different types of events."

---

### Slide 23: Projections: Event-Driven Read Models (2 minutes)
**Key Points:**
- Show the UserProjection
- Demonstrate event-to-read-model transformation
- Show the broadcast pattern
- Emphasize the event-driven nature

**Speaking Notes:**
"Projections are how we build read models from events. Here's our UserProjection. When a user_created event comes in, we build user data with aggregate_id, name, email, and created_at. We save this to the read model. And we broadcast the event to EventBridge for other systems. This gives us event-driven read model updates."

---

### Slide 24: FastAPI: Query Interface (2 minutes)
**Key Points:**
- Show the FastAPI query endpoints
- Demonstrate both current and historical queries
- Show the query handler pattern
- Emphasize the separation

**Speaking Notes:**
"Here's how we expose read models through FastAPI. We have endpoints for getting current user data and user history. For current data, we create a GetUserQuery, get the query handler from our infrastructure factory, and execute the query. For history, we create a GetUserHistoryQuery with optional date filters and get events from the event store. This gives us both current state and historical data through the same API."

---

### Slide 25: Design Flexibility: Services + Repositories (1 minute)
**Key Points:**
- Show service layer pattern
- Demonstrate separation of concerns
- Show dependency injection
- Keep it practical

**Speaking Notes:**
"Here's how we achieve design flexibility through services and repositories. On the command side, we have a service that handles business logic and coordinates between the event store and event bus. On the query side, we have a service that uses the read model. This gives us clean separation of concerns and makes testing much easier."

---

### Slide 26: Async + Decoupling for Scale (1 minute)
**Key Points:**
- Reinforce the benefits
- Show scalability advantages
- Keep it practical

**Speaking Notes:**
"This architecture gives us several benefits. High availability - commands return immediately. Independent scaling - read/write workloads differ. Resilience - failures don't cascade. Technology flexibility - different DBs for different needs. And eventual consistency - which is a feature, not a bug."

---

## Section 4: Real-World Patterns & Gotchas

### Slide 27: Section Overview (15 seconds)
**Key Points:**
- Introduce the real-world section
- Set expectations for practical advice

**Speaking Notes:**
"Now let's talk about real-world patterns and gotchas. I'll cover eventual consistency, snapshots for performance, fixes by reprocessing history, and debugging and testing in an immutable world."

---

### Slide 28: Eventual Consistency: Feature, Not Bug (1.5 minutes)
**Key Points:**
- Address the consistency concern
- Show why it's beneficial
- Give concrete examples
- Build confidence

**Speaking Notes:**
"Eventual consistency scares a lot of people, but it's actually a feature. On the command side, we return immediately - high availability. On the query side, we might not have the latest changes yet - but that's okay. This gives us high availability, scalability, and resilience. Failures don't cascade through the system."

---

### Slide 29: Snapshots for Performance on Replay (1.5 minutes)
**Key Points:**
- Address the performance concern
- Show the snapshot pattern
- Demonstrate the improvement
- Keep it practical

**Speaking Notes:**
"One concern with event sourcing is performance - what if you have thousands of events? That's where snapshots come in. We periodically save the state of our aggregates. When we need to build state, we start from the latest snapshot and only replay events after that. This gives us the best of both worlds - performance and auditability."

---

### Slide 30: Fixes by Reprocessing History (1 minute)
**Key Points:**
- Show safe data fixes
- Contrast with traditional approach
- Emphasize safety
- Show automation

**Speaking Notes:**
"Instead of scary manual data patches, we emit correction events. This is much safer - we're not directly manipulating data. All our projections will be updated automatically. We maintain our audit trail. And we can replay the fix if needed."

---

### Slide 31: Debugging in an Immutable World (1 minute)
**Key Points:**
- Show debugging superpowers
- Give concrete examples
- Emphasize the value
- Connect to real scenarios

**Speaking Notes:**
"This is where event sourcing really shines - debugging. We can see exactly what happened by replaying events. We can compare states at different times. We can answer questions like 'what was the user's state at 3pm?' This is incredibly powerful for debugging production issues."

---

### Slide 32: Testing in an Immutable World (1 minute)
**Key Points:**
- Show testing strategies
- Emphasize simplicity
- Show confidence
- Keep it practical

**Speaking Notes:**
"Testing event-sourced systems is actually quite straightforward. Test your aggregates by applying events. Test your event store by appending and retrieving events. The immutability makes testing much more predictable."

---

### Slide 33: Thank You (30 seconds)
**Key Points:**
- Thank the audience
- Invite questions
- End warmly

**Speaking Notes:**
"Thank you all for your attention. I hope I've convinced you that raw events are worth loving. I'm happy to take questions. Let's have a great discussion!"

---

## Overall Presentation Flow:

**Timing Breakdown:**
- Section 1: What We'll Discuss (Slides 1-8): 4 minutes
- Section 2: Core Concepts (Slides 9-16): 6 minutes
- Section 3: Architecture Walkthrough (Slides 17-26): 12 minutes
- Section 4: Real-World Patterns (Slides 27-32): 6 minutes
- Thank You (Slide 33): 30 seconds

**Key Speaking Tips:**
- Use the code examples to anchor concepts
- Emphasize the Python ecosystem's readiness
- Address concerns proactively (performance, complexity, etc.)
- Keep it practical and actionable
- Use humor and real-world examples
- Encourage questions throughout
- Connect to audience's existing Python experience

**Interactive Elements:**
- Ask "Who here has debugged a production issue and wished they could see exactly what happened?"
- Ask "Who here has had to manually fix data in production?"
- Ask "Who here has struggled with scaling read vs write workloads?"
- Use these to connect with audience pain points

**Section Transitions:**
- Each section starts with an overview slide
- Clear transitions between sections
- Consistent timing throughout
- Build complexity gradually

**Code Examples Strategy:**
- Use actual code to show real implementation
- Explain the patterns (Events, Aggregates, Command Handlers, Projections, etc.)
- Show how Python features (Pydantic, async/await, Celery) enable this architecture
- Demonstrate the separation of concerns and clean design
