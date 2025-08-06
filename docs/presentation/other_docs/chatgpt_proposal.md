🎬 1. [Slide] Title Slide (1 min)

Title: How I Learned to Stop Worrying and Love Raw Events
Subtitle: Event Sourcing & CQRS with FastAPI and Celery

✔️ Speaker intro (1-liner on background)
✔️ What we'll cover: Problem → Solution → Real-world lessons
🟡 2. [Slide] Why Traditional Architectures Break Down (2 min)

Slide: Diagram showing state overwrite flow (CRUD → SQL)
Key Points:

    You only store current state — you lose history

    No audit trail, can't replay or debug

    Scaling issues: same DB, same schema, same contention

🟢 Tell a story here: “Imagine a user account was deleted accidentally. Can you tell me exactly when, how, and why?”
🟢 3. [Slide] Enter Event Sourcing + CQRS (2 min)

Diagram: Commands → Events → Stream → Read Models

Definitions:

    Event Sourcing: Store every change as an event

    CQRS: Separate reads and writes into different models

🎯 Value prop:

    Immutability = integrity

    Replay = debugging

    Separation = scalability

🧱 4. [Slide] Events: The New Source of Truth (2 min)

Code (10 lines): UserCreated event model
Emphasize:

    Immutable

    Append-only

    Time-stamped

🧠 Analogy: “Think Git, not SQL.”
🧩 5. [Slide] Event Streams & Rebuilding State (2 min)

Diagram:

UserCreated → NameChanged → StatusChanged
 → Aggregate State

Concept: Events are applied in order to reconstruct domain state.
🔀 6. [Slide] CQRS: Reads & Writes Split (2 min)

Split diagram:
Commands → Events → Write store
← Read model ← Projections ← Events

🎯 Explain: Read DB can be optimized, denormalized, or stored in Redis/Postgres/Elastic/etc.
🧪 7. [Slide] Real Example: Create User Flow (3 min)

Diagram + minimal code (~8 lines):
FastAPI POST → Command handler → Aggregate → Event → EventStore → ReadModel (via Celery)

Emphasize:

    Async = fast response

    Celery processes event

    Projection builds read model

🎯 Focus more on flow than syntax.
⚠️ 8. [Slide] What Could Go Wrong? (2 min)

Bullet points:

    Eventual consistency

    Projection failures

    Schema evolution

    Debugging across services

🎯 Add humility here: "These aren't magic bullets — just better defaults when history matters."
🧠 9. [Slide] Schema Evolution: Changing Events (2 min)

Concept only:

    Events are versioned

    You migrate or version your handlers

    Strategy: don’t break old events, support both for a while

🧪 10. [Slide] Debugging with Time Travel (2 min)

Mini code (5 lines): replay events around a timestamp
🎯 Value: No more "I don't know what happened."
🧪 11. [Slide] Testing Aggregates & Pipelines (2 min)

Testing philosophy:

    Events as inputs

    State or events as outputs

    Fully reproducible test cases

🎯 Emphasize immutability = testability
⚙️ 12. [Slide] Why Celery? Why FastAPI? (1 min)

✔️ FastAPI = modern, async, clean
✔️ Celery = battle-tested, easy to start
⚠️ Acknowledge: not perfect, but gets you going
📈 13. [Slide] Scaling: Start Simple, Grow Later (1 min)

Diagram:
Start with: FastAPI + PostgreSQL + Celery
Grow to: Kafka + Snapshots + Multiple Projections + Caching

🎯 "You don’t need Kafka to start."
📊 14. [Slide] Production Insights (2 min)

Lessons from real-world use:

    Use snapshots for long histories

    Monitor projection lag

    Reprocess streams instead of patching data

    Build read model tools for ops/debug

❓ 15. [Slide] When NOT to Use This (2 min)

Bullet list:

    CRUD-heavy apps without audit needs

    Simple workflows, no replay required

    Teams not ready for operational overhead

🎯 Show maturity by acknowledging tradeoffs.
✅ 16. [Slide] Summary (1 min)

Key messages:

    Think in events, not state

    CQRS + Event Sourcing give you powerful traceability

    Python has the ecosystem (FastAPI, Celery, Pydantic)

    Start small — evolve over time

🙏 17. [Slide] Thank You + Questions
