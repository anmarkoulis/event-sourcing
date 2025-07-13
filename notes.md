# Speaker Notes: Event Sourcing & CQRS with FastAPI and Celery

## Section 1: Intro & Motivation (3-4 minutes)

### Slide 1: Title Slide (30 seconds)
**Key Points:**
- Welcome everyone to PyCon Athens
- Mention this is about a mindset shift in how we think about data
- The title is a play on "Dr. Strangelove" - events can be scary but powerful
- Set expectation: 30 minutes, lots of code examples, interactive

**Speaking Notes:**
"Good morning everyone! I'm excited to be here at PyCon Athens. Today we're going to talk about something that might sound scary at first - raw events. But by the end of this talk, I hope you'll see why I've learned to love them. This is about a fundamental shift in how we think about data in our systems."

---

### Slide 2: Section Overview (15 seconds)
**Key Points:**
- Introduce the structure
- Set expectations for the section

**Speaking Notes:**
"In the next few minutes, I'll introduce myself, explain what raw events are and why they're powerful, show you the pain points of traditional architectures, and give you a quick teaser of what an audited-by-design system looks like."

---

### Slide 3: Who Am I? (45 seconds)
**Key Points:**
- Establish credibility as a staff engineer
- Show real-world experience with scale
- Position as someone who's been through the journey
- Connect with audience's Python experience

**Speaking Notes:**
"I'm a staff engineer who's been working with Python for over a decade. I've built systems that handle millions of events daily, and I've learned the hard way why traditional architectures break down at scale. I'm what you might call an 'event sourcing evangelist' - someone who's recovered from the pain of mutable state and tight coupling. I love immutable data and audit trails, and I want to share why."

---

### Slide 4: What Are Raw Events? (1 minute)
**Key Points:**
- Show the contrast between traditional and event sourcing approaches
- Introduce the fundamental concept
- Show concrete examples of events
- Emphasize immutability

**Speaking Notes:**
"Instead of storing current state, we store every change as an immutable event. Look at this contrast - on the left, we have the traditional approach where we get a user, mutate their state, and save it back, overwriting history. On the right, we have the event sourcing approach where we record a UserCreated event when a user is created, and a UserNameChanged event when their name changes. Each event is immutable, timestamped, and tells us exactly what happened. We're not overwriting history - we're building it."

---

### Slide 5: Why Would Anyone Love Raw Events? (45 seconds)
**Key Points:**
- Highlight the superpowers this gives you
- Connect to real debugging scenarios
- Show business value
- Build excitement

**Speaking Notes:**
"When you store every change, you get these superpowers. Complete audit trail - every action is recorded. Time travel - you can replay any point in history. Debugging superpowers - you can see exactly what happened when something goes wrong. Data integrity - no more lost changes. And scalability - you can separate read and write concerns."

---

### Slide 6: Pain Points of Traditional Architectures (45 seconds)
**Key Points:**
- Show familiar problems that everyone recognizes
- Connect to real pain points developers face
- Set up the motivation for event sourcing

**Speaking Notes:**
"This is what we're used to with traditional architectures. Tight coupling between read and write - you can't scale them independently. Poor auditability - you can't answer 'who changed what when?' Mutable state - data corruption risks. And scaling challenges - read/write conflicts. The result is systems that can't explain themselves."

---

### Slide 7: Quick Teaser: Audited-by-Design System (45 seconds)
**Key Points:**
- Show what the end result looks like
- Demonstrate the power of events
- Build excitement for the solution

**Speaking Notes:**
"Here's what an audited-by-design system looks like. Every action is an event - UserCreated, UserNameChanged, UserEmailChanged. This gives us complete history - nothing is ever lost. We can do temporal queries - what was the state at 3pm? We can replay events to rebuild state from scratch. And we have audit by design - every change is recorded."

---

## Section 2: Core Concepts (5-6 minutes)

### Slide 8: Section Overview (15 seconds)
**Key Points:**
- Introduce the core concepts section
- Set expectations

**Speaking Notes:**
"Now let's dive into the core concepts. I'll explain event sourcing, show you how system state equals the result of replaying events, introduce CQRS, show you the benefits, and bust the misconception that you need Kafka to do this."

---

### Slide 9: Event Sourcing: The Fundamental Idea (1 minute)
**Key Points:**
- Explain the fundamental equation
- Show the mental model shift
- Highlight key principles
- Use the quote to emphasize the concept

**Speaking Notes:**
"This is the fundamental idea of event sourcing: system state equals the result of replaying all events. Instead of saying 'give me the current state,' we say 'replay all events to build the current state.' The key principles are: store every change as an immutable event, never update or delete events, replay events to build current state, and events are the source of truth."

---

### Slide 10: Event Sourcing in Practice (1.5 minutes)
**Key Points:**
- Show the aggregate pattern
- Demonstrate event application
- Show state reconstruction
- Emphasize simplicity

**Speaking Notes:**
"Here's how we implement this in practice. We have an aggregate that knows how to apply events. When we want to get the current state of a user, we get all their events and apply them one by one. This is the core of event sourcing - state is just the result of replaying events. Notice how simple this is - we just apply events in order."

---

### Slide 11: CQRS: Command Query Responsibility Segregation (1 minute)
**Key Points:**
- Explain the separation of concerns
- Show concrete examples
- Keep it simple

**Speaking Notes:**
"CQRS stands for Command Query Responsibility Segregation. We separate our write model - commands that change state - from our read model - queries that retrieve data. Commands handle business logic and emit events. Queries are optimized for fast, flexible reads. This gives us independent scaling and technology flexibility."

---

### Slide 12: CQRS Benefits (1 minute)
**Key Points:**
- Reinforce the benefits
- Address common misconceptions
- Keep it practical

**Speaking Notes:**
"This separation gives us real benefits. Auditability - commands emit events, queries are optimized. Modularity - different models for different concerns. Scalability - read/write workloads differ. Technology flexibility - different DBs for different needs. And here's the key point: you don't need Kafka to start with CQRS. You can start simple."

---

## Section 3: Architecture Walkthrough (10-12 minutes)

### Slide 13: Section Overview (15 seconds)
**Key Points:**
- Introduce the architecture section
- Set expectations for the deep dive

**Speaking Notes:**
"Now let's walk through the architecture. I'll show you the high-level flow, the tools and layers we use, the key components, and how we achieve design flexibility through services, repositories, and async decoupling."

---

### Slide 14: High-Level Architecture Flow (1 minute)
**Key Points:**
- Show the high-level flow
- Introduce key components
- Keep it conceptual
- Set up for detailed examples

**Speaking Notes:**
"Here's the high-level flow. External request comes in, we process it as a command, we store the event, we publish it to an event bus, and we update our read model. The key components are FastAPI for our API surface, Celery for async event processing, an event store for our append-only log, a read model optimized for queries, and an event bus for pub/sub communication."

---

### Slide 15: FastAPI: The Command Interface (2 minutes)
**Key Points:**
- Show real FastAPI code
- Emphasize async nature
- Show immediate response pattern
- Keep it practical

**Speaking Notes:**
"Here's how we implement this with FastAPI. We define our commands using Pydantic models. When a request comes in, we validate it, create an event, append it to our event store, publish it to our event bus, and return immediately. Notice we're not waiting for the event to be processed - we return right away. This gives us high availability and responsiveness."

---

### Slide 16: Celery: Async Task Runner & Scalable Workers (2 minutes)
**Key Points:**
- Show Celery task definitions
- Emphasize async processing
- Show business logic separation
- Demonstrate flexibility

**Speaking Notes:**
"Celery is our async task runner and scalable workers. We define tasks for each event type. When a UserCreated event is published, this task processes it. It can do business logic, update the read model, send emails, notify other services - whatever we need. Each task is independent and can be scaled separately. This gives us tremendous flexibility."

---

### Slide 17: Event Store: The Source of Truth (2 minutes)
**Key Points:**
- Show append-only operations
- Emphasize immutability
- Show stream-based retrieval
- Keep it simple

**Speaking Notes:**
"The event store is our source of truth. It's append-only - we never update or delete events. We store each event with a stream ID, event type, data, and version. To get events for a stream, we query by stream ID and version. This gives us the ability to replay any stream from any point in time."

---

### Slide 18: Read Model: Search-Optimized Database (1.5 minutes)
**Key Points:**
- Show optimized queries
- Emphasize performance
- Show flexibility
- Keep it practical

**Speaking Notes:**
"Our read model is optimized for queries. We can do fast, direct queries by ID. We can do complex searches. We can optimize for different query patterns. This is where we get the performance benefits of CQRS - our reads are fast because they're optimized for reading, not for consistency with writes."

---

### Slide 19: Design Flexibility: Services + Repositories (2 minutes)
**Key Points:**
- Show service layer pattern
- Demonstrate separation of concerns
- Show dependency injection
- Keep it practical

**Speaking Notes:**
"Here's how we achieve design flexibility through services and repositories. On the command side, we have a service that handles business logic and coordinates between the event store and event bus. On the query side, we have a service that uses the read model. This gives us clean separation of concerns and makes testing much easier."

---

### Slide 20: Async + Decoupling for Scale (1 minute)
**Key Points:**
- Reinforce the benefits
- Show scalability advantages
- Keep it practical

**Speaking Notes:**
"This architecture gives us several benefits. High availability - commands return immediately. Independent scaling - read/write workloads differ. Resilience - failures don't cascade. Technology flexibility - different DBs for different needs. And eventual consistency - which is a feature, not a bug."

---

## Section 4: Real-World Patterns & Gotchas (6-7 minutes)

### Slide 21: Section Overview (15 seconds)
**Key Points:**
- Introduce the real-world section
- Set expectations for practical advice

**Speaking Notes:**
"Now let's talk about real-world patterns and gotchas. I'll cover eventual consistency, snapshots for performance, initial backfill, fixes by reprocessing history, and debugging and testing in an immutable world."

---

### Slide 22: Eventual Consistency: Feature, Not Bug (1.5 minutes)
**Key Points:**
- Address the consistency concern
- Show why it's beneficial
- Give concrete examples
- Build confidence

**Speaking Notes:**
"Eventual consistency scares a lot of people, but it's actually a feature. On the command side, we return immediately - high availability. On the query side, we might not have the latest changes yet - but that's okay. This gives us high availability, scalability, and resilience. Failures don't cascade through the system."

---

### Slide 23: Snapshots for Performance on Replay (1.5 minutes)
**Key Points:**
- Address the performance concern
- Show the snapshot pattern
- Demonstrate the improvement
- Keep it practical

**Speaking Notes:**
"One concern with event sourcing is performance - what if you have thousands of events? That's where snapshots come in. We periodically save the state of our aggregates. When we need to build state, we start from the latest snapshot and only replay events after that. This gives us the best of both worlds - performance and auditability."

---

### Slide 24: Initial Backfill: Bootstrapping from Source APIs (1 minute)
**Key Points:**
- Show migration strategy
- Demonstrate practical approach
- Keep it simple

**Speaking Notes:**
"When you're migrating to event sourcing, you need to backfill existing data. Here's how to do it. We get users from the existing system, create events for their current state, store them in the event store, publish them to the event bus, and update the read model. This gives us a clean migration path."

---

### Slide 25: Fixes by Reprocessing History (1 minute)
**Key Points:**
- Show safe data fixes
- Contrast with traditional approach
- Emphasize safety
- Show automation

**Speaking Notes:**
"Instead of scary manual data patches, we emit correction events. This is much safer - we're not directly manipulating data. All our projections will be updated automatically. We maintain our audit trail. And we can replay the fix if needed."

---

### Slide 26: Debugging in an Immutable World (1 minute)
**Key Points:**
- Show debugging superpowers
- Give concrete examples
- Emphasize the value
- Connect to real scenarios

**Speaking Notes:**
"This is where event sourcing really shines - debugging. We can see exactly what happened by replaying events. We can compare states at different times. We can answer questions like 'what was the user's state at 3pm?' This is incredibly powerful for debugging production issues."

---

### Slide 27: Testing in an Immutable World (1 minute)
**Key Points:**
- Show testing strategies
- Emphasize simplicity
- Show confidence
- Keep it practical

**Speaking Notes:**
"Testing event-sourced systems is actually quite straightforward. Test your aggregates by applying events. Test your event store by appending and retrieving events. The immutability makes testing much more predictable."

---

## Section 5: Key Takeaways & Reflections (2-3 minutes)

### Slide 28: Section Overview (15 seconds)
**Key Points:**
- Introduce the final section
- Set expectations for takeaways

**Speaking Notes:**
"Let me wrap up with some key takeaways and reflections. I want to leave you with some thoughts about raw events, the Python ecosystem, event sourcing as a mindset, and building systems that can explain themselves."

---

### Slide 29: Key Takeaways (1.5 minutes)
**Key Points:**
- Reinforce main messages
- Keep it memorable
- End strong
- Connect to audience

**Speaking Notes:**
"Here are the key things I want you to remember. Raw events are powerful - they give you audit trails, time travel, and debugging superpowers. The Python ecosystem is ready - FastAPI, Celery, and async/await are perfect for this. Start simple - you don't need complex infrastructure. Event sourcing is a mindset shift - think in terms of what happened, not what is. And your system should explain itself - six months from now, you'll thank yourself."

---

### Slide 30: Questions to Challenge Your Architecture (1 minute)
**Key Points:**
- Give actionable questions
- Encourage thinking
- End with reflection
- Connect to next steps

**Speaking Notes:**
"Before your next project, ask yourself these questions. What if I stored every change instead of just current state? How would I debug this if I could replay every action? What would complete audit trails mean for my business? Could I separate read and write concerns? What if my data was immutable? These questions will help you think differently about your architecture."

---

### Slide 31: Questions & Discussion (30 seconds)
**Key Points:**
- Invite audience participation
- Set up for Q&A
- Keep it engaging

**Speaking Notes:**
"Now let's have a discussion. What are your experiences with event sourcing? What challenges have you faced with traditional architectures? What questions do you have about implementation details?"

---

### Slide 32: Resources (30 seconds)
**Key Points:**
- Provide further reading
- Show tools and libraries
- Keep it practical
- End with action items

**Speaking Notes:**
"Here are some resources to dive deeper. These books will give you the theoretical foundation. These tools and libraries will help you implement event sourcing in Python. Start with the simple stuff and work your way up."

---

### Slide 33: Thank You (30 seconds)
**Key Points:**
- Thank the audience
- Provide contact info
- Invite questions
- End warmly

**Speaking Notes:**
"Thank you all for your attention. I hope I've convinced you that raw events are worth loving. I'm happy to take questions, and you can find me on Twitter or email. Let's have a great discussion!"

---

## Overall Presentation Flow:

**Timing Breakdown:**
- Section 1: Intro & Motivation (Slides 1-7): 4 minutes
- Section 2: Core Concepts (Slides 8-12): 5.5 minutes
- Section 3: Architecture Walkthrough (Slides 13-20): 12 minutes
- Section 4: Real-World Patterns (Slides 21-27): 7 minutes
- Section 5: Key Takeaways (Slides 28-33): 3 minutes

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
