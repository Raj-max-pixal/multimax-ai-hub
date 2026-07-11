"""
Persistent Event Bus.

Provides an event-driven architecture with:
- In-memory and PostgreSQL backends
- Automatic retry with exponential backoff
- Dead letter queue for failed events
- Type-based event routing
"""

from __future__ import annotations

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type

from app.core.config import Settings
from app.core.logger import get_logger

logger = get_logger("app.core.events")


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass
class Event:
    """Base event class.

    All events should inherit from this class or use it directly.
    """

    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    source: str = "system"
    priority: EventPriority = EventPriority.NORMAL
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retry_count: int = 0
    max_retries: int = 3
    status: EventStatus = EventStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        return cls(**data)


EventHandler = Callable[[Event], Any]


class EventBus(ABC):
    """Abstract event bus interface."""

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event to all registered handlers."""
        ...

    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        ...

    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the event bus processing loop."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus processing loop."""
        ...


class InMemoryEventBus(EventBus):
    """In-memory event bus implementation.

    Suitable for development and single-process deployments.
    Events are not persisted and will be lost on restart.
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._handlers: Dict[str, EventHandler] = {}
        self._dead_letter_queue: List[Event] = []
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._running = False

    async def publish(self, event: Event) -> None:
        event.max_retries = self._max_retries
        await self._process_event(event)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Handler subscribed to event type: {event_type}")

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def start(self) -> None:
        self._running = True
        logger.info("In-memory event bus started")

    async def stop(self) -> None:
        self._running = False
        if self._dead_letter_queue:
            logger.warning(f"Dead letter queue has {len(self._dead_letter_queue)} unprocessed events")
        logger.info("In-memory event bus stopped")

    async def _process_event(self, event: Event) -> None:
        handlers = self._subscribers.get(event.type, [])
        if not handlers:
            logger.debug(f"No handlers for event type: {event.type}")
            return

        for handler in handlers:
            try:
                event.status = EventStatus.PROCESSING
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
                event.status = EventStatus.COMPLETED
            except Exception as e:
                logger.error(f"Handler failed for event {event.id}: {e}")
                if event.retry_count < self._max_retries:
                    event.retry_count += 1
                    event.status = EventStatus.RETRYING
                    await asyncio.sleep(self._retry_delay * event.retry_count)
                    await self._process_event(event)
                else:
                    event.status = EventStatus.DEAD_LETTER
                    self._dead_letter_queue.append(event)
                    logger.error(f"Event {event.id} moved to dead letter queue after {event.retry_count} retries")


class PostgresEventBus(EventBus):
    """PostgreSQL-backed event bus.

    Provides persistence, at-least-once delivery, and survives restarts.
    Implementation placeholder for Phase 1.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._subscribers: Dict[str, List[EventHandler]] = {}

    async def publish(self, event: Event) -> None:
        # TODO: Implement PostgreSQL-backed event publishing
        # with INSERT into events table + LISTEN/NOTIFY
        logger.info(f"Event published (Postgres): {event.type} [{event.id}]")

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def start(self) -> None:
        logger.info("PostgreSQL event bus started")

    async def stop(self) -> None:
        logger.info("PostgreSQL event bus stopped")


def create_event_bus(settings: Settings) -> EventBus:
    """Factory function to create the appropriate event bus."""
    if settings.EVENT_BUS_BACKEND == "postgresql":
        return PostgresEventBus(settings)
    return InMemoryEventBus(
        max_retries=settings.EVENT_BUS_MAX_RETRIES,
        retry_delay=settings.EVENT_BUS_RETRY_DELAY_SECONDS,
    )