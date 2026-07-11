# ADR-003: AI Provider Abstraction Layer

## Status

Accepted

## Context

Multimax AI Hub must support multiple AI models from different providers:
- Local: Ollama (Qwen, DeepSeek, Llama, Mistral, Gemma, Phi)
- Cloud: OpenAI, Anthropic, Google, OpenRouter

Users should be able to connect their own API keys, and the AI Router should
intelligently select the best model for a given task. The system must work
without paid APIs, but also allow advanced users to bring their own keys.

## Decision

We will implement an **AI Provider Abstraction Layer** with the following structure:

1. **AIProviderInterface**: Abstract base class defining `chat()`, `chat_stream()`,
   `get_models()`, `is_available()`
2. **Concrete Providers**: One class per provider (OllamaProvider, OpenAIProvider,
   AnthropicProvider, etc.) implementing the interface
3. **Provider Registry**: A central registry that discovers connected providers
   and routes requests to the appropriate one
4. **AI Router**: A smart router that selects the best provider/model based on:
   - Task type (coding, reasoning, writing, vision, etc.)
   - User preference (manual override)
   - Provider availability
   - Cost (prefer free/local when possible)

```python
class AIProviderInterface(ABC):
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse: ...
    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator: ...
    @abstractmethod
    async def get_models(self) -> List[ModelInfo]: ...
    @abstractmethod
    async def is_available(self) -> bool: ...
```

## Consequences

- Positive: Users can switch between providers seamlessly
- Positive: New providers can be added without changing existing code
- Positive: AI Router provides intelligent defaults while allowing manual override
- Positive: Works offline with local models, extends to cloud with API keys
- Negative: Abstraction may limit access to provider-specific features
- Negative: Streaming requires careful handling across different provider formats
- Neutral: Router logic will evolve as more models are added