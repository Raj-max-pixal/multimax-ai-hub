"""
Base Exception Classes for Multimax AI Hub.

All domain-specific exceptions should inherit from MultimaxError.
This allows consistent error handling across the entire application.
"""

from typing import Any, Dict, Optional


class MultimaxError(Exception):
    """Base exception for all Multimax AI Hub errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ConfigurationError(MultimaxError):
    """Raised when application configuration is invalid or missing."""

    def __init__(self, message: str = "Invalid configuration", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="CONFIGURATION_ERROR", status_code=500, details=details)


class NotFoundError(MultimaxError):
    """Raised when a requested resource was not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="NOT_FOUND", status_code=404, details=details)


class AuthenticationError(MultimaxError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="AUTHENTICATION_ERROR", status_code=401, details=details)


class AuthorizationError(MultimaxError):
    """Raised when the user lacks permission for an action."""

    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="AUTHORIZATION_ERROR", status_code=403, details=details)


class ValidationError(MultimaxError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class DuplicateError(MultimaxError):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, message: str = "Resource already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="DUPLICATE_ERROR", status_code=409, details=details)


class ExternalServiceError(MultimaxError):
    """Raised when an external service (AI model, database, etc.) fails."""

    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        code = f"EXTERNAL_SERVICE_ERROR_{service_name.upper()}" if service_name else "EXTERNAL_SERVICE_ERROR"
        super().__init__(message=message, code=code, status_code=502, details=details)


class RateLimitError(MultimaxError):
    """Raised when the API rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="RATE_LIMIT_ERROR", status_code=429, details=details)