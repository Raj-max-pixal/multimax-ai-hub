"""
Storage Module Exceptions.

Defines domain-specific exceptions for file storage operations.
"""

from app.core.exceptions import MultimaxError


class StorageError(MultimaxError):
    """Base exception for all storage-related errors."""

    def __init__(self, message: str = "Storage operation failed", details: dict = None):
        super().__init__(message=message, code="STORAGE_ERROR", status_code=500, details=details)


class FileNotFoundError_(StorageError):
    """Raised when a requested file is not found in storage."""

    def __init__(self, path: str = ""):
        super().__init__(
            message=f"File not found: {path}",
            code="FILE_NOT_FOUND",
            status_code=404,
            details={"path": path},
        )


class FileAlreadyExistsError(StorageError):
    """Raised when attempting to create a file that already exists."""

    def __init__(self, path: str = ""):
        super().__init__(
            message=f"File already exists: {path}",
            code="FILE_ALREADY_EXISTS",
            status_code=409,
            details={"path": path},
        )


class StorageQuotaExceededError(StorageError):
    """Raised when storage quota has been exceeded."""

    def __init__(self, path: str = "", current_bytes: int = 0, max_bytes: int = 0):
        super().__init__(
            message=f"Storage quota exceeded: {path}",
            code="STORAGE_QUOTA_EXCEEDED",
            status_code=413,
            details={
                "path": path,
                "current_bytes": current_bytes,
                "max_bytes": max_bytes,
            },
        )


class InvalidFilePathError(StorageError):
    """Raised when the provided file path is invalid."""

    def __init__(self, path: str = "", reason: str = ""):
        super().__init__(
            message=f"Invalid file path: {path} — {reason}",
            code="INVALID_FILE_PATH",
            status_code=422,
            details={"path": path, "reason": reason},
        )