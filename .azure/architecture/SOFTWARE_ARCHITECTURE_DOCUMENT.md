# MULTIMAX AI HUB — Software Architecture Document (SAD)

> **Document Version:** 0.1.0  
> **Status:** Draft  
> **Classification:** Internal — Multimax  
> **Author:** Principal Software Architect, Multimax  
> **Last Updated:** 2026-07-11

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Core Architectural Principles](#3-core-architectural-principles)
4. [Module Architecture & Plugin System](#4-module-architecture--plugin-system)
5. [AI Router Architecture](#5-ai-router-architecture)
6. [Agent Architecture](#6-agent-architecture)
7. [Service Architecture](#7-service-architecture)
8. [Database Architecture](#8-database-architecture)
9. [Authentication & Authorization Architecture](#9-authentication--authorization-architecture)
10. [Event System & Message Bus](#10-event-system--message-bus)
11. [Queue System & Async Processing](#11-queue-system--async-processing)
12. [Cache Architecture](#12-cache-architecture)
13. [Storage Architecture](#13-storage-architecture)
14. [Security Architecture](#14-security-architecture)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Frontend Architecture](#16-frontend-architecture)
17. [API Design & Versioning](#17-api-design--versioning)
18. [Monitoring, Observability & Logging](#18-monitoring-observability--logging)
19. [Testing Strategy](#19-testing-strategy)
20. [Scalability & Future-Proofing](#20-scalability--future-proofing)
21. [Technology Stack & Rationale](#21-technology-stack--rationale)
22. [5-Year Product Roadmap](#22-5-year-product-roadmap)
23. [Risk Register & Mitigation](#23-risk-register--mitigation)
24. [Appendices](#24-appendices)

---

## 1. EXECUTIVE SUMMARY

Multimax AI Hub is an **AI Operating System** — a unified platform that aggregates and orchestrates the world's best open-source AI technologies into a single, extensible, self-hostable application. It is **not a chatbot**. It is a **platform** upon which any AI capability can be installed, configured, and composed.

### 1.1 Core Mission

> Build the world's most powerful free AI Operating System by combining the best open-source AI technologies into one unified platform.

### 1.2 Architectural Mandate

| Requirement | Implication |
|-------------|-------------|
| Modularity | Every feature is an independent module. No tight coupling between modules. Modules can be installed/uninstalled without affecting others. |
| Plugin-First | Everything — models, agents, tools, search providers, voice engines — is a plugin. The core is a thin kernel. |
| Provider Abstraction | The AI Router decouples all consumers from model providers. No code outside the router knows which provider is being used. |
| Zero Budget | Open source, self-hosted, free tiers. Only pay for what absolutely cannot be done for free. |
| Millions of Users | Stateless services, horizontal scaling, caching, async processing, CDN distribution. |
| Enterprise Ready | SSO, RBAC, audit logs, compliance, multi-tenancy, isolation. |

### 1.3 Architectural Style

**Hexagonal Architecture (Ports & Adapters)** combined with **Microkernel Architecture**:
- The **core kernel** provides: identity, routing, event bus, plugin registry, storage abstraction, security.
- Everything else is a **module** or **plugin** that connects via well-defined ports (interfaces).
- Modules communicate through the **event bus**, not through direct calls.
- AI providers are **adapters** behind the **AI Router port**.

---

## 2. SYSTEM ARCHITECTURE OVERVIEW

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Web    │  │  Mobile  │  │   CLI    │  │   API    │  │   SDK    │ │
│  │  (React) │  │ (Flutter)│  │ (Python) │  │ (REST)   │  │ (JS/TS)  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
└───────┼──────────────┼──────────────┼──────────────┼──────────────┼─────┘
        │              │              │              │              │
        ▼              ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / REVERSE PROXY                        │
│                    (nginx / Cloudflare / Traefik)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │   Rate Limit │  │   Auth       │  │   Load Bal   │  │   WAF       ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER (FastAPI)                      │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        CORE KERNEL                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │   │
│  │  │ Plugin   │ │  Event   │ │   AI     │ │   Identity &     │   │   │
│  │  │ Registry │ │   Bus    │ │  Router  │ │   Security       │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────┐│
│  │Chat     │ │Coding   │ │Research │ │Agents   │ │Docs     │ │Voice ││
│  │Module   │ │Module   │ │Module   │ │Module   │ │Module   │ │Module││
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └──┬───┘│
│       │           │           │           │           │          │    │
│  ┌────▼───────────▼───────────▼───────────▼───────────▼──────────▼───┐│
│  │                      SERVICE LAYER                                ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ││
│  │  │Storage   │ │Search    │ │Vector    │ │Document  │ │Memory  │ ││
│  │  │Svc      │ │Svc      │ │Svc      │ │Svc     │ │Svc    │ ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ ││
│  └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │PostgreSQL│  │  Redis   │  │ ChromaDB │  │   S3     │  │  Rabbit  │ │
│  │          │  │  Cache   │  │ /Qdrant  │  │ Storage  │  │   MQ     │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    AI PROVIDER LAYER                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Ollama  │  │OpenRouter│  │  OpenAI  │  │ Anthropic│  │  Gemini  │ │
│  │ (Local)  │  │ (Cloud)  │  │(BYOK)    │  │ (BYOK)   │  │ (BYOK)   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Layer Responsibilities

| Layer | Responsibility | Technologies |
|-------|---------------|--------------|
| **Client Layer** | UI rendering, user interaction, local state | React, Next.js, Tailwind, Flutter (future) |
| **API Gateway** | Reverse proxy, rate limiting, auth, TLS, WAF, load balancing | nginx, Cloudflare, Traefik |
| **Core Kernel** | Plugin registry, event bus, AI router, identity, security | FastAPI, Python |
| **Module Layer** | Business capabilities (chat, coding, agents, etc.) | FastAPI Routers, installed as plugins |
| **Service Layer** | Shared infrastructure services (storage, search, vector, memory) | Python services, stateless |
| **Infrastructure** | Data persistence, caching, messaging, search indexes | PostgreSQL, Redis, ChromaDB, RabbitMQ |
| **AI Provider Layer** | Model inference providers (local/cloud) | Ollama, OpenRouter, OpenAI, Anthropic, etc. |

---

## 3. CORE ARCHITECTURAL PRINCIPLES

### 3.1 The Laws of Multimax Architecture

These principles are **non-negotiable**. Every architectural decision must be evaluated against them.

#### Law 1: Modular Independence
> Every module must be independently installable, uninstallable, and replaceable without affecting any other module.

**Enforcement:**
- Modules communicate exclusively through the event bus or defined service interfaces.
- No module may import another module's internals.
- Each module has its own database schema (schema-per-module or table prefix).
- Module manifests declare dependencies, permissions, and capabilities.

#### Law 2: Provider Abstraction
> No code outside the AI Router may know which AI provider is being used.

**Enforcement:**
- All AI interactions go through `ai_router.chat()`, `ai_router.embed()`, etc.
- The router returns a standard `AIResponse` object regardless of provider.
- Provider-specific features (e.g., tool usage) are exposed through standardized capabilities.

#### Law 3: Plugin-First Everything
> Every capability in the system — including models, agents, search engines, voice services, storage backends — must be a plugin.

**Enforcement:**
- The core contains only: plugin registry, event bus, identity, storage abstraction, AI router interface.
- Everything else is a plugin with a manifest, version, and lifecycle hooks.
- Plugins are discoverable, installable, and removable at runtime (or at container restart).

#### Law 4: Data Sovereignty
> User data belongs to the user. The system is just a custodian.

**Enforcement:**
- All user data is encrypted at rest and in transit.
- Users can export all their data at any time.
- Users can delete all their data permanently.
- Self-hosted instances have zero telemetry by default.

#### Law 5: Eventual Consistency First
> The system must work correctly even when components are temporarily unavailable.

**Enforcement:**
- All cross-module communication is asynchronous by default.
- The event bus guarantees at-least-once delivery.
- Modules are designed to handle delayed or out-of-order events.

#### Law 6: Scale-Out Architecture
> Every component must be horizontally scalable.

**Enforcement:**
- All application services are stateless.
- State lives in PostgreSQL, Redis, or object storage.
- Vector databases support replication and sharding.
- The event bus supports consumer groups.

#### Law 7: Zero-Lock-In
> No dependency that cannot be replaced without rewriting the system.

**Enforcement:**
- All external services are behind abstraction layers.
- Database access is through repositories, not raw queries scattered everywhere.
- AI providers are behind the AI Router.
- Storage is behind a storage interface (local, S3, Supabase).

---

## 4. MODULE ARCHITECTURE & PLUGIN SYSTEM

### 4.1 Module Definition

A **Module** is an independently deployable unit of functionality. Each module:

- Has a unique identifier (e.g., `multimax.chat`, `multimax.coding`)
- Declares its version, dependencies, and permissions in a `module.yaml` manifest
- Has its own database schemas (with namespace prefix)
- Registers event handlers
- Exposes API routes (optionally)
- Registers services with the service mesh
- Can be enabled/disabled without code changes

### 4.2 Module Manifest (`module.yaml`)

```yaml
# Example: modules/chat/module.yaml
id: multimax.chat
name: AI Chat
version: 1.0.0
description: Conversational AI chat with streaming, markdown, and file support
author: Multimax
license: MIT

dependencies:
  - multimax.ai-router >= 1.0.0
  - multimax.storage >= 0.5.0

permissions:
  - ai:chat
  - storage:read
  - storage:write
  - events:publish:message.created
  - events:subscribe:message.deleted

routes:
  prefix: /api/v1/chat
  openapi: ./openapi.yaml

database:
  migrations: ./migrations/
  schemas:
    - prefix: chat_

events:
  publishes:
    - message.created
    - conversation.created
    - conversation.deleted
  subscribes:
    - user.deleted
    - module.uninstalling

lifecycle:
  on_install: ./scripts/install.py
  on_uninstall: ./scripts/uninstall.py
  on_enable: ./scripts/enable.py
  on_disable: ./scripts/disable.py
```

### 4.3 Plugin System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PLUGIN REGISTRY                                │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │  Plugin  │  │  Plugin  │  │  Plugin  │  │  Plugin Discovery  │ │
│  │  Manager │  │  Loader  │  │  Sandbox │  │  (Local + Remote)  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────────┬──────────┘ │
│       │              │              │                  │            │
│       ▼              ▼              ▼                  ▼            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PLUGIN STORE                              │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │  SQLAlchemy Models: plugin, plugin_version,            │  │   │
│  │  │  plugin_config, plugin_dependency                      │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 Plugin Types

| Plugin Type | Description | Examples |
|-------------|-------------|----------|
| **AI Provider** | Adds a model provider | OllamaPlugin, OpenRouterPlugin, AnthropicPlugin |
| **Agent Tool** | Adds a capability for AI agents | BrowserTool, CalculatorTool, WebSearchTool |
| **Storage Backend** | Adds a storage provider | S3Plugin, LocalStoragePlugin, SupabaseStoragePlugin |
| **Search Provider** | Adds a search engine | SearXNGPlugin, WebSearchPlugin, AcademicSearchPlugin |
| **Voice Provider** | Adds speech-to-text or text-to-speech | WhisperPlugin, ElevenLabsPlugin |
| **Image Provider** | Adds image generation/editing | StableDiffusionPlugin, ComfyUIPlugin |
| **Vector Provider** | Adds vector database support | ChromaDBPlugin, QdrantPlugin, PineconePlugin |
| **Auth Provider** | Adds authentication methods | SupabaseAuthPlugin, BetterAuthPlugin, LDAPAuthPlugin |
| **UI Extension** | Adds frontend components | ChatUIPlugin, CodingUIPlugin |
| **Workflow Node** | Adds automation nodes | EmailNodePlugin, SlackNodePlugin |

### 4.5 Plugin Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Discover │───▶│ Install  │───▶│ Configure│───▶│  Enable  │───▶│  Active  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                                    │
                                                                    ▼
                                          ┌──────────┐    ┌──────────┐
                                          │ Disabled │◀───│ Disable  │
                                          └──────────┘    └──────────┘
                                                │
                                                ▼
                                          ┌──────────┐
                                          │Uninstall │
                                          └──────────┘
```

### 4.6 Module Isolation Strategy

| Isolation Mechanism | Description |
|---------------------|-------------|
| **Schema-per-Module** | Each module uses PostgreSQL schema namespacing (e.g., `chat_`, `coding_`) |
| **Separate Processes** | Heavy modules can run as separate microservices |
| **Plugin Sandbox** | Python plugins run in restricted execution context with limited syscalls |
| **Resource Limits** | CPU/memory quotas via cgroups (Docker) or Kubernetes limits |
| **Rate Limits** | Per-module rate limiting via API gateway |

---

## 5. AI ROUTER ARCHITECTURE

### 5.1 The Core Abstraction

The AI Router is the **single most important architectural component**. It decouples all AI consumers from the specific model providers. No code outside the router knows which model or provider is being used.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Consumer Code (Chat Module, Coding Module, Agent, etc.)               │
│                                                                         │
│  await ai_router.chat(request: ChatRequest) → AIResponse               │
│  await ai_router.embed(text: str) → Embedding                          │
│  await ai_router.stream(request: ChatRequest) → AsyncIterator[Chunk]   │
│  await ai_router.tool_call(request: ToolRequest) → ToolResponse        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI ROUTER                                       │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     Routing Strategy Engine                       │ │
│  │                                                                   │ │
│  │  • Default routing (model → task type mapping)                    │ │
│  │  • Manual override (user selects model)                           │ │
│  │  • Cost-aware routing (pick cheapest capable)                     │ │
│  │  • Latency-aware routing (pick fastest)                           │ │
│  │  • Load-balanced routing (round-robin across providers)           │ │
│  │  • Fallback routing (retry on secondary if primary fails)         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    Provider Registry                               │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │ │
│  │  │ Ollama   │  │ Open     │  │ OpenAI   │  │ Anthropic│  ...    │ │
│  │  │Provider  │  │Router    │  │Provider  │  │Provider  │        │ │
│  │  │          │  │Provider  │  │          │  │          │        │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    Provider Interface (Abstract Base)              │ │
│  │                                                                   │ │
│  │  class AIProvider(ABC):                                           │ │
│  │      @abstractmethod                                              │ │
│  │      async def chat(self, request: ChatRequest) -> AIResponse     │ │
│  │      @abstractmethod                                              │ │
│  │      async def stream(self, request: ChatRequest) -> AsyncIter... │ │
│  │      @abstractmethod                                              │ │
│  │      async def embed(self, text: str) -> Embedding                │ │
│  │      @abstractmethod                                              │ │
│  │      def get_capabilities(self) -> ProviderCapabilities           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Provider Interface

```python
# app/ai_router/provider_interface.py

class ModelCapability(enum.Enum):
    CHAT = "chat"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    EMBEDDINGS = "embeddings"
    CODE = "code"
    REASONING = "reasoning"
    TOOL_USE = "tool_use"
    JSON_MODE = "json_mode"
    SYSTEM_PROMPT = "system_prompt"

class ProviderCapabilities(BaseModel):
    model: str
    capabilities: set[ModelCapability]
    context_window: int
    max_output_tokens: int
    pricing_per_1k_input: float = 0.0
    pricing_per_1k_output: float = 0.0
    latency_p50_ms: float
    is_available: bool

class ChatRequest(BaseModel):
    messages: list[Message]
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[list[ToolDefinition]] = None
    stream: bool = False

class AIResponse(BaseModel):
    id: str
    model: str
    provider: str
    content: str
    finish_reason: str
    usage: Optional[TokenUsage] = None
    tool_calls: Optional[list[ToolCall]] = None

class AIProvider(ABC):
    @abstractmethod
    async def chat(self, request: ChatRequest) -> AIResponse: ...
    
    @abstractmethod
    def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]: ...
    
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[Embedding]: ...
    
    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities: ...
    
    @abstractmethod
    def get_models(self) -> list[ModelInfo]: ...
```

### 5.3 Routing Strategy Engine

The routing engine uses a **strategy pattern** to determine which model/provider to use for each request.

```python
# app/ai_router/strategies.py

class RoutingStrategy(ABC):
    @abstractmethod
    async def select(self, request: RoutingRequest, 
                     available: list[ProviderCapabilities]) -> ProviderCapabilities: ...

class DefaultStrategy(RoutingStrategy):
    """Route based on task type → model mapping"""
    MODEL_MAP = {
        "coding": ["deepseek-coder", "qwen2.5-coder"],
        "reasoning": ["qwen3", "deepseek-r1"],
        "writing": ["llama3", "mistral"],
        "vision": ["qwen-vl", "llava"],
        "chat": ["phi4", "llama3"],
        "embedding": ["all-MiniLM-L6-v2"],
    }
    
class CostOptimizedStrategy(RoutingStrategy):
    """Pick cheapest provider that meets capability requirements"""
    
class LatencyOptimizedStrategy(RoutingStrategy):
    """Pick provider with lowest latency"""
    
class LoadBalancedStrategy(RoutingStrategy):
    """Round-robin across eligible providers"""
    
class FallbackStrategy(RoutingStrategy):
    """Try primary, fallback to secondary if unavailable"""
```

### 5.4 Default Model Routing Map

The default router automatically selects the best model for a task. Users can override.

| Task Type | Default Model | Reasoning |
|-----------|---------------|-----------|
| Coding | DeepSeek (qwen2.5-coder if local) | Best code generation, understands context |
| Reasoning / Math | Qwen 3 | Strong reasoning capabilities |
| Writing / Content | Llama 3 | Creative, follows instructions well |
| Vision | Qwen Vision / LLaVA | Multimodal understanding |
| Chat / General | Phi-4 or Llama 3 | Fast, efficient for general conversation |
| Embeddings | all-MiniLM-L6-v2 | Fast, good quality, runs locally |
| Image Generation | Stable Diffusion / SDXL | Open-source image generation |
| Summarization | Mistral | Efficient, good at extraction |

### 5.5 Provider Configuration

```yaml
# config/providers.yaml
providers:
  ollama:
    enabled: true
    base_url: http://ollama:11434
    default_model: phi4:latest
    models:
      - phi4:latest
      - llama3:latest
      - qwen3:4b
      - deepseek-coder:latest
  
  openrouter:
    enabled: false
    api_key: ${OPENROUTER_API_KEY}
    default_model: openai/gpt-4o
    
  openai:
    enabled: false
    api_key: ${OPENAI_API_KEY}
    default_model: gpt-4o-mini
```

### 5.6 Model Capability Registry

The router maintains a registry of model capabilities so it can make intelligent routing decisions.

```
┌──────────────────────────────────────────────────────────────┐
│                    MODEL REGISTRY                            │
├───────────────┬──────────┬──────────┬──────────┬────────────┤
│ Model         │ Capabilities         │ Context  │ Cost/1K   │
├───────────────┼──────────┼──────────┼──────────┼────────────┤
│ phi4:latest   │ chat, stream, code    │ 128K     │ $0.00     │
│ llama3:latest │ chat, stream, code,   │ 128K     │ $0.00     │
│               │ function_calling      │          │           │
│ deepseek-     │ chat, stream, code,   │ 128K     │ $0.00     │
│ coder:latest  │ reasoning, vision     │          │           │
│ qwen3:4b      │ chat, stream,         │ 128K     │ $0.00     │
│               │ reasoning             │          │           │
│ gpt-4o-mini   │ chat, stream, vision, │ 128K     │ $0.150    │
│               │ function_calling,     │          │           │
│               │ json_mode             │          │           │
│ claude-3-     │ chat, stream, vision, │ 200K     │ $0.250    │
│ sonnet        │ function_calling      │          │           │
└───────────────┴──────────────────────────────────────────────┘
```

---

## 6. AGENT ARCHITECTURE

### 6.1 Agent System Overview

Agents are autonomous or semi-autonomous programs that use AI models to accomplish tasks. The agent system is built on top of the AI Router and the Plugin System.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT SYSTEM                                    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Agent Runtime                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │   │
│  │  │ Execution │ │ Memory   │ │ Planning │ │ Tool Resolution  │   │   │
│  │  │ Engine    │ │ Manager  │ │ Engine   │ │ & Invocation     │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Agent Registry                              │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │   │
│  │  │Browser │  │Research│  │Coding  │  │Data    │  │Custom  │ ...│   │
│  │  │Agent   │  │Agent   │  │Agent   │  │Agent   │  │Agent   │    │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Tool Registry                                │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │   │
│  │  │Web      │ │Browser  │ │File     │ │Database │ │API      │...  │   │
│  │  │Search   │ │Control  │ │Ops      │ │Query    │ │Call     │    │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Agent Definition

```yaml
# agents/browser-agent/agent.yaml
id: multimax.agent.browser
name: Browser Agent
version: 1.0.0
description: Controls a browser to perform web-based tasks
model: qwen3:4b  # Default model, can be overridden
max_iterations: 50
timeout_seconds: 300

tools:
  - multimax.tool.browser.navigate
  - multimax.tool.browser.click
  - multimax.tool.browser.type
  - multimax.tool.browser.screenshot
  - multimax.tool.browser.extract
  - multimax.tool.search.web

memory:
  type: conversation
  ttl_days: 7

permissions:
  - network:http
  - browser:control
  - storage:read
```

### 6.3 Agent Execution Flow

```
User Request
    │
    ▼
┌──────────────────┐
│  Planning Engine │──▶ Break down into sub-tasks
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Tool Resolution │──▶ Find available tools for each sub-task
└──────┬───────────┘
       │
       ▼
┌──────────────────┐     ┌──────────────────┐
│  Execution       │────▶│  AI Router       │──▶ Model generates next action
│  Engine          │     └──────────────────┘
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Tool Invocation │──▶ Execute the chosen tool
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Result          │──▶ Feed result back to model, continue or finish
│  Processing      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Memory Update   │──▶ Store relevant information
└──────────────────┘
```

### 6.4 Multi-Agent System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR AGENT                                 │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Receives complex tasks, delegates to specialized agents         │   │
│  │  Coordinates results, handles conflicts                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Research Agent  │ │  Coding Agent    │ │  Browser Agent   │
│  (Web Search,    │ │  (Code Gen,      │ │  (Web Tasks,     │
│   Fact Check)    │ │  Debug, Review)  │ │  Data Extraction)│
└──────────────────┘ └──────────────────┘ └──────────────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      RESULT AGGREGATOR                                  │
│  Combines results, resolves conflicts, generates final answer           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. SERVICE ARCHITECTURE

### 7.1 Services Overview

Services are the shared infrastructure that modules and agents use. They are stateless and horizontally scalable.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                                     │
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Identity │  │ Storage  │  │ Vector   │  │ Search   │  │ Document │ │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │  │ Service  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Memory  │  │  Task    │  │ Workflow │  │  Cache   │  │  Audit   │ │
│  │  Service │  │  Queue   │  │ Service  │  │  Service │  │  Service │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Service Definitions

| Service | Responsibility | Storage | Scaling |
|---------|---------------|---------|---------|
| **Identity Service** | Auth, users, organizations, roles, permissions | PostgreSQL | Horizontal |
| **Storage Service** | File storage abstraction (local, S3, Supabase) | S3/Local | Horizontal |
| **Vector Service** | Vector embeddings storage and search | ChromaDB/Qdrant | Horizontal |
| **Search Service** | Full-text, web, academic search aggregation | PostgreSQL + External APIs | Horizontal |
| **Document Service** | Document parsing, OCR, format conversion | Stateless | Horizontal |
| **Memory Service** | Long-term memory, knowledge graphs, user preferences | PostgreSQL + Vector DB | Horizontal |
| **Task Queue Service** | Async job management, scheduling, retries | Redis/RabbitMQ | Horizontal |
| **Workflow Service** | Visual workflow builder and execution engine | PostgreSQL + Redis | Horizontal |
| **Cache Service** | Distributed caching layer | Redis | Horizontal |
| **Audit Service** | Immutable audit log for all actions | PostgreSQL (append-only) | Horizontal |

---

## 8. DATABASE ARCHITECTURE

### 8.1 Multi-Tenant Database Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATABASE ARCHITECTURE                              │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL (Primary)                          │   │
│  │                                                                  │   │
│  │  ┌────────────────────┐  ┌────────────────────┐                 │   │
│  │  │   Public Schema    │  │   Module Schemas   │                 │   │
│  │  │                    │  │                    │                 │   │
│  │  │  • users           │  │  • chat_convos     │                 │   │
│  │  │  • organizations   │  │  • chat_messages   │                 │   │
│  │  │  • api_keys        │  │  • coding_sessions │                 │   │
│  │  │  • audit_log       │  │  • agents          │                 │   │
│  │  │  • plugins         │  │  • agent_runs      │                 │   │
│  │  │  • plugin_configs  │  │  • docs_knowledge  │                 │   │
│  │  │  • settings        │  │  • voice_recordings│                 │   │
│  │  └────────────────────┘  └────────────────────┘                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Redis (Cache + Queue)                         │   │
│  │                                                                  │   │
│  │  • Session cache         • Rate limit counters                  │   │
│  │  • API response cache    • Task queue (RQ/Celery)               │   │
│  │  • Model capabilities    • Event bus (Pub/Sub)                  │   │
│  │  • Streaming tokens       • User presence                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │            ChromaDB / Qdrant (Vector Database)                   │   │
│  │                                                                  │   │
│  │  • Document embeddings          • User memory vectors            │   │
│  │  • Knowledge base               • Semantic search index          │   │
│  │  • Agent context vectors         • Plugin metadata embeddings    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Core Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
│    User      │       │  Organization    │       │    Plugin        │
├──────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)      │       │ id (PK)          │       │ id (PK)          │
│ email        │──────▶│ name             │       │ name             │
│ password_hash│       │ slug             │       │ version          │
│ display_name │       │ owner_id (FK)    │       │ enabled          │
│ avatar_url   │       │ created_at       │       │ config (JSON)    │
│ created_at   │       └──────────────────┘       │ type             │
└──────┬───────┘              │                    └──────────────────┘
       │                      │
       │                      ▼
       │              ┌──────────────────┐
       │              │ Organization     │
       │              │ Member           │
       │              ├──────────────────┤
       │              │ id (PK)          │
       │              │ org_id (FK)      │
       │              │ user_id (FK)     │
       │              │ role             │
       └─────────────▶│ joined_at        │
                      └──────────────────┘

┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  Conversation    │       │    Message       │       │   ApiKey         │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │       │ id (PK)          │
│ user_id (FK)     │──────▶│ conversation_id  │       │ user_id (FK)     │
│ title            │       │ role             │       │ key_hash         │
│ model            │       │ content (text)   │       │ name             │
│ folder_id (FK)   │       │ tokens_used      │       │ last_used_at     │
│ pinned           │       │ metadata (JSON)  │       │ expires_at       │
│ created_at       │       │ created_at       │       └──────────────────┘
│ updated_at       │       └──────────────────┘
└──────────────────┘

┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Document       │       │  KnowledgeBase   │       │   Agent          │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │       │ id (PK)          │
│ user_id (FK)     │       │ user_id (FK)     │       │ user_id (FK)     │
│ filename         │       │ name             │       │ name             │
│ file_type        │       │ description      │       │ model            │
│ file_size        │       │ embedding_config │       │ system_prompt    │
│ storage_path     │       │ created_at       │       │ tools (JSON)     │
│ chunk_count      │       └──────────────────┘       │ max_iterations   │
│ created_at       │                                   │ created_at       │
└──────────────────┘                                   └──────────────────┘
```

### 8.3 Database Selection Rationale

**PostgreSQL** (over MySQL, SQLite, MSSQL):
- **Why not MySQL?** PostgreSQL has better JSON support, full-text search, array types, and concurrent read/write performance. It also has native UUID support, which is critical for distributed systems.
- **Why not SQLite?** SQLite doesn't support concurrent writes, which is necessary for multi-user scenarios.
- **Why not MSSQL?** Proprietary, expensive, runs primarily on Windows.
- **PostgreSQL advantage**: PGVector extension for vector search, PostGIS for geospatial, logical replication, excellent extension ecosystem.

**Redis** (over Memcached, Dragonfly):
- **Why not Memcached?** Memcached is only key-value cache. Redis provides pub/sub, streams, sorted sets, and persistence — all needed for the event bus and queue.
- **Why not Dragonfly?** Dragonfly is interesting but less mature and has a smaller community. Redis is more battle-tested.
- **Redis advantage**: Single dependency provides cache, queue, event bus, session store, and rate limiter.

**ChromaDB** (over Qdrant, Pinecone, Weaviate):
- **Why ChromaDB?** Open source (Apache 2.0), self-hostable, lightweight, Python-native, no external dependencies for basic operation. Perfect for zero-budget start.
- **When to upgrade?** When collections exceed 1M vectors or when high availability is needed, migrate to Qdrant (also open source, better performance).
- **Why not Pinecone?** Proprietary, expensive at scale. However, we support it as a plugin for users who want managed vector DB.

---

## 9. AUTHENTICATION & AUTHORIZATION ARCHITECTURE

### 9.1 Authentication Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION ARCHITECTURE                          │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  Better Auth     │    │  Supabase Auth   │    │  OAuth (Future)  │  │
│  │  (Primary,       │    │  (Alternative    │    │                  │  │
│  │   Self-Hosted)   │    │   Cloud Option)  │    │  • Google        │  │
│  └────────┬─────────┘    └────────┬─────────┘    │  • GitHub        │  │
│           │                       │              │  • Microsoft     │  │
│           │                       │              │  • SSO/SAML      │  │
│           │                       │              └──────────────────┘  │
│           └───────────┬───────────┘                                     │
│                       ▼                                                │
│           ┌──────────────────────┐                                     │
│           │  Auth Abstraction   │                                     │
│           │  Layer (Interface)  │                                     │
│           └──────────┬──────────┘                                     │
│                      ▼                                                │
│           ┌──────────────────────┐                                     │
│           │  JWT Token Service  │                                     │
│           │  (Access + Refresh) │                                     │
│           └──────────┬──────────┘                                     │
│                      ▼                                                │
│           ┌──────────────────────┐                                     │
│           │  Session Store      │                                     │
│           │  (Redis + PostgreSQL)│                                     │
│           └──────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Token Strategy

| Token Type | Lifetime | Storage | Purpose |
|------------|----------|---------|---------|
| Access Token (JWT) | 15 minutes | Memory / httpOnly cookie | API authorization |
| Refresh Token | 7 days | Redis + PostgreSQL | Obtain new access tokens |
| API Key | Per-user config | Hashed in PostgreSQL | Programmatic access |
| Session Token | Browser session | Redis | Web UI sessions |

### 9.3 Authorization Model (RBAC)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    User      │────▶│    Role      │────▶│  Permission  │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                      │
       │                    ▼                      │
       │           ┌──────────────┐               │
       │           │ Organization │               │
       │           │ Member       │───────┐       │
       │           └──────────────┘       │       │
       │                                  ▼       ▼
       │                          ┌──────────────────────┐
       └─────────────────────────▶│  Permission Check    │
                                  │  Middleware          │
                                  └──────────────────────┘
```

**Default Roles:**
| Role | Scope | Permissions |
|------|-------|-------------|
| `owner` | Organization | Full access, billing, member management, delete org |
| `admin` | Organization | Manage members, settings, all modules |
| `member` | Organization | Use modules, create agents, manage own data |
| `viewer` | Organization | Read-only access to shared resources |
| `user` | Personal | Single user, no organization |

**Permission Example:**
```python
# app/security/permissions.py
class Permission(str, Enum):
    # Chat
    CHAT_CREATE = "chat:create"
    CHAT_READ = "chat:read"
    CHAT_DELETE = "chat:delete"
    CHAT_SHARE = "chat:share"
    
    # Storage
    STORAGE_READ = "storage:read"
    STORAGE_WRITE = "storage:write"
    STORAGE_DELETE = "storage:delete"
    
    # Admin
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_PLUGINS = "admin:plugins"
    ADMIN_BILLING = "admin:billing"
```

### 9.4 Auth Provider Selection Rationale

**Why Better Auth as Primary?**
- **Free and open source** (MIT license)
- **Self-hostable** — no dependency on external auth services
- **No usage limits** — unlimited users, unlimited requests
- **Full control** — customize flows, add hooks, extend providers
- **TypeScript-native** — excellent DX for the frontend team
- **Supports**: email/password, OAuth (Google, GitHub, Discord), magic links, passkeys

**Why Supabase Auth as Alternative?**
- If the team wants to minimize backend work, Supabase Auth is a good managed option
- Free tier includes 50,000 users and 500,000 monthly active users
- Downside: vendor lock-in, usage limits on free tier

**Decision**: Start with **Better Auth** for self-hosted instances. Provide Supabase Auth as a configurable plugin for teams that want managed auth.

---

## 10. EVENT SYSTEM & MESSAGE BUS

### 10.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EVENT BUS                                          │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Event Router                                  │   │
│  │                                                                  │   │
│  │  • Topic-based routing (chat.created, agent.completed, etc.)    │   │
│  │  • Fan-out (one event, multiple subscribers)                    │   │
│  │  • Delayed delivery (for retries)                               │   │
│  │  • Dead letter queue (for failed events)                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Module  │  │  Module  │  │  Agent   │  │ Workflow │  │  Audit   │ │
│  │  A Pub   │  │  B Sub   │  │  Pub     │  │  Sub     │  │  Sub     │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Event Types

```python
# app/events/events.py

class EventCategory(str, Enum):
    CHAT = "chat"
    AGENT = "agent"
    DOCUMENT = "document"
    USER = "user"
    MODULE = "module"
    WORKFLOW = "workflow"
    SYSTEM = "system"

# Core Events
class CoreEvents:
    # User events
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    
    # Chat events
    MESSAGE_CREATED = "message.created"
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_SHARED = "conversation.shared"
    
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_TOOL_CALL = "agent.tool.call"
    
    # Document events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_DELETED = "document.deleted"
    
    # Module events
    MODULE_INSTALLED = "module.installed"
    MODULE_UNINSTALLED = "module.uninstalled"
    MODULE_ENABLED = "module.enabled"
    MODULE_DISABLED = "module.disabled"
    
    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
```

### 10.3 Event Flow Example

```python
# When a user sends a message in chat:
# 1. Chat module publishes "message.created"
# 2. Multiple subscribers react:

# Subscriber 1: AI Router processes message and generates response
@event_bus.subscribe("message.created")
async def on_message_created(event: Event):
    response = await ai_router.chat(event.data)
    await chat_service.add_message(conversation_id, response)
    
# Subscriber 2: Memory service stores interaction
@event_bus.subscribe("message.created")
async def update_memory(event: Event):
    await memory_service.store_interaction(event.data)
    
# Subscriber 3: Audit service logs the event
@event_bus.subscribe("message.created")
async def audit_log(event: Event):
    await audit_service.log("message.created", event.data)
    
# Subscriber 4: Real-time WebSocket broadcast
@event_bus.subscribe("message.created")
async def broadcast_to_clients(event: Event):
    await ws_manager.broadcast(conversation_id, event.data)
```

### 10.4 Event Bus Implementation Strategy

| Stage | Implementation | Why |
|-------|---------------|-----|
| **MVP (Phase 0)** | In-process event bus using asyncio | Zero dependencies, works single-process |
| **Growth (Phase 2+)** | Redis Pub/Sub | Lightweight, same Redis dependency needed for cache anyway |
| **Scale (Phase 10+)** | RabbitMQ or Kafka | Durable, persistent, replayable, high-throughput |

---

## 11. QUEUE SYSTEM & ASYNC PROCESSING

### 11.1 Queue Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TASK QUEUE                                         │
│                                                                         │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐ │
│  │  Document        │     │  Embedding       │     │  Research        │ │
│  │  Processing      │     │  Generation      │     │  Deep Search     │ │
│  │  Queue           │────▶│  Queue           │────▶│  Queue           │ │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘ │
│         │                        │                        │             │
│         │                        │                        │             │
│         ▼                        ▼                        ▼             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Worker Pool                                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker 4 │  ...  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│         │                        │                        │             │
│         ▼                        ▼                        ▼             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Result Store (PostgreSQL)                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Queue Definitions

| Queue Name | Priority | Workers | Retries | Timeout |
|------------|----------|---------|---------|---------|
| `documents.process` | Medium | 4 | 3 | 300s |
| `embeddings.generate` | Low | 2 | 3 | 120s |
| `research.deep` | Low | 2 | 2 | 600s |
| `email.send` | High | 2 | 5 | 30s |
| `agent.execute` | Medium | 4 | 2 | 600s |
| `export.generate` | Low | 2 | 3 | 300s |

### 11.3 Queue Provider Selection

| Stage | Implementation | Why |
|-------|---------------|-----|
| **MVP** | Redis + RQ (Python Redis Queue) | Simple, same Redis, no additional dependency |
| **Growth** | Celery + Redis | More powerful, task scheduling, periodic tasks |
| **Scale** | RabbitMQ + Celery | Durable persistent queues, clustering, high throughput |

---

## 12. CACHE ARCHITECTURE

### 12.1 Caching Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CACHE ARCHITECTURE                                 │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  L1: Browser Cache (CDN)                                       │   │
│  │  • Static assets (JS, CSS, images) → 1 year TTL                │   │
│  │  • API responses with ETag headers                              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  L2: Application Cache (Redis)                                 │   │
│  │  • Model capabilities registry → 1 hour TTL                    │   │
│  │  • User session data → 15 minute TTL                           │   │
│  │  • API response cache (GET only) → 5 minute TTL                │   │
│  │  • Rate limit counters → variable TTL                          │   │
│  │  • Conversation list (metadata) → 1 minute TTL                 │   │
│  │  • Configuration / settings → 10 minute TTL                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  L3: Database Cache (PostgreSQL)                                │   │
│  │  • Query result cache (materialized views)                      │   │
│  │  • Frequent aggregates (dashboard stats, usage metrics)         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Cache Invalidation Strategy

| Strategy | When | How |
|----------|------|-----|
| **TTL-based** | Expiry time reached | Automatic |
| **Write-through** | On data update | Update cache immediately |
| **Event-based** | On related event | Subscribe to event, invalidate |
| **Pattern-based** | On pattern match | Redis SCAN + DEL pattern |

---

## 13. STORAGE ARCHITECTURE

### 13.1 Storage Abstraction Layer

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Consumer Code (No knowledge of underlying storage)                    │
│                                                                         │
│  storage = StorageService()                                             │
│  url = await storage.upload(file, "documents/")                        │
│  content = await storage.download(url)                                  │
│  await storage.delete(url)                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Storage Abstraction Interface                      │
│                                                                         │
│  class StorageBackend(ABC):                                             │
│      @abstractmethod                                                    │
│      async def upload(self, file, path) -> str                          │
│      @abstractmethod                                                    │
│      async def download(self, url) -> bytes                             │
│      @abstractmethod                                                    │
│      async def delete(self, url) -> None                                │
│      @abstractmethod                                                    │
│      async def list(self, prefix) -> list[str]                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ Local Storage │         │     S3        │         │ Supabase      │
│ (Development) │         │ (MinIO/S3)    │         │ Storage       │
│               │         │               │         │ (Free Tier)   │
│ /uploads/     │         │ bucket/       │         │ bucket/       │
└───────────────┘         └───────────────┘         └───────────────┘
```

### 13.2 Storage Strategy by Phase

| Phase | Storage | Rationale |
|-------|---------|-----------|
| **MVP** | Local filesystem | Zero cost, simple, works immediately |
| **Growth** | MinIO (S3-compatible self-hosted) | Horizontal scaling, S3 API compatibility, no vendor lock |
| **Scale** | Cloudflare R2 or Backblaze B2 | Zero egress fees, S3-compatible, affordable |
| **Enterprise** | AWS S3 / Azure Blob / GCS | Enterprise compliance, SLA, global replication |

---

## 14. SECURITY ARCHITECTURE

### 14.1 Security Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SECURITY ARCHITECTURE                              │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  L1: Network Security                                           │   │
│  │  • All traffic over TLS 1.3                                     │   │
│  │  • Internal services on isolated Docker network                 │   │
│  │  • Database ports not exposed externally                        │   │
│  │  • WAF (Web Application Firewall) via Cloudflare or nginx       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  L2: Application Security                                       │   │
│  │  • JWT-based authentication with short-lived tokens              │   │
│  │  • RBAC authorization on every API endpoint                      │   │
│  │  • Input validation on all endpoints (Pydantic schemas)          │   │
│  │  • Rate limiting per user, per IP, per endpoint                  │   │
│  │  • CORS whitelist (configurable)                                 │   │
│  │  • CSP headers (Content Security Policy)                         │   │
│  │  • SQL injection prevention (parameterized queries)              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  L3: Data Security                                              │   │
│  │  • All secrets in environment variables (not in code)            │   │
│  │  • Passwords hashed with bcrypt (cost factor 12)                 │   │
│  │  • API keys hashed before storage (SHA-256)                      │   │
│  │  • Encryption at rest (database-level or column-level)           │   │
│  │  • File upload validation: type, size, content scanning          │   │
│  │  • User data export and deletion (GDPR compliance)               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  L4: Operational Security                                       │   │
│  │  • Least privilege principle for all service accounts            │   │
│  │  • Regular dependency scanning (Dependabot / Snyk)              │   │
│  │  • Audit log for all administrative actions                      │   │
│  │  • Container image scanning                                      │   │
│  │  • Secrets rotation policy                                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 14.2 Security Checklist (Phase 0)

- [ ] Environment variable validation at startup
- [ ] CORS configured for production domains only
- [ ] Rate limiting middleware
- [ ] Request size limits on all endpoints
- [ ] File upload validation (type whitelist, max size)
- [ ] HTTPS enforcement
- [ ] HSTS headers
- [ ] Content Security Policy headers
- [ ] XSS protection headers
- [ ] SQL injection prevention (ORM usage, no raw queries)
- [ ] JWT secret rotation support
- [ ] Audit logging for auth events

---

## 15. DEPLOYMENT ARCHITECTURE

### 15.1 Single-Server Deployment (MVP)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DOCKER HOST (Single VPS)                           │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                        nginx (Reverse Proxy)                     │   │
│  │  • TLS termination    • Static file serving    • Rate limiting   │   │
│  │  • /api/* → backend   • /* → frontend         • WebSocket proxy │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Frontend    │  │   Backend    │  │   Redis      │  │ ChromaDB   │ │
│  │  (nginx)     │  │  (uvicorn)   │  │              │  │            │ │
│  │  :3000       │  │  :8000       │  │  :6379       │  │  :8001     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐                                     │
│  │  PostgreSQL  │  │   Ollama     │                                     │
│  │  :5432       │  │  :11434      │                                     │
│  └──────────────┘  └──────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 15.2 Scaled Deployment (Future)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION (Kubernetes / Docker Swarm)               │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    CDN (Cloudflare)                              │   │
│  │  • Static assets           • DDoS protection                    │   │
│  │  • Edge caching            • WAF                                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Load Balancer                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Frontend    │  │   Backend    │  │   Backend    │  │  Backend   │ │
│  │  Replica 1   │  │  Replica 1   │  │  Replica 2   │  │  Replica N │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  PostgreSQL  │  │  PostgreSQL  │  │   Redis      │  │  Redis     │ │
│  │  Primary     │◀─│  Replica     │  │  Primary     │  │  Replica   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  ChromaDB    │  │  Qdrant      │  │  MinIO (S3)  │                 │
│  │  (Vector)    │  │  (Vector)    │  │  (Storage)   │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### 15.3 Docker Compose Configuration (Phase 0)

```yaml
version: "3.8"

services:
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
    
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis, chromadb]
    volumes: [uploads:/app/uploads]
    
  postgres:
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: multimax
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      
  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]
    
  chromadb:
    image: chromadb/chroma:latest
    volumes: [chroma_data:/chroma/data]
    
  # Optional: Ollama for local AI
  ollama:
    image: ollama/ollama:latest
    volumes: [ollama_models:/root/.ollama]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  pgdata:
  redis_data:
  chroma_data:
  ollama_models:
  uploads:
```

### 15.4 Hosting Options (Zero Budget)

| Provider | Free Tier | Limitations | Best For |
|----------|-----------|-------------|----------|
| **Vercel** | Frontend hosting | Serverless functions 10s timeout | Frontend only |
| **Railway** | $5 free credit | Limited hours | Full stack |
| **Fly.io** | Free 3 VMs | 256MB RAM each | Backend services |
| **Oracle Cloud** | Free 4 ARM cores + 24GB RAM | 2 VMs | Best free VPS |
| **Self-hosted** | Your own hardware | Power/internet costs | Full control |
| **GitHub Codespaces** | 60 hours/month | Development only | Dev environment |

**Recommendation:** Start with **self-hosted** on Oracle Cloud free tier (4 ARM cores, 24GB RAM — enough for all services including Ollama). Use Vercel free tier for frontend hosting. Docker Compose for local development.

---

## 16. FRONTEND ARCHITECTURE

### 16.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND ARCHITECTURE                              │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Pages (Route-level components)                │   │
│  │                                                                  │   │
│  │  /dashboard → Dashboard.tsx                                      │   │
│  │  /chat → AIChat.tsx                                              │   │
│  │  /coding → AICoding.tsx                                          │   │
│  │  /agents → Agents.tsx                                            │   │
│  │  /docs → Documents.tsx                                           │   │
│  │  /voice → VoiceAssistant.tsx                                     │   │
│  │  /images → AIImage.tsx                                           │   │
│  │  /automation → Automation.tsx                                    │   │
│  │  /settings → Settings.tsx                                        │   │
│  │  /profile → Profile.tsx                                          │   │
│  │  /admin → Admin.tsx                                              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Feature Components                            │   │
│  │                                                                  │   │
│  │  Chat feature:                                                   │   │
│  │  ┌───────────────────────────────────────────────────────────┐   │   │
│  │  │ ChatSidebar / ChatMessages / ChatInput / ChatMessage      │   │   │
│  │  │ ModelSelector / FileUpload / StreamingText / ExportDialog │   │   │
│  │  └───────────────────────────────────────────────────────────┘   │   │
│  │                                                                  │   │
│  │  Documents feature:                                              │   │
│  │  ┌───────────────────────────────────────────────────────────┐   │   │
│  │  │ DocumentList / DocumentUploader / DocumentViewer          │   │   │
│  │  │ SearchResults / KnowledgeBase / ChunkViewer               │   │   │
│  │  └───────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Shared UI Components (Shadcn)                 │   │
│  │                                                                  │   │
│  │  Button / Input / Card / Dialog / DropdownMenu / Select         │   │
│  │  Tabs / Tooltip / Avatar / Badge / Sheet / Popover              │   │
│  │  Command / ContextMenu / ScrollArea / Separator / Switch        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Hooks & State Management                      │   │
│  │                                                                  │   │
│  │  • useAuth() → Authentication state + actions                   │   │
│  │  • useChat() → Chat state, streaming, history                   │   │
│  │  • useDocuments() → Document management                         │   │
│  │  • useAgents() → Agent lifecycle                                │   │
│  │  • useSettings() → User and app settings                        │   │
│  │  • useKeyboard() → Keyboard shortcuts                           │   │
│  │  • useWebSocket() → Real-time connection                        │   │
│  │  • useLocalStorage() → Persistent local state                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    API Client Layer                              │   │
│  │                                                                  │   │
│  │  • api.ts → Axios/fetch instance with interceptors              │   │
│  │    - Auth token injection                                       │   │
│  │    - Automatic refresh on 401                                   │   │
│  │    - Error normalization                                        │   │
│  │    - Request deduplication                                      │   │
│  │    - Retry logic                                                │   │
│  │  • Generated API clients (from OpenAPI spec)                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 16.2 State Management Strategy

| State Type | Tool | Rationale |
|------------|------|-----------|
| **Server State** (data from API) | TanStack Query (React Query) | Caching, refetching, optimistic updates, deduplication |
| **UI State** (modals, toggles) | React useState + useReducer | Local component state, no global pollution |
| **Global State** (auth, theme, settings) | Zustand | Lightweight, TypeScript-first, no boilerplate |
| **Form State** | React Hook Form + Zod | Performance, validation, DX |
| **URL State** (search params, filters) | React Router | Shareable, bookmarkable, browser navigation |
| **Real-time State** (streaming, presence) | WebSocket + Zustand | Low latency, persistent connection |

### 16.3 Why TanStack Query?

- **Automatic caching** — No manual cache management
- **Background refetching** — Always fresh data
- **Optimistic updates** — Instant UI feedback
- **Request deduplication** — No duplicate API calls
- **Pagination** — Built-in infinite query support
- **Devtools** — Excellent debugging experience

### 16.4 Why Zustand over Redux?

- **Minimal boilerplate** — No actions, reducers, dispatch types
- **TypeScript native** — Full type inference without extra effort
- **No providers** — Can use outside React (e.g., in API interceptors)
- **Small bundle** — ~1KB vs Redux's ~12KB
- **Simple API** — `create()` and `useStore()` — that's it

---

## 17. API DESIGN & VERSIONING

### 17.1 API Design Principles

- **RESTful** for CRUD operations
- **WebSocket** for real-time events
- **SSE (Server-Sent Events)** for streaming AI responses
- **Consistent error format** across all endpoints
- **Pagination** for all list endpoints
- **API versioning** via URL prefix (`/api/v1/`)

### 17.2 API Versioning Strategy

```
/api/v1/chat/       → Current stable
/api/v2/chat/       → Future breaking changes
/api/beta/chat/     → Preview of upcoming features
```

### 17.3 Endpoint Structure

```
# Core
GET    /api/v1/health                          → Health check
GET    /api/v1/version                         → API version info

# Authentication
POST   /api/v1/auth/register                   → Register user
POST   /api/v1/auth/login                      → Login
POST   /api/v1/auth/refresh                    → Refresh token
POST   /api/v1/auth/logout                     → Logout
POST   /api/v1/auth/forgot-password            → Request reset
POST   /api/v1/auth/reset-password             → Reset password

# Users
GET    /api/v1/users/me                        → Get current user
PATCH  /api/v1/users/me                        → Update profile
DELETE /api/v1/users/me                        → Delete account
GET    /api/v1/users/me/api-keys               → List API keys
POST   /api/v1/users/me/api-keys               → Create API key
DELETE /api/v1/users/me/api-keys/{id}          → Delete API key

# Conversations
GET    /api/v1/conversations                   → List conversations
POST   /api/v1/conversations                   → Create conversation
GET    /api/v1/conversations/{id}              → Get conversation
PATCH  /api/v1/conversations/{id}              → Update conversation
DELETE /api/v1/conversations/{id}              → Delete conversation
POST   /api/v1/conversations/{id}/messages     → Add message
POST   /api/v1/conversations/{id}/share        → Share conversation
DELETE /api/v1/conversations/{id}/share        → Unshare conversation

# Chat
POST   /api/v1/chat/completions                → Chat (non-streaming)
POST   /api/v1/chat/stream                     → Chat (streaming SSE)
GET    /api/v1/models                          → List available models
POST   /api/v1/chat/route                      → Route to best model

# Documents
POST   /api/v1/documents/upload                → Upload document(s)
GET    /api/v1/documents                       → List documents
GET    /api/v1/documents/{id}                  → Get document details
DELETE /api/v1/documents/{id}                  → Delete document
POST   /api/v1/documents/{id}/process          → (Re)process document
POST   /api/v1/documents/chat                  → Chat with documents

# Agents
GET    /api/v1/agents                          → List agents
POST   /api/v1/agents                          → Create agent
GET    /api/v1/agents/{id}                     → Get agent
PATCH  /api/v1/agents/{id}                     → Update agent
DELETE /api/v1/agents/{id}                     → Delete agent
POST   /api/v1/agents/{id}/run                 → Execute agent
GET    /api/v1/agents/{id}/runs                → Get agent run history

# Plugins
GET    /api/v1/plugins                         → List plugins
POST   /api/v1/plugins/install                 → Install plugin
POST   /api/v1/plugins/{id}/enable             → Enable plugin
POST   /api/v1/plugins/{id}/disable            → Disable plugin
DELETE /api/v1/plugins/{id}                    → Uninstall plugin

# Settings
GET    /api/v1/settings                        → Get all settings
PATCH  /api/v1/settings                        → Update settings

# Voice
POST   /api/v1/voice/stt                       → Speech-to-text
POST   /api/v1/voice/tts                       → Text-to-speech

# Admin
GET    /api/v1/admin/users                     → List all users (admin)
GET    /api/v1/admin/stats                     → System statistics
GET    /api/v1/admin/logs                      → System logs
```

### 17.4 Common Response Format

```python
# Success
{
    "success": true,
    "data": { ... },
    "meta": {
        "page": 1,
        "per_page": 50,
        "total": 1000,
        "total_pages": 20
    }
}

# Error
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": [
            {
                "field": "email",
                "message": "Invalid email format",
                "code": "INVALID_EMAIL"
            }
        ],
        "request_id": "req_12345"
    }
}
```

---

## 18. MONITORING, OBSERVABILITY & LOGGING

### 18.1 Three Pillars of Observability

| Pillar | Tool (MVP) | Tool (Scale) | Purpose |
|--------|------------|--------------|---------|
| **Metrics** | Prometheus + Grafana | Same | System health, performance, usage |
| **Logging** | loguru (structured JSON) | ELK / Loki | Debugging, audit, error tracking |
| **Tracing** | OpenTelemetry | Jaeger / Tempo | Request flow across services |

### 18.2 Logging Strategy (Phase 0)

```python
# app/core/logging.py
import structlog

# Structured JSON logging
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        }
    },
    "loggers": {
        "multimax": {"handlers": ["console"], "level": "INFO"},
        "multimax.ai_router": {"level": "DEBUG"},
        "uvicorn": {"handlers": ["console"], "level": "INFO"},
    }
}
```

### 18.3 What to Log

| Category | Events |
|----------|--------|
| **Auth events** | Login, logout, failed login, token refresh, password reset |
| **API requests** | Method, path, status code, duration, user ID (not body) |
| **AI requests** | Model, tokens used, latency, success/failure |
| **Errors** | Stack traces, request context, user ID if authenticated |
| **Admin actions** | User management, settings changes, plugin operations |
| **System events** | Startup, shutdown, resource warnings, database connections |

### 18.4 What NOT to Log

- Passwords or password hashes
- JWT tokens
- API keys
- Full message content (metadata only for audit)
- Personally identifiable information (PII) beyond user ID

---

## 19. TESTING STRATEGY

### 19.1 Testing Pyramid

```
            ╱╲
           ╱  ╲
          ╱ E2E╲           → Playwright (critical user journeys)
         ╱──────╲
        ╱Integration╲      → pytest + FastAPI TestClient
       ╱────────────╲      → vitest + RTL (component tests)
      ╱  Unit Tests   ╲
     ╱──────────────────╲  → pytest (services, routers, models)
    ╱                    ╲ → vitest (hooks, utils, types)
```

### 19.2 Test Coverage Goals

| Layer | Coverage Target | Tools |
|-------|-----------------|-------|
| **Backend Services** | 90%+ | pytest, pytest-asyncio |
| **Backend Routes** | 85%+ | FastAPI TestClient |
| **Frontend Components** | 75%+ | vitest, React Testing Library |
| **Frontend Hooks** | 90%+ | vitest, @testing-library/react-hooks |
| **E2E Flows** | Critical paths | Playwright |

### 19.3 Test Structure

```python
# backend/tests/test_chat.py
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_chat_streaming(app, test_db, auth_headers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/stream",
            json={
                "model": "phi4:latest",
                "messages": [{"role": "user", "content": "Hello"}]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
```

---

## 20. SCALABILITY & FUTURE-PROOFING

### 20.1 Horizontal Scaling Strategy

| Component | Scaling Strategy | When to Scale |
|-----------|-----------------|---------------|
| **Frontend** | CDN caching + multiple replicas | 10K+ concurrent users |
| **Backend API** | Stateless replicas behind load balancer | 1K+ QPS |
| **PostgreSQL** | Read replicas, connection pooling (PgBouncer) | 5K+ concurrent connections |
| **Redis** | Redis Cluster with sharding | 100K+ cache keys |
| **ChromaDB / Qdrant** | Distributed deployment with replication | 10M+ vectors |
| **Task Queue** | More workers, separate queues by priority | 100K+ daily tasks |
| **File Storage** | S3-compatible object store (MinIO) | 100GB+ stored files |

### 20.2 Performance Budget

| Metric | Target (P95) | Notes |
|--------|-------------|-------|
| API response (non-AI) | < 200ms | Cache hit should be < 20ms |
| AI first token | < 2s | Depends on model size/hardware |
| Page load (initial) | < 1.5s | CDN + code splitting |
| Page load (subsequent) | < 500ms | Client-side caching |
| Search results | < 300ms | Vector search + cache |
| File upload (1MB) | < 2s | Direct to storage, async processing |
| Database query (simple) | < 50ms | Indexed queries |
| Database query (complex) | < 500ms | Materialized views for aggregations |

### 20.3 Future-Proofing Decisions

| Decision | Rationale |
|----------|-----------|
| **API versioning from day 1** | We will never have to break existing clients |
| **Schema-per-module** | Modules can be extracted to independent microservices later |
| **Event-driven architecture** | New features can be added by subscribing to events without modifying existing code |
| **Provider abstraction** | New AI providers can be added as plugins without changing any consumer code |
| **Storage abstraction** | Can migrate from local to S3 without application changes |
| **Plugin system** | The entire future marketplace ecosystem is built into the architecture from day 1 |
| **Async-first** | Python async from day 1 prevents blocking in a multi-tenant environment |
| **OpenTelemetry instrumentation** | No need to retrofit observability later |

---

## 21. TECHNOLOGY STACK & RATIONALE

### 21.1 Complete Technology Stack

| Layer | Technology | Version | License | Cost | Why Chosen |
|-------|-----------|---------|---------|------|------------|
| **Frontend Framework** | React 18 + Next.js 14 | 18.x / 14.x | MIT | Free | Largest ecosystem, best SSR/SSG, excellent DX |
| **UI Components** | Shadcn UI | Latest | MIT | Free | Copy-paste components, full customization, no dependency bloat |
| **Styling** | Tailwind CSS 3 | 3.x | MIT | Free | Utility-first, rapid prototyping, tiny production CSS |
| **State Management** | Zustand + TanStack Query | Latest | MIT | Free | Minimal boilerplate, excellent caching, devtools |
| **Form Validation** | React Hook Form + Zod | Latest | MIT | Free | Performance, TypeScript inference, schema validation |
| **Animation** | Framer Motion | Latest | MIT | Free | Declarative animations, layout animations, gesture support |
| **Icons** | Lucide React | Latest | ISC | Free | Clean, consistent, tree-shakeable |
| **Backend Framework** | FastAPI | 0.111+ | MIT | Free | Fastest Python framework, async-native, auto OpenAPI docs |
| **ASGI Server** | Uvicorn | 0.30+ | BSD | Free | High-performance, HTTP/2 support |
| **ORM** | SQLAlchemy 2.0 | 2.0+ | MIT | Free | Most mature Python ORM, async support, excellent docs |
| **Migrations** | Alembic | Latest | MIT | Free | SQLAlchemy-native, auto-generation, reversible |
| **Validation** | Pydantic V2 | 2.x | MIT | Free | Fastest Python validation, JSON Schema generation |
| **Database** | PostgreSQL | 16+ | PostgreSQL | Free | Most advanced open-source database, PGVector, JSONB |
| **Cache** | Redis | 7+ | BSD | Free | Cache, queue, pub/sub, session store — one dependency |
| **Vector DB** | ChromaDB | 0.5+ | Apache 2.0 | Free | Lightweight, Python-native, no external deps |
| **Task Queue** | RQ (Redis Queue) | Latest | BSD | Free | Simple, same Redis, no additional dependency |
| **Event Bus** | Redis Pub/Sub (MVP) | 7+ | BSD | Free | Simple pub/sub, no additional infrastructure |
| **Auth** | Better Auth | Latest | MIT | Free | Self-hostable, no usage limits, full control |
| **LLM Runtime** | Ollama | Latest | MIT | Free | Run local models, no GPU required for small models |
| **Embeddings** | Sentence Transformers | 3.x | Apache 2.0 | Free | State-of-the-art embeddings, runs locally |
| **Container** | Docker + Docker Compose | Latest | Apache 2.0 | Free | Universal, reproducible deployments |
| **Reverse Proxy** | nginx | Latest | BSD | Free | Battle-tested, high-performance, simple config |
| **CI/CD** | GitHub Actions | N/A | N/A | Free (public) | Native GitHub integration, generous free tier |
| **Logging** | loguru + structlog | Latest | MIT | Free | Structured JSON logging, zero-config |
| **Testing (Backend)** | pytest + pytest-asyncio | Latest | MIT | Free | Most popular Python testing framework |
| **Testing (Frontend)** | vitest + React Testing Library | Latest | MIT | Free | Fast, Vite-native, React best practices |
| **E2E Testing** | Playwright | Latest | Apache 2.0 | Free | Cross-browser, reliable, excellent debugging |

### 21.2 Technologies Consciously Excluded

| Technology | Why Excluded | Alternative |
|------------|-------------|-------------|
| **MongoDB** | Document DB not suitable for relational data (users, orgs, permissions) | PostgreSQL |
| **Elasticsearch** | Too heavy for MVP, not needed until 10M+ documents | PostgreSQL FTS + ChromaDB |
| **GraphQL** | Additional complexity, not needed for Phase 0 | REST with OpenAPI |
| **Django** | Heavy, opinionated, not async-first | FastAPI |
| **Redux** | Too much boilerplate, Zustand does everything we need | Zustand |
| **gRPC** | Overkill for Phase 0, adds protobuf compilation step | REST + WebSocket |
| **Kubernetes** | Overkill for Phase 0, significant operational overhead | Docker Compose |

---

## 22. 5-YEAR PRODUCT ROADMAP

### 22.1 Timeline Overview

```
YEAR 1                                   YEAR 2                          YEAR 3-5
├───────────────────────┼──────────────────────────┼──────────────────────────────────┤
│  Phase 0-4            │  Phase 5-9               │  Phase 10-15                     │
│  Foundation           │  Advanced Features       │  Ecosystem & Enterprise          │
│  Core AI Chat         │  Document Intelligence   │  Plugin Marketplace              │
│  Coding Assistant     │  Memory System           │  Team Workspace                  │
│  Research Engine      │  Voice AI                │  Multi-Tenant                    │
│  AI Agents            │  Image Studio            │  Mobile Apps                     │
│                       │  Workflow Automation     │  Enterprise Suite               │
└───────────────────────┴──────────────────────────┴──────────────────────────────────┘
```

### 22.2 Detailed Phase Breakdown

**YEAR 1 — Foundation & Core Capabilities**

| Quarter | Phase | Deliverables |
|---------|-------|-------------|
| **Q1** | Phase 0 | Modular backend architecture, PostgreSQL + Alembic, authentication (Better Auth), Docker setup, CI/CD, testing infrastructure, documentation |
| | Phase 1 | AI Chat: streaming, markdown, code highlighting, conversation management, file uploads, model selection, prompt library |
| **Q2** | Phase 2 | Coding Assistant: code generation, bug fixing, explanation, refactoring, git integration, terminal assistant, project scaffolding |
| | Phase 3 | Research Engine: web search integration (SearXNG), deep search, research reports, citations, academic search, fact-checking |
| **Q3** | Phase 4 | AI Agents: agent framework, browser agent, research agent, coding agent, custom agent creator, tool registry, agent marketplace UI |
| **Q4** | Phase 4 (cont.) | Multi-agent orchestration, agent memory, agent scheduling, agent monitoring dashboard |

**YEAR 2 — Advanced Capabilities & Media**

| Quarter | Phase | Deliverables |
|---------|-------|-------------|
| **Q1** | Phase 5 | Document Intelligence: PDF/Office parsing, OCR (PaddleOCR), document Q&A, summaries, flashcards, mind maps, knowledge extraction |
| | Phase 6 | Memory System: long-term memory, user preferences, knowledge graphs, conversation recall, memory search, memory management UI |
| **Q2** | Phase 7 | Voice AI: speech-to-text (Whisper), text-to-speech, voice chat, voice commands, voice assistant, multi-language support |
| | Phase 8 | Image Studio: image generation (Stable Diffusion), logo generation, thumbnail maker, poster generator, photo editing, background removal |
| **Q3** | Phase 8 (cont.) | AI upscaling, batch processing, image style transfer, integration with ComfyUI workflows |
| | Phase 9 | Video Studio: video generation (early), subtitle generation, avatar videos, short video generator |
| **Q4** | Phase 10 | Workflow Automation: visual workflow builder, triggers (email, calendar, webhook), nodes (AI, API, logic), workflow templates |

**YEAR 3 — Ecosystem & Platform**

| Quarter | Phase | Deliverables |
|---------|-------|-------------|
| **Q1** | Phase 11 | Plugin Marketplace: plugin store UI, plugin installation/management, version control, plugin updates, plugin developer SDK |
| | Phase 11 (cont.) | MCP server support: install, configure, connect MCP servers as tools/plugins |
| **Q2** | Phase 12 | Team Workspace: organizations, shared chats, shared agents, permissions, role management, projects, shared files |
| **Q3** | Phase 13 | Marketplace: publish agents, prompts, templates, plugins, workflows. Community ratings, reviews, featured content |
| **Q4** | Platform Polish | Performance optimization, security audit, documentation overhaul, developer portal |

**YEAR 4 — Mobile & Scale**

| Quarter | Phase | Deliverables |
|---------|-------|-------------|
| **Q1** | Phase 14 | Mobile Apps (Android): native app, push notifications, offline mode, voice input |
| **Q2** | Phase 14 | Mobile Apps (iOS): same features as Android, tablet optimization |
| **Q3** | Scalability | Database sharding, CDN optimization, performance benchmarking, load testing |
| **Q4** | Scalability | Multi-region deployment, disaster recovery, high availability setup |

**YEAR 5 — Enterprise & Maturity**

| Quarter | Phase | Deliverables |
|---------|-------|-------------|
| **Q1** | Phase 15 | Enterprise: SSO/SAML, audit logs, RBAC v2, enterprise APIs, compliance (SOC2, GDPR) |
| **Q2** | Phase 15 | Enterprise: dedicated cloud deployment, SLA guarantees, enterprise support portal |
| **Q3** | Platform 2.0 | Architecture review and iteration, performance optimization, technical debt reduction |
| **Q4** | Future | AI-native OS integration, desktop app, new capabilities based on community feedback |

---

## 23. RISK REGISTER & MITIGATION

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| **R1** | Ollama cannot run on user hardware | High | Medium | AI Router supports cloud providers; users can connect their own API keys |
| **R2** | ChromaDB performance degrades at scale | Medium | High | Abstraction layer allows swap to Qdrant; monitor vector count |
| **R3** | PostgreSQL becomes bottleneck | Medium | High | Read replicas, connection pooling, query optimization from day 1 |
| **R4** | Frontend bundle size grows too large | Medium | Medium | Code splitting, dynamic imports, lazy loading from day 1 |
| **R5** | Plugin security vulnerabilities | Medium | High | Plugin sandbox, permission system, code review for official plugins |
| **R6** | Community fragmentation (forks) | Low | Medium | AGPL-style license protection, strong governance model |
| **R7** | Authentication vendor dependency | Medium | Medium | Auth abstraction layer; Better Auth is self-hosted, no vendor lock |
| **R8** | Memory/service costs at scale | Medium | Medium | Self-hosted components, zero-cost S3 alternatives (R2, B2) |
| **R9** | Feature creep / scope expansion | High | Medium | Strict modular architecture; each feature is a plugin, core stays lean |
| **R10** | Key developer departure | Medium | High | Comprehensive documentation, code reviews, CI/CD, knowledge sharing |

---

## 24. APPENDICES

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Module** | An independently deployable unit of functionality with its own schema, routes, and event handlers |
| **Plugin** | A package that extends the system with new capabilities (models, tools, providers, UI) |
| **AI Router** | The core abstraction layer that decouples all consumers from AI model providers |
| **Agent** | An autonomous or semi-autonomous program that uses AI models and tools to accomplish tasks |
| **Event Bus** | A publish-subscribe system for asynchronous communication between modules |
| **Plugin Registry** | Central registry of all installed plugins, their versions, and configurations |
| **Vector Database** | A database optimized for storing and searching high-dimensional vector embeddings |
| **RBAC** | Role-Based Access Control — assigning permissions to roles, roles to users |
| **MCP** | Model Context Protocol — a standard for connecting AI models to external tools and data |

### Appendix B: Environment Variables (Phase 0)

```env
# === REQUIRED ===
# Database
DATABASE_URL=postgresql+asyncpg://multimax:password@localhost:5432/multimax
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Auth
JWT_SECRET=your-256-bit-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379/0

# App
APP_NAME=Multimax AI Hub
APP_VERSION=0.1.0
APP_ENV=development  # development | staging | production
DEBUG=true
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# === OPTIONAL ===
# AI Providers
OLLAMA_URL=http://localhost:11434
OPENROUTER_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Storage
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./uploads
# S3_STORAGE_BUCKET=
# S3_ACCESS_KEY=
# S3_SECRET_KEY=
# S3_ENDPOINT=

# Vector Database
VECTOR_DB_BACKEND=chroma
CHROMA_PERSIST_DIR=./chroma_db

# Sentry / Error Tracking
SENTRY_DSN=

# Supabase (optional, for alternative auth)
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Email
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@multimax.ai
```

### Appendix C: Git Branching Strategy

```
main
  ├── develop
  │   ├── feature/phase-0-backend
  │   ├── feature/phase-0-auth
  │   ├── feature/phase-0-docker
  │   ├── feature/phase-1-chat-enhancements
  │   └── ...
  ├── release/v0.1.0
  ├── release/v0.2.0
  └── hotfix/*
```

### Appendix D: Code Review Checklist

- [ ] Follows the architecture principles (modular, abstracted, testable)
- [ ] No hardcoded secrets or configuration
- [ ] Input validation on all endpoints
- [ ] Proper error handling (no bare excepts)
- [ ] Type hints on all functions
- [ ] Docstrings on public APIs
- [ ] Tests for new functionality
- [ ] No circular imports
- [ ] Database queries use indexes appropriately
- [ ] No N+1 query problems
- [ ] Frontend components use proper TypeScript types
- [ ] No large bundle imports (tree-shakeable)

---

## DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-07-11 | Principal Architect | Initial draft covering all architecture areas |
| | | | |

---

*This document is a living artifact. It should be reviewed and updated as architectural decisions evolve. Every significant decision should be documented here with the rationale.*