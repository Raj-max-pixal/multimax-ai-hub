"""
AI Provider Implementations.

Each provider module implements the BaseProvider interface for a specific
AI model service. Currently all providers return placeholder responses;
real API integration will be added in a later milestone.

Available providers:
    - GeminiProvider (Google Gemini)
    - OllamaProvider (Local Ollama)
    - OpenAIProvider (OpenAI-compatible APIs)
    - QwenProvider (Alibaba Qwen)
"""

from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAIProvider
from app.ai.providers.qwen import QwenProvider

__all__ = [
    "GeminiProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "QwenProvider",
]