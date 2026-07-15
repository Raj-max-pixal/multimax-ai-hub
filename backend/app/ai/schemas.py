

"""
Pydantic schemas for AI API request/response validation.

These schemas mirror the dataclasses in base.py but use Pydantic
for FastAPI integration and request validation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GenerationRequestSchema(BaseModel):
    """Request schema for model generation."""

    model: str = Field(..., description="Model ID to use for generation")
    messages: List[Dict[str, str]] = Field(
        ..., description="List of message dicts with 'role' and 'content' keys"
    )
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    top_p: float = Field(0.95, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    stream: bool = Field(False, description="Whether to stream the response")


class GenerationResponseSchema(BaseModel):
    """Response schema for model generation."""

    content: str = Field(..., description="Generated text content")
    model: str = Field(..., description="Model used for generation")
    provider: str = Field(..., description="Provider that generated the response")
    finish_reason: str = Field("stop", description="Reason generation finished")
    tokens_prompt: Optional[int] = Field(None, description="Prompt token count")
    tokens_completion: Optional[int] = Field(None, description="Completion token count")
    tokens_total: Optional[int] = Field(None, description="Total token count")
    latency_ms: Optional[float] = Field(None, description="Generation latency in ms")


class HealthStatusSchema(BaseModel):
    """Response schema for provider health check."""

    available: bool = Field(..., description="Whether the provider is available")
    provider: str = Field(..., description="Provider name")
    latency_ms: Optional[float] = Field(None, description="Health check latency in ms")
    models_available: int = Field(0, description="Number of available models")
    error: Optional[str] = Field(None, description="Error message if unavailable")


class ModelInfoSchema(BaseModel):
    """Response schema for model information."""

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Human-readable model name")
    description: str = Field("", description="Model description")
    max_tokens: int = Field(4096, description="Maximum context length")
    supports_streaming: bool = Field(True, description="Whether streaming is supported")
    supports_system_prompt: bool = Field(True, description="Whether system prompts are supported")