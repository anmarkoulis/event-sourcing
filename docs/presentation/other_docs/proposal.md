# Proposal for PyCon

## Title

How I Learned to Stop Worrying and Love Raw Events: Event Sourcing & CQRS with FastAPI and Celery.

## Abstract

What happens when you stop storing the current state and start storing every change instead?

In this talk, we'll explore how to build Python systems that are audited by design, event-driven at the core, and designed around CQRS and event sourcing. Using FastAPI, Celery, and a few familiar cloud tools, we'll follow the evolution of a real-world architecture that treats raw events as first-class citizens.

We'll dive into the fundamental questions:
	•	How do you model the world as a sequence of immutable events?
	•	What does it mean to replay the past—and why would you want to?
	•	Can you build a system that has no "current state," and still serve fast, reliable queries?
	•	How do you scale such a system? Can it be consistent… eventually?
	•	How do you handle failures, race conditions, and fixes in a world where data isn't just stored—it's remembered?
	•	What does debugging look like when nothing is overwritten, and history is always available?

We'll also touch on key design patterns—separating command from query logic, modularizing business rules with services and repositories, and how Celery can power a resilient pipeline for processing and projecting events.

You'll leave with a deeper appreciation for the power of raw events, an understanding of what it means to treat event sourcing as a design philosophy, and a toolkit of questions to challenge the way you build your next Python backend.

## Outline

1. Intro & Motivation (3–4 min)
   - Who am I?
   - What are raw events? And why would anyone love them?
   - The pain points of traditional architectures (tight coupling, poor auditability, mutable state)
   - Quick teaser: what does an "audited-by-design" system look like?

2. Core Concepts (5–6 min)
   - Event Sourcing:
     - Store every change as an immutable event
     - System state = the result of replaying events
   - CQRS (Command Query Responsibility Segregation):
     - Separate write model (commands/events) from read model (queries)
     - Benefits: auditability, modularity, scalability
     - Misconception bust: You don't need Kafka to do this

3. Architecture Walkthrough (10–12 min)
   - High-level flow:
     - External event → queue → processing → publish → read model
   - Tools & layers:
     - Celery: async task runner, scalable workers
     - FastAPI: API surface for queries (and optionally commands)
     - Internal Event Bus: pub/sub style comms (e.g., EventBridge)
   - Key components:
     - Raw event ingestion
     - Event store (write DB)
     - Replaying events to build current state
     - Read DB (search-optimized)
   - Emphasize design flexibility via:
     - Services + repositories for command/query
     - Async + decoupling for scale

4. Real-World Patterns & Gotchas (6–7 min)
   - Eventual consistency: why it's a feature, not a bug
   - Snapshots for performance on replay
   - Initial backfill: bootstrapping from source APIs
   - Fixes by reprocessing history — no manual data patching
   - Debugging & testing in an immutable world

5. Key Takeaways & Reflections (2–3 min)
   - Raw events are scary — until you realize how powerful they are
   - Python + Celery + FastAPI are more than capable for serious architecture
   - Event sourcing is a mindset shift, not a silver bullet — but it's fun
   - The system you build today should be able to explain itself 6 months from now


   ## Abstract as a short post

   Love raw events? So do we. Event Sourcing & CQRS with FastAPI and Celery, the Pythonic way.

   ## Biography

   **Option 1:**
   I am a Senior Staff Engineer at Orfium, where I work with multiple teams and am responsible for the technical growth of engineers and software quality across the organization. Despite studying Physics, I entered the world of software engineering through coding for simulations. This passion was enhanced during my Master's in Computational Physics, which led to my first role as a software engineer. I've worked across diverse industries including simulations, security platforms, and music technology. From small startups to larger organizations, I've experienced the complete development lifecycle. I am committed to building software that not only meets customer needs but does so with exceptional quality and efficiency.

   **Option 2:**
   I am a Senior Staff Engineer at Orfium, where I work with multiple teams and am responsible for the technical growth of engineers and software quality across the organization. Despite my Physics background, I found my way into software engineering through coding for simulations. This journey was accelerated during my Master's in Computational Physics, which opened the door to my first software engineering position. My experience spans simulations, security platforms, and music technology. I've worked in both small startups and larger organizations, giving me a comprehensive view of the development lifecycle. I am committed to building software that not only meets customer needs but does so with exceptional quality and efficiency.

   **Option 3:**
   I am a Senior Staff Engineer at Orfium, where I work with multiple teams and am responsible for the technical growth of engineers and software quality across the organization. Despite studying Physics, I discovered software engineering through coding for simulations. This path was solidified during my Master's in Computational Physics, which propelled me into my first software engineering role. I've worked in simulations, security platforms, and music technology. Throughout my career, I've experienced environments ranging from small startups to larger organizations, providing me with a complete understanding of the development lifecycle. I am committed to building software that not only meets customer needs but does so with exceptional quality and efficiency.

   **Option 4:**
   I am a Senior Staff Engineer at Orfium, where I work with multiple teams and am responsible for the technical growth of engineers and software quality across the organization. Despite my Physics education, I ventured into software engineering through coding for simulations. This transition was catalyzed during my Master's in Computational Physics, which marked the beginning of my software engineering career. My career has taken me through simulations, security platforms, and music technology. I've experienced the full spectrum from small startups to larger organizations, gaining comprehensive insight into the development lifecycle. I am committed to building software that not only meets customer needs but does so with exceptional quality and efficiency.

   **Option 5:**
   I am a Senior Staff Engineer at Orfium, where I work with multiple teams and am responsible for the technical growth of engineers and software quality across the organization. Despite studying Physics, I crossed into software engineering through coding for simulations. This transformation was deepened during my Master's in Computational Physics, which launched my career as a software engineer. I've worked across simulations, security platforms, and music technology. From small startups to larger organizations, I've witnessed the development lifecycle in various contexts. I am committed to building software that not only meets customer needs but does so with exceptional quality and efficiency.
