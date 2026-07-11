"""Shared interfaces, DTOs, and base classes used across modules."""

from app.shared.interfaces import (
    RepositoryInterface,
    ServiceInterface,
    AIProviderInterface,
    VectorStoreInterface,
    StorageInterface,
    CacheInterface,
    SearchInterface,
    TaskQueueInterface,
)

__all__ = [
    "RepositoryInterface",
    "ServiceInterface",
    "AIProviderInterface",
    "VectorStoreInterface",
    "StorageInterface",
    "CacheInterface",
    "SearchInterface",
    "TaskQueueInterface",
]