"""
Shared Interfaces.

Defines the contracts that all domain modules must follow.
This ensures consistency and interchangeability across the application.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, Protocol, Sequence, TypeVar, Union
from datetime import datetime


# --------------------------------------------------------------------------- #
# Generic Types
# --------------------------------------------------------------------------- #

T = TypeVar("T")
ID = TypeVar("ID")


# --------------------------------------------------------------------------- #
# Repository Pattern
# --------------------------------------------------------------------------- #

class RepositoryInterface(ABC, Generic[T, ID]):
    """Generic repository interface for data access."""

    @abstractmethod
    async def get(self, id: ID) -> Optional[T]:
        """Get an entity by its identifier."""
        ...

    @abstractmethod
    async def get_all(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> tuple[list[T], int]:
        """Get all entities with pagination and optional filters.
        Returns (items, total_count).
        """
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        ...

    @abstractmethod
    async def update(self, id: ID, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing entity. Returns None if not found."""
        ...

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete an entity. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    async def count(self, **filters) -> int:
        """Count entities matching the given filters."""
        ...

    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """Check if an entity exists."""
        ...


# --------------------------------------------------------------------------- #
# Service Pattern
# --------------------------------------------------------------------------- #

class ServiceInterface(ABC):
    """Base interface for all business logic services."""

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        ...


# --------------------------------------------------------------------------- #
# AI Provider Pattern
# --------------------------------------------------------------------------- #

@dataclass
class ChatMessage:
    """A single message in a chat conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )


@dataclass
class ChatRequest:
    """A request to an AI chat model."""
    messages: List[ChatMessage]
    model: str = ""
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)


@dataclass
class ChatResponse:
    """A response from an AI chat model."""
    message: ChatMessage
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: str = "stop"


class AIProviderInterface(ABC):
    """Interface for AI model providers (Ollama, OpenAI, etc.)."""

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a chat request and get a response."""
        ...

    @abstractmethod
    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """Send a streaming chat request. Yields response chunks."""
        ...

    @abstractmethod
    async def get_models(self) -> List[Dict[str, Any]]:
        """List available models from this provider."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is reachable."""
        ...


# --------------------------------------------------------------------------- #
# Vector Store Pattern
# --------------------------------------------------------------------------- #

@dataclass
class VectorEmbedding:
    """A vector embedding with metadata."""
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    text: str = ""


@dataclass
class SearchResult:
    """A search result from a vector store."""
    id: str
    score: float
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStoreInterface(ABC):
    """Interface for vector database operations."""

    @abstractmethod
    async def add_embeddings(
        self, collection: str, embeddings: List[VectorEmbedding]
    ) -> int:
        """Add embeddings to a collection. Returns count added."""
        ...

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        ...

    @abstractmethod
    async def delete_embeddings(
        self, collection: str, ids: List[str]
    ) -> int:
        """Delete embeddings by IDs."""
        ...

    @abstractmethod
    async def get_collections(self) -> List[str]:
        """List all collections."""
        ...


# --------------------------------------------------------------------------- #
# Storage Pattern
# --------------------------------------------------------------------------- #

class StorageInterface(ABC):
    """Interface for file storage operations."""

    @abstractmethod
    async def upload(
        self, path: str, data: bytes, content_type: Optional[str] = None
    ) -> str:
        """Upload a file. Returns the file URL/path."""
        ...

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """Download a file."""
        ...

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete a file."""
        ...

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if a file exists."""
        ...

    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files with the given prefix."""
        ...


# --------------------------------------------------------------------------- #
# Cache Pattern
# --------------------------------------------------------------------------- #

class CacheInterface(ABC):
    """Interface for caching operations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value."""
        ...

    @abstractmethod
    async def set(
        self, key: str, value: Any, ttl_seconds: int = 300
    ) -> None:
        """Set a cached value with TTL."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        ...


# --------------------------------------------------------------------------- #
# Search Pattern
# --------------------------------------------------------------------------- #

class SearchInterface(ABC):
    """Interface for full-text search operations."""

    @abstractmethod
    async def search(
        self, index: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search across an index."""
        ...

    @abstractmethod
    async def index_document(
        self, index: str, document_id: str, content: Dict[str, Any]
    ) -> bool:
        """Index a document for search."""
        ...

    @abstractmethod
    async def remove_document(self, index: str, document_id: str) -> bool:
        """Remove a document from the index."""
        ...


# --------------------------------------------------------------------------- #
# Task Queue Pattern
# --------------------------------------------------------------------------- #

class TaskQueueInterface(ABC):
    """Interface for async task processing."""

    @abstractmethod
    async def enqueue(
        self, task_name: str, payload: Dict[str, Any], delay: int = 0
    ) -> str:
        """Enqueue a task for async processing. Returns task ID."""
        ...

    @abstractmethod
    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a task."""
        ...

    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        ...