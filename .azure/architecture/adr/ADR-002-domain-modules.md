# ADR-002: Domain-Driven Module Architecture

## Status

Accepted

## Context

The Multimax AI Hub spans 15+ phases covering AI chat, coding, research, agents, documents, image
generation, voice, video, workflow automation, and more. Each phase represents a distinct domain
that must be independently developable, testable, and deployable.

The architecture must support:
- Independent module development by different contributors
- Dynamic loading/unloading of features
- Future plugin marketplace (Phase 11)
- Graceful degradation when a module fails

## Decision

We will use a **Domain-Driven Module Architecture** where each phase maps to a self-contained
Python package under `app/modules/`. Each module:

1. Has its own models, services, API routes, and tests
2. Exposes a standard `register(app, container)` function
3. Declares a `module_info` dict with metadata (name, version, dependencies)
4. Is discovered and loaded dynamically by `ModuleLoader`
5. Communicates with other modules only through the event bus (loose coupling)

Module categories:
- **Core**: Config, DI, logger, events, database, plugin manager, module loader
- **Shared**: Reusable interfaces (repositories, services, AI providers)
- **Domain**: Specific business logic (chat, research, agents, etc.)

## Consequences

- Positive: Clear separation of concerns between domains
- Positive: Independent development and testing
- Positive: Dynamic loading enables the plugin marketplace
- Positive: One module's failure doesn't crash the entire app
- Negative: Requires upfront design for module interfaces
- Negative: Event-based communication adds indirection
- Neutral: Module loader adds startup time proportional to number of modules