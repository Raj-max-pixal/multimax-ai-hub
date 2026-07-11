# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Multimax AI Hub project.

## What is an ADR?

An Architecture Decision Record is a short document that captures an important architectural
decision made along with its context and consequences.

## Index

| ID | Title | Status |
|----|-------|--------|
| 001 | [Use Architecture Decision Records](ADR-001-record-architecture-decisions.md) | Accepted |
| 002 | [Domain-Driven Module Architecture](ADR-002-domain-modules.md) | Accepted |
| 003 | [AI Provider Abstraction Layer](ADR-003-ai-provider-abstraction.md) | Accepted |
| 004 | [Event-Driven Communication Between Modules](ADR-004-event-driven-communication.md) | Accepted |
| 005 | [Zero-Budget Open Source Stack](ADR-005-zero-budget-stack.md) | Accepted |

## Adding New ADRs

1. Create a new markdown file following the template below
2. Number sequentially (ADR-006, ADR-007, etc.)
3. Update this README with the new entry
4. Submit for review

### Template

```markdown
# ADR-NNN: Title

## Status

Proposed | Accepted | Deprecated | Superseded

## Context

Why is this decision needed? What problem does it solve?

## Decision

What was decided? Describe the chosen approach in detail.

## Consequences

- Positive: ...
- Positive: ...
- Negative: ...
- Neutral: ...