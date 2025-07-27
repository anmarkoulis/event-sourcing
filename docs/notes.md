# Speaker Notes: Event Sourcing & CQRS with FastAPI and Celery

## Section 1: Opening Story (5 minutes)

### Slide 2: Who Am I?
**Key Points:**
- Start with warm greeting and gratitude
- Establish credibility as a staff engineer
- Show academic background with a joke
- Share the personal journey with events
- Connect to the movie title naturally
- Create a natural, engaging introduction

**Speaking Notes:**
"Hello everybody! I'm super excited to be presenting at PyCon Athens. This is the first one, so it's extra important to me. I'd like to thank the committee for having me here - it's truly an honor to be part of this inaugural event.

I'm a staff engineer who's been working with Python for over a decade. I studied Physics, then Computational Physics, and then made the switch to software engineering. I went from calculating planet trajectories to debugging production systems - turns out, both involve a lot of uncertainty!

My journey with events started with 'Events are too complex!' and ended with 'Events are the solution to complexity!' I'm passionate about building systems with quality.

Now, some of you might be wondering about this title. I just saw Stanley Kubrick's 'Dr. Strangelove' last year, and it inspired me. In our case, the bomb is complex distributed systems, the worrying is traditional debugging nightmares, and the love is embracing event sourcing's power. Today we're going to talk about something that might sound scary at first - raw events. But by the end of this talk, I hope you'll see why I've learned to love them."

---

### Slide 3: What We'll Discuss
**Key Points:**
- Introduce the structure and what will be covered
- Set expectations for the talk
- Transition from personal story to content overview

**Speaking Notes:**
"So, what are we going to cover today? We'll go through three main areas. First, the core principles of event sourcing and CQRS - how to store every change as an immutable event and separate read and write concerns. Second, how the Python ecosystem offers excellent solutions for this - FastAPI for APIs, Celery for async processing, and Pydantic for data validation. Finally, we'll look at the aftermath - real-world patterns, performance considerations, and how to debug and test in an immutable world."

---

### Slide 4: The Nightmare: "Who Deleted My User?"
**Key Points:**
- Tell a compelling debugging story
- Show the real pain of traditional systems
- Make it relatable to everyone in the audience
- Set up the motivation for event sourcing
- Transition from overview to concrete problem

**Speaking Notes:**
"Now, let me tell you a story that probably sounds familiar to many of you. Monday 3:47 PM - someone reports that Sarah's account is missing. Tuesday 9:15 AM - we're still trying to figure out when it was deleted, who did it, and why. With traditional systems, we can't answer any of these questions. The system has no memory of what happened. This is the nightmare we all face when debugging production issues."

---

### Slide 5: Enter Event Sourcing: The System That Remembers
**Key Points:**
- Show the solution with concrete examples
- Demonstrate the fundamental shift
- Highlight the immediate benefits
- Build excitement for the solution
- Transition from problem to solution

**Speaking Notes:**
"Event sourcing is the solution. Instead of deleting data forever, we record what happened as an immutable event. Now we can answer everything: when it was deleted, who did it, why, and even what the user's data was before deletion. Every action becomes a permanent record. This is the fundamental shift - from systems that forget to systems that remember."

---

## Section 2: Core Concepts (8 minutes)

### Slide 6: Core Concepts: Events
**Key Points:**
- Introduce events as immutable facts
- Show concrete event structure
- Emphasize immutability
- Connect to the debugging story
- Transition from solution to building blocks

**Speaking Notes:**
"Now that we've seen the problem and the solution, let's understand the building blocks. Let's start with the first one: Events. Every change in our system becomes an immutable event. Here's what a UserCreated event looks like - it has an event_id, aggregate_id, timestamp, event_type, and the actual data. The key principle is that events are immutable facts - they never change once created. This is what gives us the audit trail we need for debugging."

---

### Slide 7: Core Concepts: Event Streams
**Key Points:**
- Show how events belong to ordered sequences
- Demonstrate the concept of a user's complete story
- Emphasize the source of truth concept
- Connect to time travel capabilities
- Transition from individual events to sequences

**Speaking Notes:**
"Events aren't isolated - they belong to ordered sequences called event streams. Here's a user's complete story: UserCreated, UserNameChanged, UserEmailChanged, UserStatusChanged, and finally UserDeleted. The stream is the source of truth - we can rebuild any point in time by replaying these events in order. This is how we get time travel capabilities."

---

### Slide 8: Core Concepts: Commands
**Key Points:**
- Show commands as intent to change
- Demonstrate the command pattern
- Emphasize validation and idempotency
- Connect to CQRS separation
- Transition from events to commands

**Speaking Notes:**
"Now, how do we actually change the system? Commands represent the intent to change the system state. They express what we want to happen - like 'Create a new user account'. Commands can be validated before execution, are idempotent for safety, and serve as the entry point for all changes. This is the command side of CQRS."

---

### Slide 9: Core Concepts: Queries
**Key Points:**
- Show queries as intent to read
- Demonstrate the separation from commands
- Emphasize read optimization
- Connect to CQRS separation
- Transition from commands to queries

**Speaking Notes:**
"On the other hand, queries represent the intent to read data from the system. They're read-only, optimized for specific patterns, use separate models from commands, and are designed for fast retrieval. This is the query side of CQRS - completely separate from the command side."

---

### Slide 10: Core Concepts: Aggregates
**Key Points:**
- Show aggregates as domain logic containers
- Demonstrate business rule enforcement
- Emphasize state management and event creation
- Connect to consistency
- Transition from commands/queries to business logic

**Speaking Notes:**
"Now, where does the business logic live? Aggregates contain domain logic and apply business rules to create events. They enforce domain-specific validation like 'User email must be unique' and 'Cannot delete already deleted user'. When rules pass, they create events. When rules fail, they return errors. This ensures business invariants are maintained."

---

### Slide 11: Core Concepts: Event Store
**Key Points:**
- Show event store as source of truth
- Demonstrate append-only nature
- Emphasize immutability and stream management
- Connect to optimistic concurrency
- Transition from business logic to storage

**Speaking Notes:**
"Where do we store all these events? The Event Store is the append-only storage for all events in the system. Here's a user's event stream: UserCreated, EmailChanged, UserDeleted. Operations are simple: store new events, read in order, never modify. Events are immutable - once written, they're permanent. This gives us optimistic concurrency control."

---

### Slide 12: Core Concepts: Projections
**Key Points:**
- Show projections as read model builders
- Demonstrate event-driven updates
- Emphasize optimization and eventual consistency
- Connect to performance
- Transition from storage to read models

**Speaking Notes:**
"Finally, how do we build fast read models? Projections build optimized read models from events for fast querying. When a UserCreated event happens, we create a user record. When EmailChanged happens, we update the email field. This gives us event-driven read model updates that are optimized for queries and eventually consistent."

---

### Slide 13: How Everything Works Together
**Key Points:**
- Show end-to-end flow with the diagram
- Demonstrate how all components work together
- Make it concrete and understandable
- Set up for implementation section
- Transition from theory to implementation

**Speaking Notes:**
"Now that we understand all the building blocks, here's how everything connects in a real-world example. This diagram shows the complete flow from command to projection. Each interaction follows this pattern - from command to projection. This is the complete event sourcing and CQRS workflow in action."

---

## Section 3: Python Ecosystem Implementation (10 minutes)

### Slide 14: FastAPI: The Command Interface
**Key Points:**
- Show real FastAPI code
- Emphasize Pydantic validation
- Show immediate response pattern
- Keep it practical
- Transition from theory to Python implementation

**Speaking Notes:**
"Now let's see how the Python ecosystem implements this architecture. Here's how we implement this with FastAPI. We define our endpoints to accept user data. We create commands using Pydantic models for validation. When a request comes in, we create a CreateUserCommand, get the appropriate handler from our infrastructure factory, and process the command. Notice we return immediately - we don't wait for the event to be processed. This gives us high availability and responsiveness."

---

### Slide 15: Command Handlers: Business Logic
**Key Points:**
- Show the CreateUserCommandHandler
- Emphasize the handle method pattern
- Show aggregate creation and event application
- Demonstrate clean separation
- Transition from API to business logic implementation

**Speaking Notes:**
"Behind the API, command handlers are where the business logic lives. Here's our CreateUserCommandHandler with stream-based operations. The handle method loads the existing aggregate from the stream, reconstructs the state by applying all previous events, calls the domain method to validate and create an event, applies the event to the aggregate, appends to the stream with version checking for concurrency control, and publishes it to the event bus. This gives us clean separation between business logic and infrastructure concerns."

---

### Slide 16: Event Handler: Celery Integration
**Key Points:**
- Show the CeleryEventHandler
- Emphasize event type mapping
- Show dispatch mechanism
- Demonstrate message queue integration
- Transition from command processing to event handling

**Speaking Notes:**
"Once events are created, the Event Handler dispatches them to message queues. Here's our CeleryEventHandler that maps event types to Celery tasks. When a USER_CREATED event comes in, it triggers process_user_created_task and send_welcome_email_task. The dispatch method sends each task to Celery with the event data. This gives us scalable, async event processing."

---

### Slide 17: Celery Tasks: Event Processing
**Key Points:**
- Show the Celery task wrapper
- Emphasize async-to-sync conversion
- Show projection calling
- Demonstrate clean separation
- Transition from event dispatch to task processing

**Speaking Notes:**
"On the receiving end, Celery tasks are wrappers that call the appropriate projection handlers. Here's how it works: we define a Celery task that receives an event, convert our async function to sync for Celery using async_to_sync, and then call the projection. The task is just a wrapper - the actual business logic is in the projection handlers."

---

### Slide 18: Projections: Event-Driven Read Models
**Key Points:**
- Show the UserProjection
- Demonstrate event-to-read-model transformation
- Show the event-driven nature
- Emphasize the separation
- Transition from task processing to read model updates

**Speaking Notes:**
"Inside the Celery tasks, projections handle business logic and update read models from events. Here's our UserProjection. When a user_created event comes in, we build user data with aggregate_id, name, email, and created_at. We save this to the read model. This gives us event-driven read model updates that are optimized for queries."

---

### Slide 19: FastAPI: Query Interface
**Key Points:**
- Show the FastAPI query endpoints
- Demonstrate both current and historical queries
- Show the query handler pattern
- Emphasize the separation
- Transition from read model updates to query interface

**Speaking Notes:**
"Finally, FastAPI queries expose read models with dependency injection. Here's how we expose read models through FastAPI. We have endpoints for getting current user data and user history. For current data, we create a GetUserQuery, get the query handler from our infrastructure factory, and execute the query. For history, we create a GetUserHistoryQuery and get events from the event store. This gives us both current state and historical data through the same API."

---

### Slide 20: The Aftermath: Real-World Patterns & Gotchas
**Key Points:**
- Introduce the real-world section
- Set expectations for practical advice
- Acknowledge that this is where things get real
- Transition from implementation to real-world challenges

**Speaking Notes:**
"Now let's talk about what happens when you actually build this. This is where theory meets reality. We'll cover eventual consistency and how to handle the delay between write and read, error handling and retries with different strategies for commands vs projections, performance challenges with snapshots, and debugging superpowers. Let's talk about the real challenges."

---

### Slide 21: Eventual Consistency: The Real Challenge
**Key Points:**
- Show the real challenge with concrete example
- Present two different approaches
- Explain the naive vs advanced solutions
- Emphasize UI design importance
- Transition from implementation to real-world concerns

**Speaking Notes:**
"Now, let's talk about the real challenge of eventual consistency. Here's a concrete example: a user updates their first name. The API returns success immediately, but the read model might not be updated yet. This creates a real UI challenge. I've seen two approaches to handle this. The naive approach is optimistic updates - the frontend updates the UI immediately, but if the user refreshes, they might see old data. The more advanced approach is the outbox pattern - we store events in an outbox table with job status, track processing status like pending, processing, completed, or failed, and create views of unprocessed events. This gives us clear visibility into what's been processed versus what's still pending. Eventual consistency requires thoughtful UI design."

---

### Slide 22: Performance with Snapshots
**Key Points:**
- Address the performance concern
- Show the snapshot pattern with aggregate changes
- Demonstrate the improvement
- Keep it practical
- Transition from consistency to performance concerns

**Speaking Notes:**
"Another concern is performance - what if you have thousands of events? Here's the problem: replaying 10,000 events takes 5 seconds. The solution is snapshots, but this requires changes to our command handlers. We try to get the latest snapshot first, and if it exists, we rebuild the aggregate from the snapshot and apply only the recent events. If no snapshot exists, we fall back to getting all events - this handles the case where snapshots haven't been created yet. This gives us the best of both worlds - performance when snapshots exist, and correctness when they don't. The key insight is that snapshots require proper error handling in the command handlers."

---

### Slide 23: Error Handling & Retries: Two Different Worlds
**Key Points:**
- Distinguish between command and projection failures
- Show different strategies for each
- Emphasize idempotence importance
- Keep it practical
- Transition from performance to resilience concerns

**Speaking Notes:**
"Now let's talk about error handling and retries, which are actually two different worlds. For commands - the synchronous API calls - we use Unit of Work to ensure atomicity. Either the event is stored and dispatched, or it fails completely and the API returns a 500. There's no retry here - it's all or nothing. For projections - the asynchronous Celery tasks - we use Celery's built-in retry mechanisms with late acknowledgment. Messages are never lost, but idempotence is critical because the same message can arrive multiple times. This actually enables powerful capabilities like backfill tasks that can reprocess all events from the event store."

---

### Slide 24: Debugging Superpowers: The Immutable World
**Key Points:**
- Show debugging superpowers
- Give concrete examples
- Emphasize the value
- Connect to real scenarios
- Transition from resilience to debugging benefits

**Speaking Notes:**
"Now, this is where event sourcing really shines - debugging. Traditional debugging is like 'I don't know what happened' - check logs maybe, check database current state only, ask users unreliable. Event sourcing debugging is 'I can see exactly what happened' - we get all events around a timestamp, see every change with timestamps and data, and can replay to see the exact state. Every change is recorded - nothing is lost."

---

### Slide 25: Real-World Trade-offs & Key Takeaways
**Key Points:**
- Be honest about limitations
- Show when it's overkill
- Present balanced trade-offs
- Help audience make informed decisions
- Provide clear takeaways
- Transition from challenges to summary

**Speaking Notes:**
"Let's be honest about when NOT to use event sourcing. It's overkill for simple CRUD applications. It has a steep learning curve for teams new to distributed systems. Traditional logging suffices for systems with simple audit requirements. And it has overhead for performance-critical reads. Event sourcing is for systems that need to explain themselves. Here are the real trade-offs: you gain complete audit trail, time travel, debugging superpowers, and scalability, but you lose simplicity, immediate consistency, storage overhead, and learning curve. So what have we learned today? Event sourcing is about building systems that can explain themselves. Python + FastAPI + Celery are more than capable for serious architecture. Eventual consistency requires thoughtful UI design. Performance requires design - snapshots, indexing, caching. And event sourcing is not for every system - know when to use it. The goal is to build systems that can explain themselves 6 months from now."

---

### Slide 26: Thank You
**Key Points:**
- Thank the audience
- Invite questions
- End warmly
- Transition from summary to closing

**Speaking Notes:**
"Thank you all for your attention. I hope I've convinced you that raw events are worth loving. I'm happy to take questions. Let's have a great discussion!"

---

## Overall Presentation Flow:

**Section Breakdown:**
- Section 1: Opening Story (Slides 1-5): 4 minutes
- Section 2: Core Concepts (Slides 6-13): 7 minutes
- Section 3: Python Ecosystem (Slides 14-19): 8 minutes
- Section 4: Real-World Patterns (Slides 20-25): 5 minutes
- Thank You (Slide 26): 1 minute
- Total: 25 minutes

**Key Speaking Tips:**
- Use the debugging story to anchor the entire presentation
- Connect each theoretical concept to real-world scenarios
- Emphasize the Python ecosystem's readiness for serious architecture
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
- Each section builds on the previous one
- Clear narrative flow from problem to solution to implementation to reality
- Consistent story-telling approach throughout
- Build complexity gradually

**Code Examples Strategy:**
- Use actual code to show real implementation
- Explain the patterns (Events, Aggregates, Command Handlers, Projections, etc.)
- Show how Python features (Pydantic, async/await, Celery) enable this architecture
- Demonstrate the separation of concerns and clean design
