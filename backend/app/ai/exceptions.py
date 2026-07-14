"""
AI Provider Exceptions for Multimax AI Hub.

All AI-specific exceptions inherit from MultimaxError to ensure
consistent error handling across the entire application.
"""

from typing import Any, Dict, Optional

from app.core.exceptions import MultimaxError


class AIProviderError(MultimaxError):
    """Base exception for all AI provider errors."""

    def __init__(
        self,
        message: str = "AI provider error",
        code: str = "AI_PROVIDER_ERROR",
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=status_code, details=details)


class ProviderUnavailableError(AIProviderError):
    """Raised when a provider is not available or cannot be reached."""

    def __init__(
        self,
        provider_name: str = "unknown",
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        msg = message or f"AI provider '{provider_name}' is unavailable"
        super().__init__(
            message=msg,
            code="PROVIDER_UNAVAILABLE",
            status_code=503,
            details=details,
        )
        self.provider_name = provider_name


class InvalidModelError(AIProviderError):
    """Raised when an invalid or unsupported model is requested."""

    def __init__(
        self,
        model: str = "unknown",
        provider_name: str = "unknown",
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        msg = message or f"Model '{model}' is not supported by provider '{provider_name}'"
        super().__init__(
            message=msg,
            code="INVALID_MODEL",
            status_code=400,
            details={"model": model, "provider": provider_name, **(details or {})},
        )
        self.model = model
        self.provider_name = provider_name


class InvalidApiKeyError(AIProviderError):
    """Raised when the API key for a provider is invalid or missing."""

    def __init__(
        self,
        provider_name: str = "unknown",
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        msg = message or f"Invalid or missing API key for provider '{provider_name}'"
        super().__init__(
            message=msg,
            code="INVALID_API_KEY",
            status_code=401,
            details=details,
        )
        self.provider_name = provider_name


class RateLimitError(AIProviderError):
    """Raised when a provider's rate limit has been exceeded."""

    def __init__(
        self,
        provider_name: str = "unknown",
        retry_after: Optional[int] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        msg = message or f"Rate limit exceeded for provider '{provider_name}'"
        super().__init__(
            message=msg,
            code="PROVIDER_RATE_LIMIT",
            status_code=429,
            details={"retry_after": retry_after, **(details or {})},
        )
        self.provider_name = provider_name
        self.retry_after = retry_after


class ProviderConfigurationError(AIProviderError):
    """Raised when a provider is misconfigured."""

    def __init__(
        self,
        provider_name: str = "unknown",
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        msg = message or f"Provider '{provider_name}' is misconfigured"
        super().__init__(
            message=msg,
            code="PROVIDER_CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )
        self.provider_name = provider_name