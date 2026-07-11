# ADR-004: Event-Driven Communication Between Modules

## Status

Accepted

## Context

With the Domain-Driven Module Architecture (ADR-002), modules must communicate without
tight coupling. Direct imports between domain modules would create circular dependencies
and prevent independent development. A mechanism is needed for asynchronous, decoupled
inter-module communication.

## Decision

We will use an **Event-Driven Communication** pattern with a central **Event Bus**:

1. Modules publish events to the Event Bus via `event_bus.publish(event_name, payload)`
2. Modules subscribe to events via `event_bus.subscribe(event_name, handler)`
3. Events are typed dataclasses with a standardized envelope:
   - `event_name`: Namespaced string (`module_name.event_type`)
   - `payload`: Dict or Pydantic model
   - `timestamp`: ISO 8601 timestamp
   - `source`: Module name that published the event
4. Event handlers run asynchronously via the FastAPI background task system

Key events defined for Phase 0:
- `workspace.created` — A new workspace was created
- `workspace.updated` — Workspace settings changed
- `workspace.deleted` — A workspace was removed
- `project.created` — A project was created
- `project.deleted` — A project was deleted

## Consequences

- Positive: Modules remain loosely coupled
- Positive: New modules can react to existing events without modifying publishers
- Positive: Enables async workflows and background processing
- Positive: Audit trail through event logging
- Negative: Eventual consistency — subscribers see events after a delay
- Negative: Debugging event flows can be more complex than direct calls
- Negative: Requires discipline to avoid event overload