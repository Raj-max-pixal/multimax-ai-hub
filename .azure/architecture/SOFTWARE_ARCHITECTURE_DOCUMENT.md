# MULTIMAX AI HUB — SOFTWARE ARCHITECTURE DOCUMENT

**Version:** 1.0.0 (FROZEN)
**Status:** Architecture Baseline — Implementation Phase 0 Ready
**Last Updated:** 2026-07-11

---

## ARCHITECTURE PRINCIPLE: Design Before Build

This document defines **architecture** (interfaces, contracts, abstractions, extension points) — NOT implementation.

Key distinction:
- **Architecture** = What exists at compile/start time: interfaces, abstract classes, type definitions, configuration schemas, event contracts, extension registries
- **Implementation** = What runs at runtime: concrete service classes, database queries, UI components, API handlers

All interfaces and extension points are designed in this document. Their implementations will be built progressively across phases.

---

## TABLE OF CONTENTS

1. [Architecture vs Implementation](#1-architecture-vs-implementation)
2. [Core Platform Architecture](#2-core-platform-architecture)
3. [Module Architecture & Capability Manifest](#3-module-architecture--capability-manifest)
4. [Plugin Architecture (Interface Only)](#4-plugin-architecture-interface-only)
5. [AI Router](#5-ai-router)
6. [Agent Runtime](#6-agent-runtime)
7. [Event Bus](#7-event-bus)
8. [Queue System & Async Processing](#8-queue-system--async-processing)
9. [Memory Architecture (First-Class System)](#9-memory-architecture-first-class-system)
10. [Search Engine](#10-search-engine)
11. [Authentication & Authorization](#11-authentication--authorization)
12. [Database Design](#12-database-design)
13. [API Design & Versioning](#13-api-design--versioning)
14. [Cache Architecture & Offline Strategy](#14-cache-architecture--offline-strategy)
15. [Storage Architecture](#15-storage-architecture)
16. [Security Architecture](#16-security-architecture)
17. [Frontend Architecture](#17-frontend-architecture)
18. [Deployment Architecture & Enterprise Interfaces](#18-deployment-architecture--enterprise-interfaces)
19. [Monitoring, Observability & Logging](#19-monitoring-observability--logging)
20. [Testing Strategy & Phase Gates](#20-testing-strategy--phase-gates)
21. [CI/CD Pipeline](#21-cicd-pipeline)
22. [Scalability & Future-Proofing](#22-scalability--future-proofing)
23. [Technology Stack & Rationale](#23-technology-stack--rationale)
24. [5-Year Product Roadmap](#24-5-year-product-roadmap)
25. [Risk Register & Mitigation](#25-risk-register--mitigation)
26. [Phase Completion Gates](#26-phase-completion-gates)
27. [Version 1.0 Freeze](#27-version-10-freeze)
28. [Appendices](#28-appendices)

---

## 1. ARCHITECTURE VS IMPLEMENTATION

### 1.1 The Principle

Every system component has two states:

| State | Definition | When |
|-------|------------|------|
| **Interface** | Abstract contract, type definition, schema, extension point | **Designed before Phase 0** |
| **Implementation** | Concrete code, database queries, API handlers, UI components | **Built progressively per phase** |

### 1.2 What is Architecture (Designed Now)

| Component | Interface Status | Implementation Phase |
|-----------|-----------------|---------------------|
| Plugin Registry | Abstract contract + extension point | Phase 11 |
| Marketplace API | OpenAPI schema + auth contract | Phase 13 |
| Enterprise SSO | Interface + configuration schema | Phase 15 |
| Multi-tenant isolation | Schema + middleware interface | Phase 12 |
| Plugin sandbox | Isolation contract + permission model | Phase 11 |
| Billing/usage tracking | Event schema + metrics interface | Phase 15 |

### 1.3 Why This Matters

Without early interface design:
- Plugins will require rewriting core code to add hooks
- Marketplace will need API versioning retrofitted
- Enterprise customers will fork the codebase
- Breaking changes will anger the community

With early interface design:
- Third-party developers can build against stable contracts
- Modules can be independently developed
- Marketplace can launch with existing plugins
- Enterprise deploys without custom forks

---

## 2. CORE PLATFORM ARCHITECTURE

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MULTIMAX AI HUB                                  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    PLATFORM LAYER (Core OS)                      │    │
│  │                                                                  │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │    │
│  │  │  DI        │ │  Config    │ │  Event     │ │  Queue       │  │    │
│  │  │  Container │ │  Service   │ │  Bus       │ │  Manager     │  │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │    │
│  │                                                                  │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │    │
│  │  │  Logger    │ │  Metrics   │ │  Auth      │ │  Storage     │  │    │
│  │  │  Service   │ │  Collector │ │  Service   │ │  Service     │  │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                     │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    MODULE LAYER                                   │    │
│  │                                                                  │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │    │
│  │  │  Chat      │ │  Coding    │ │  Research  │ │  Documents   │  │    │
│  │  │  Module    │ │  Module    │ │  Engine    │ │  Intelligence│  │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │    │
│  │                                                                  │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │    │
│  │  │  Agents    │ │  Voice     │ │  Image     │ │  Workflow    │  │    │
│  │  │  Runtime   │ │  Engine    │ │  Studio    │ │  Engine      │  │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                     │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    SHARED SERVICES                                 │    │
│  │                                                                  │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │    │
│  │  │  AI       │ │  Memory   │ │  Search   │ │  Knowledge   │  │    │
│  │  │  Router   │ │  Engine   │ │  Engine   │ │  Graph       │  │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Dependency Injection Container

Every module receives its dependencies through constructor injection. No module imports another module directly.

```python
# app/core/container.py
from dependency_injector import containers, providers

class ApplicationContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.modules.chat",
            "app.modules.coding",
            "app.modules.agents",
            "app.modules.documents",
            "app.modules.research",
        ]
    )
    
    # Core services
    config = providers.Singleton(ConfigurationService)
    logger = providers.Singleton(LoggingService)
    event_bus = providers.Singleton(EventBus)
    queue = providers.Singleton(QueueManager)
    
    # Infrastructure
    db = providers.Singleton(DatabaseSession, config=config)
    cache = providers.Singleton(CacheService, config=config)
    storage = providers.Singleton(StorageService, config=config)
    
    # AI Layer
    ai_provider_registry = providers.Singleton(AIProviderRegistry)
    ai_router = providers.Singleton(
        AIRouter,
        provider_registry=ai_provider_registry,
        event_bus=event_bus,
        config=config,
    )
    
    # Memory
    memory_engine = providers.Singleton(
        MemoryEngine,
        db=db,
        vector_db=config.vector_db,
        cache=cache,
        event_bus=event_bus,
    )
    
    # Search
    search_engine = providers.Singleton(
        SearchEngine,
        db=db,
        vector_db=config.vector_db,
        cache=cache,
    )
    
    # Modules
    chat_module = providers.Factory(
        ChatModule,
        ai_router=ai_router,
        memory_engine=memory_engine,
        event_bus=event_bus,
        db=db,
    )
```

### 2.3 Module Interface (Abstract Base)

```python
# app/core/module.py

class ModuleManifest(BaseModel):
    """Published by every module at registration time."""
    name: str = Field(..., pattern=r"^[a-z0-9_]+$")
    version: str
    description: str
    author: str
    license: str = "MIT"
    
    capabilities: list[CapabilityDeclaration]
    """What this module can do. Discovered dynamically by AI Router."""
    
    dependencies: list[ModuleDependency]
    """Other modules this module requires."""
    
    permissions: list[str]
    """What system resources this module needs."""
    
    lifecycle_hooks: LifecycleHooks | None = None

class ModuleDependency(BaseModel):
    module: str
    version_spec: str  # Semver range, e.g. ">=1.0.0,<2.0.0"
    optional: bool = False

class CapabilityDeclaration(BaseModel):
    """A single capability this module provides."""
    id: str  # e.g. "chat.completions", "code.generation", "search.web"
    name: str
    description: str
    input_schema: dict  # JSON Schema for input
    output_schema: dict  # JSON Schema for output
    models: list[str] = []  # Recommended models for this capability
    requires: list[str] = []  # Required capabilities from other modules
    cost_multiplier: float = 1.0  # Relative computational cost

class Module(ABC):
    """Base class for all modules."""
    
    manifest: ModuleManifest
    
    @abstractmethod
    async def initialize(self, container: Container) -> None:
        """Called once at startup. Use to register routes, subscribe to events."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Called on graceful shutdown."""
        pass
    
    @abstractmethod
    async def health_check(self) -> ModuleHealth:
        """Return current health status."""
        pass
```

### 2.4 Capability Registry (Dynamic Discovery)

```python
# app/core/capability_registry.py

class CapabilityRegistry:
    """Central registry for all module capabilities.
    
    AI Router queries this to find the best module+model for a task.
    Marketplace queries this to display available capabilities.
    Future plugin system registers capabilities the same way.
    """
    
    def __init__(self):
        self._capabilities: dict[str, list[CapabilityDeclaration]] = {}
        self._module_map: dict[str, Module] = {}
    
    def register(self, module: Module) -> None:
        """Called when a module initializes."""
        for cap in module.manifest.capabilities:
            if cap.id not in self._capabilities:
                self._capabilities[cap.id] = []
            self._capabilities[cap.id].append(cap)
        self._module_map[module.manifest.name] = module
    
    def unregister(self, module_name: str) -> None:
        """Called when a module is disabled or uninstalled."""
        module = self._module_map.pop(module_name, None)
        if module:
            for cap in module.manifest.capabilities:
                self._capabilities[cap.id] = [
                    c for c in self._capabilities.get(cap.id, [])
                    if c.name != cap.name
                ]
    
    def find_capability(self, capability_id: str) -> list[CapabilityDeclaration]:
        """Find all modules providing a capability."""
        return self._capabilities.get(capability_id, [])
    
    def find_best_match(
        self,
        task_type: str,
        preferred_model: str | None = None,
        constraints: TaskConstraints | None = None,
    ) -> CapabilityMatch | None:
        """AI Router calls this to find optimal capability match."""
        pass
    
    @property
    def all_capabilities(self) -> dict[str, list[CapabilityDeclaration]]:
        """Full capability map. Used by AI Router and Marketplace."""
        return dict(self._capabilities)
```

---

## 3. MODULE ARCHITECTURE & CAPABILITY MANIFEST

### 3.1 Module Structure

Every module follows this structure:

```
backend/modules/{module_name}/
├── __init__.py              # Module class, routes FastAPI app
├── models.py                # Pydantic schemas (interface)
├── service.py               # Business logic (implementation)
├── repository.py            # Database access (implementation)
├── events.py                # Event definitions (interface)
├── capabilities.py          # Capability declarations (interface)
├── templates/               # Optional: Jinja2 templates
├── static/                  # Optional: module-specific static files
└── tests/
    ├── test_service.py
    └── test_api.py
```

### 3.2 Module Manifest (module.yaml)

```yaml
# modules/chat/module.yaml
name: chat
version: 1.0.0
author: Multimax
license: MIT

description: >
  AI Chat with streaming, markdown, code highlighting, 
  file uploads, conversation management, and multi-model support.

capabilities:
  - id: chat.completions
    name: Chat Completion
    description: Generate text responses in a conversational context
    input_schema:
      type: object
      properties:
        messages: { type: array, items: { $ref: "#/definitions/Message" } }
        model: { type: string }
        stream: { type: boolean, default: false }
        temperature: { type: number, default: 0.7 }
    output_schema:
      type: object
      properties:
        content: { type: string }
        model: { type: string }
        usage: { $ref: "#/definitions/Usage" }
    models: ["qwen3:4b", "llama3:8b", "phi4:latest"]
    
  - id: chat.streaming
    name: Chat Streaming
    description: Stream AI responses token by token via SSE
    input_schema:
      type: object
      properties:
        messages: { type: array }
        model: { type: string }
    output_schema:
      type: object
      properties:
        type: { type: string, enum: ["token", "done", "error"] }
        content: { type: string }
    models: ["qwen3:4b", "llama3:8b", "phi4:latest"]

  - id: chat.code_highlighting
    name: Code Highlighting
    description: Detect and highlight code blocks in responses
    requires: ["chat.completions"]

  - id: chat.file_upload
    name: File Upload
    description: Upload and process files within chat context
    permissions: ["storage.write", "storage.read"]

dependencies:
  modules:
    - { module: memory, version_spec: ">=1.0.0", optional: false }
  packages:
    - sentence-transformers

permissions:
  - storage.read
  - storage.write
  
lifecycle:
  on_enable: scripts/enable.py
  on_disable: scripts/disable.py
```

### 3.3 Module Registration

```python
# Happens at startup, discovers all installed modules
class ModuleLoader:
    def __init__(self, container: Container, registry: CapabilityRegistry):
        self.container = container
        self.registry = registry
    
    async def discover_and_load(self) -> list[Module]:
        """Scan modules directory, validate manifests, load modules."""
        modules = []
        module_paths = self._scan_for_modules()
        
        # Phase 1: Resolve dependencies
        sorted_modules = self._resolve_dependency_order(module_paths)
        
        # Phase 2: Validate manifests
        for module_path in sorted_modules:
            manifest = self._load_manifest(module_path)
            self._validate_manifest(manifest)
        
        # Phase 3: Initialize modules in dependency order
        for module_path in sorted_modules:
            module = self._instantiate_module(module_path, self.container)
            await module.initialize(self.container)
            self.registry.register(module)
            modules.append(module)
        
        return modules
    
    def _resolve_dependency_order(self, paths: list[str]) -> list[str]:
        """Topological sort based on module dependencies."""
        pass
```

### 3.4 Capability Manifest vs Hardcoded Routing

| Before (Hardcoded) | After (Dynamic) |
|--------------------|-----------------|
| `if task == "coding": use deepseek` | `registry.find_capability("code.generation")` |
| `if task == "chat": use qwen` | `registry.find_capability("chat.completions")` |
| New feature = edit if/else chain | New feature = register capability |
| Marketplace = separate code | Marketplace = query registry |

---

## 4. PLUGIN ARCHITECTURE (Interface Only)

### 4.1 Design Rationale

The plugin system is **designed in this document** but **implemented in Phase 11**. All interfaces and extension points are defined now so that Phase 0-10 modules are built with plugin compatibility from day 1.

### 4.2 Plugin Interface (Abstract)

```python
# app/core/plugin.py (exists at compile time in Phase 0)

class PluginManifest(BaseModel):
    """Every plugin publishes this."""
    id: str  # Unique identifier, e.g. "com.multimax.search-web"
    name: str
    version: str
    author: str
    license: str
    min_core_version: str
    max_core_version: str | None
    
    capabilities: list[CapabilityDeclaration]
    """Same format as module capabilities. Enables Marketplace discovery."""
    
    permissions: list[str]
    """What the plugin can access."""
    
    config_schema: dict | None = None
    """JSON Schema for plugin configuration."""

class Plugin(ABC):
    """Base class for all plugins. Defined now, implemented in Phase 11."""
    
    manifest: PluginManifest
    
    @abstractmethod
    async def initialize(self, context: PluginContext) -> None:
        """Called when plugin is installed and enabled."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Called when plugin is disabled or uninstalled."""
        pass

class PluginContext:
    """Sandboxed context passed to plugins. Limits what plugins can access."""
    
    event_bus: EventBusProtocol
    storage: StorageServiceProtocol
    cache: CacheServiceProtocol
    logger: LoggerProtocol
    config: dict  # Plugin-specific config from user
    
    # NOT exposed: database session, filesystem path, service containers

class PluginRegistry(ABC):
    """Plugin discovery and lifecycle management."""
    
    @abstractmethod
    async def install(self, source: str) -> PluginManifest:
        """Install a plugin from URL, file, or marketplace."""
        pass
    
    @abstractmethod
    async def uninstall(self, plugin_id: str) -> None:
        """Remove a plugin."""
        pass
    
    @abstractmethod
    async def enable(self, plugin_id: str) -> None:
        """Enable a disabled plugin."""
        pass
    
    @abstractmethod
    async def disable(self, plugin_id: str) -> None:
        """Disable without uninstalling."""
        pass
    
    @abstractmethod
    async def get_plugin(self, plugin_id: str) -> Plugin | None:
        """Get plugin instance."""
        pass
    
    @abstractmethod
    def list_plugins(self) -> list[PluginManifest]:
        """List all installed plugins."""
        pass
```

### 4.3 Plugin Distribution Model (Designed)

```
Three distribution channels (interface defined, implementation deferred):

1. Local Install
   - User downloads plugin folder to /plugins/
   - System scans /plugins/ at startup
   - Phase 11 implementation

2. Marketplace Install
   - User clicks "Install" in Marketplace UI
   - System downloads from registry.multimax.ai
   - Phase 13 implementation

3. MCP Server
   - User connects via MCP protocol
   - Plugin appears as tool provider
   - Phase 11 implementation
```

### 4.4 Plugin Sandbox Model (Designed)

```
Three tiers (interface defined, implementation deferred):

Tier 1: Built-in Modules
  - Full system access
  - Direct database access
  - Unrestricted API access
  - Source: core repository

Tier 2: Verified Plugins
  - Restricted API subset (PluginContext)
  - No direct database access
  - Every system call is audited
  - Source: signed by Multimax

Tier 3: Community Plugins
  - Process-isolated (subprocess or container)
  - Strict permission model
  - Resource limits (CPU, memory, time)
  - Network access restricted by manifest
  - Source: any developer
```

### 4.5 Extension Points (Defined Now)

Every module defines extension points where plugins can hook in:

```python
# Example: Chat module extension points
class ChatModule(Module):
    extension_points = {
        "chat.before_send": {
            "description": "Modify prompt before sending to AI model",
            "hook_type": "sync",  # sync | async | stream
            "input_schema": Message.schema(),
            "output_schema": Message.schema(),
        },
        "chat.after_receive": {
            "description": "Process AI response before showing to user",
            "hook_type": "async",
            "input_schema": Message.schema(),
            "output_schema": Message.schema(),
        },
        "chat.model_select": {
            "description": "Override model selection for this request",
            "hook_type": "async",
            "input_schema": ChatRequest.schema(),
            "output_schema": ModelSelection.schema(),
        },
    }
```

---

## 5. AI ROUTER

### 5.1 Provider Abstraction

```python
# app/ai/protocol.py

class AIProviderProtocol(Protocol):
    """Every AI provider must implement this interface."""
    
    @property
    def provider_id(self) -> str:
        """Unique provider identifier, e.g. 'ollama', 'openai'."""
        ...
    
    @property
    def supported_capabilities(self) -> set[str]:
        """Capability IDs this provider supports."""
        ...
    
    @property
    def health_status(self) -> ProviderHealth:
        """Current health of this provider."""
        ...
    
    async def chat(
        self,
        messages: list[Message],
        model: str,
        stream: bool = False,
        timeout: int = 30,
    ) -> ChatResult:
        ...
    
    async def chat_stream(
        self,
        messages: list[Message],
        model: str,
        timeout: int = 30,
    ) -> AsyncIterator[StreamChunk]:
        ...
    
    async def check_availability(self) -> bool:
        """Quick health check for routing decisions."""
        ...
```

### 5.2 Provider-Agnostic Streaming Format

```python
# app/ai/streaming.py

class StreamChunk(BaseModel):
    """Normalized streaming event. Same format regardless of provider."""
    
    type: Literal["token", "done", "error", "tool_call", "tool_result"]
    
    # For type="token"
    content: str | None = None
    
    # For type="done"
    finish_reason: Literal["stop", "length", "tool_calls", "error"] | None = None
    usage: Usage | None = None
    
    # For type="error"
    error_code: str | None = None
    error_message: str | None = None
    
    # For type="tool_call"
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_arguments: dict | None = None
    
    # For type="tool_result"
    tool_call_id: str | None = None
    tool_result: Any | None = None
    
    # Metadata (always present)
    model: str
    provider: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

# SSE wire format:
# event: token
# data: {"content": "Hello", "model": "qwen3:4b", "provider": "ollama"}
# 
# event: done
# data: {"finish_reason": "stop", "usage": {"total_tokens": 42}}
```

### 5.3 Router with Fallback Chains

```python
# app/ai/router.py

class AIRouter:
    def __init__(
        self,
        provider_registry: AIProviderRegistry,
        capability_registry: CapabilityRegistry,
        event_bus: EventBus,
        config: ConfigurationService,
    ):
        self.provider_registry = provider_registry
        self.capability_registry = capability_registry
        self.event_bus = event_bus
        self.config = config
    
    async def route(
        self,
        request: ChatRequest,
        user_id: str,
    ) -> ChatResponse:
        """Route request to best provider/model based on capability + constraints."""
        
        # 1. Get capability declarations
        task_type = self._classify_task(request.messages)
        capabilities = self.capability_registry.find_capability(task_type)
        
        if not capabilities:
            # Fallback to generic chat
            capabilities = self.capability_registry.find_capability("chat.completions")
        
        # 2. Build provider chain
        provider_chain = self._build_fallback_chain(task_type, request.model)
        
        # 3. Try providers in order with fallback
        last_error = None
        for provider_id, model in provider_chain:
            provider = self.provider_registry.get(provider_id)
            if not provider or not await provider.check_availability():
                continue
            
            try:
                if request.stream:
                    return await self._route_stream(provider, model, request)
                else:
                    return await self._route_completion(provider, model, request)
            except ProviderError as e:
                last_error = e
                await self.event_bus.publish("ai.provider.fallback", {
                    "provider": provider_id,
                    "model": model,
                    "error": str(e),
                    "user_id": user_id,
                })
                continue
        
        # 4. All providers failed
        raise NoAvailableProviderError(
            "All AI providers failed. Please check your model connections.",
            errors=last_error,
        )
    
    def _build_fallback_chain(
        self,
        task_type: str,
        preferred_model: str | None,
    ) -> list[tuple[str, str]]:
        """Build ordered list of (provider, model) to try."""
        chain = []
        
        # User-specified model
        if preferred_model:
            provider = self._infer_provider(preferred_model)
            if provider:
                chain.append((provider, preferred_model))
        
        # Default routing by task type
        routing_map = self.config.get("ai.routing_map", {
            "code.generation": [("ollama", "deepseek-coder:6.7b"), ("openai", "gpt-4")],
            "chat.completions": [("ollama", "qwen3:4b"), ("ollama", "phi4:latest")],
            "reasoning": [("ollama", "qwen3:8b"), ("openai", "gpt-4o")],
            "writing": [("ollama", "llama3:8b"), ("anthropic", "claude-3-haiku")],
            "vision": [("ollama", "qwen3-vision:7b")],
            "search.web": [("openai", "gpt-4o-mini"), ("ollama", "llama3:8b")],
        })
        
        chain.extend(routing_map.get(task_type, routing_map["chat.completions"]))
        
        return chain
    
    def _classify_task(self, messages: list[Message]) -> str:
        """Determine task type from message content.
        
        Phase 0: Rule-based keyword matching
        Phase 2+: ML-based classification
        """
        # Check for code
        if any("```" in m.content for m in messages):
            return "code.generation"
        
        # Check for reasoning
        if any(kw in m.content.lower() for m in messages 
               for kw in ["explain", "why", "how does", "reason", "analyze"]):
            return "reasoning"
        
        # Default
        return "chat.completions"
```

### 5.4 Model Capability Registry

```python
# app/ai/registry.py

class ModelCapability(BaseModel):
    model_id: str
    provider: str
    capabilities: set[str]  # e.g. {"chat", "code", "vision", "tools"}
    context_length: int
    max_output_tokens: int
    supports_streaming: bool
    supports_tools: bool
    supports_vision: bool
    cost_per_1k_input: float = 0.0  # $0 for local models
    cost_per_1k_output: float = 0.0
    is_available: bool = True

class AIProviderRegistry:
    def __init__(self):
        self._providers: dict[str, AIProviderProtocol] = {}
        self._models: dict[str, ModelCapability] = {}
    
    def register_provider(self, provider: AIProviderProtocol) -> None:
        self._providers[provider.provider_id] = provider
    
    def register_model(self, capability: ModelCapability) -> None:
        self._models[capability.model_id] = capability
    
    def get_provider(self, provider_id: str) -> AIProviderProtocol | None:
        return self._providers.get(provider_id)
    
    def find_models_by_capability(
        self,
        capability: str,
        limit: int = 5,
    ) -> list[ModelCapability]:
        return sorted(
            [m for m in self._models.values() 
             if capability in m.capabilities and m.is_available],
            key=lambda m: m.cost_per_1k_output,
        )[:limit]
```

---

## 6. AGENT RUNTIME

### 6.1 Agent Lifecycle State Machine

```
                    ┌─────────────┐
                    │  DRAFT      │  Agent created but not ready to run
                    └──────┬──────┘
                           │ activate
                           ▼
                    ┌─────────────┐
                    │  ACTIVE     │  Agent is configured and ready
                    └──────┬──────┘
                           │ execute
                           ▼
                    ┌─────────────┐
            ┌─────▶ │  QUEUED     │ ◀───── retry
            │       └──────┬──────┘
            │              │ dequeue
            │              ▼
            │       ┌─────────────┐
            │       │  RUNNING    │
            │       └──────┬──────┘
            │              │ pause    resume
            │              ▼          │
            │       ┌─────────────┐   │
            │       │  PAUSED     │───┘
            │       └──────┬──────┘
            │              │ complete
            │              ▼
            │       ┌─────────────┐
            └────── │ COMPLETED   │
                    └─────────────┘

                    ┌─────────────┐
                    │   FAILED    │
                    └─────────────┘

                    ┌─────────────┐
                    │ CANCELLED   │  User cancelled execution
                    └─────────────┘
```

### 6.2 Agent State Transitions

```python
# app/agents/state_machine.py

class AgentState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentTransition(BaseModel):
    from_state: AgentState
    to_state: AgentState
    trigger: str
    condition: str | None = None

# Allowed transitions
AGENT_STATE_MACHINE = {
    AgentState.DRAFT: [
        AgentTransition(from_state="draft", to_state="active", trigger="activate"),
    ],
    AgentState.ACTIVE: [
        AgentTransition(from_state="active", to_state="queued", trigger="execute"),
        AgentTransition(from_state="active", to_state="draft", trigger="deactivate"),
    ],
    AgentState.QUEUED: [
        AgentTransition(from_state="queued", to_state="running", trigger="dequeue"),
        AgentTransition(from_state="queued", to_state="cancelled", trigger="cancel"),
        AgentTransition(from_state="queued", to_state="failed", trigger="timeout"),
    ],
    AgentState.RUNNING: [
        AgentTransition(from_state="running", to_state="paused", trigger="pause"),
        AgentTransition(from_state="running", to_state="completed", trigger="complete"),
        AgentTransition(from_state="running", to_state="failed", trigger="error"),
        AgentTransition(from_state="running", to_state="cancelled", trigger="cancel"),
    ],
    AgentState.PAUSED: [
        AgentTransition(from_state="paused", to_state="running", trigger="resume"),
        AgentTransition(from_state="paused", to_state="cancelled", trigger="cancel"),
        AgentTransition(from_state="paused", to_state="failed", trigger="timeout"),
    ],
    AgentState.COMPLETED: [],
    AgentState.FAILED: [
        AgentTransition(from_state="failed", to_state="queued", trigger="retry",
                        condition="max_retries_not_reached"),
    ],
    AgentState.CANCELLED: [],
}
```

### 6.3 Agent Execution Guardrails

```python
# app/agents/guardrails.py

class AgentGuardrails(BaseModel):
    """Applied to every agent execution to prevent runaway agents."""
    
    max_execution_time_seconds: int = 300  # 5 minutes default
    max_tool_calls: int = 50
    max_tokens: int = 32000  # Token budget
    max_concurrent_tools: int = 3
    allow_network_access: bool = True
    allow_file_system_access: bool = False
    allow_code_execution: bool = False
    require_human_approval: list[str] = []  # Tool names requiring approval
    
    class Config:
        use_enum_values = True

class AgentCheckpoint(BaseModel):
    """Saved agent state for pause/resume and crash recovery."""
    agent_id: str
    run_id: str
    state: AgentState
    messages: list[Message]
    tool_results: list[ToolResult]
    context: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        use_enum_values = True
```

---

## 7. EVENT BUS

### 7.1 Design Requirements

| Requirement | MVP (Phase 0) | Scale (Phase 10+) |
|-------------|---------------|-------------------|
| **Delivery** | At-least-once in-process + PG journal | Exactly-once with Kafka |
| **Persistence** | PostgreSQL event journal | Kafka log compaction |
| **Retry** | 3 attempts, exponential backoff | Configurable per topic |
| **Dead Letter** | PostgreSQL DLQ table | Kafka DLQ topic |
| **Replay** | Replay from PG journal | Replay from Kafka offset |
| **Backpressure** | Bounded queue per subscriber | Kafka consumer groups |

### 7.2 Event Bus Implementation (Phase 0)

```python
# app/events/bus.py

class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    topic: str
    data: dict
    source: str  # Module or service name
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: UUID | None = None  # For tracing request chains
    retry_count: int = 0
    max_retries: int = 3

class EventBus:
    """Persistent event bus with at-least-once delivery."""
    
    def __init__(self, db: DatabaseSession, config: ConfigurationService):
        self._db = db
        self._config = config
        self._subscribers: dict[str, list[EventHandler]] = {}
        self._running = False
    
    async def publish(self, topic: str, data: dict, source: str = "system") -> UUID:
        """Publish an event. Persists to PostgreSQL, then notifies subscribers."""
        event = Event(
            topic=topic,
            data=data,
            source=source,
        )
        
        # 1. Persist immediately
        await self._db.execute(
            "INSERT INTO event_journal (id, topic, data, source, timestamp) "
            "VALUES ($1, $2, $3, $4, $5)",
            event.id, event.topic, json.dumps(event.data), 
            event.source, event.timestamp,
        )
        
        # 2. Enqueue for delivery
        asyncio.create_task(self._deliver(event))
        
        return event.id
    
    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
    ) -> UUID:
        """Register a handler for a topic. Returns subscription ID."""
        sub_id = uuid4()
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append((sub_id, handler))
        return sub_id
    
    async def unsubscribe(self, subscription_id: UUID) -> None:
        """Remove a subscription."""
        for topic in self._subscribers:
            self._subscribers[topic] = [
                (sid, h) for sid, h in self._subscribers[topic]
                if sid != subscription_id
            ]
    
    async def _deliver(self, event: Event) -> None:
        """Deliver event to all subscribers with retry logic."""
        handlers = self._subscribers.get(event.topic, [])
        
        for _, handler in handlers:
            success = False
            for attempt in range(event.max_retries):
                try:
                    await handler(event)
                    success = True
                    break
                except Exception as e:
                    logger.error(
                        f"Handler failed for {event.topic}: {e}",
                        extra={"event_id": str(event.id), "attempt": attempt + 1},
                    )
                    if attempt < event.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            if not success:
                # Move to dead letter queue
                await self._db.execute(
                    "INSERT INTO dead_letter_queue "
                    "(event_id, topic, data, source, error, timestamp) "
                    "VALUES ($1, $2, $3, $4, $5, $6)",
                    event.id, event.topic, json.dumps(event.data),
                    event.source, "Max retries exceeded", datetime.utcnow(),
                )
    
    async def replay(self, topic: str, since: datetime) -> AsyncIterator[Event]:
        """Replay events from journal for recovery."""
        rows = await self._db.fetch(
            "SELECT * FROM event_journal WHERE topic = $1 AND timestamp >= $2 "
            "ORDER BY timestamp ASC",
            topic, since,
        )
        for row in rows:
            yield Event(
                id=row["id"],
                topic=row["topic"],
                data=json.loads(row["data"]),
                source=row["source"],
                timestamp=row["timestamp"],
            )
    
    @property
    async def dead_letter_queue(self) -> list[DeadLetterEvent]:
        """Events that exhausted all retries."""
        rows = await self._db.fetch(
            "SELECT * FROM dead_letter_queue ORDER BY timestamp DESC LIMIT 100"
        )
        return [DeadLetterEvent(**row) for row in rows]

class EventHandler(Protocol):
    async def __call__(self, event: Event) -> None: ...
```

### 7.3 Database Schema for Event Persistence

```sql
-- event_journal: Append-only log of all events
CREATE TABLE event_journal (
    id UUID PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    source VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT idx_event_journal_topic_ts 
        UNIQUE (topic, timestamp)
);

CREATE INDEX idx_event_journal_topic ON event_journal(topic);
CREATE INDEX idx_event_journal_ts ON event_journal(timestamp);

-- dead_letter_queue: Events that failed all retries
CREATE TABLE dead_letter_queue (
    id UUID PRIMARY KEY,
    event_id UUID NOT NULL,
    topic VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    source VARCHAR(255) NOT NULL,
    error TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 7.4 Event Schema Standards

```python
# app/events/events.py

class EventCategory(str, Enum):
    CHAT = "chat"
    AGENT = "agent"
    MEMORY = "memory"
    DOCUMENT = "document"
    USER = "user"
    MODULE = "module"
    WORKFLOW = "workflow"
    SYSTEM = "system"
    AI = "ai"
    SEARCH = "search"

class CoreEvents:
    # User events
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PASSWORD_RESET = "user.password.reset"
    
    # Chat events
    MESSAGE_CREATED = "chat.message.created"
    CONVERSATION_CREATED = "chat.conversation.created"
    CONVERSATION_DELETED = "chat.conversation.deleted"
    CONVERSATION_SHARED = "chat.conversation.shared"
    
    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_PAUSED = "agent.paused"
    AGENT_TOOL_CALL = "agent.tool.call"
    AGENT_TOOL_RESULT = "agent.tool.result"
    AGENT_STATE_CHANGE = "agent.state.change"
    
    # Document events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_FAILED = "document.processing.failed"
    
    # Module events
    MODULE_INSTALLED = "module.installed"
    MODULE_UNINSTALLED = "module.uninstalled"
    MODULE_ENABLED = "module.enabled"
    MODULE_DISABLED = "module.disabled"
    
    # AI events
    AI_REQUEST_STARTED = "ai.request.started"
    AI_REQUEST_COMPLETED = "ai.request.completed"
    AI_REQUEST_FAILED = "ai.request.failed"
    AI_PROVIDER_FALLBACK = "ai.provider.fallback"
    
    # Memory events
    MEMORY_CREATED = "memory.created"
    MEMORY_CONSOLIDATED = "memory.consolidated"
    MEMORY_DELETED = "memory.deleted"
    
    # Search events
    SEARCH_EXECUTED = "search.executed"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_CONFIG_CHANGE = "system.config.change"
```

---

## 8. QUEUE SYSTEM & ASYNC PROCESSING

[Content from original Section 11, unchanged]

_See original document Section 11 for Queue Architecture diagram and definitions._

### 8.1 Queue Implementation Strategy

| Stage | Implementation | Why |
|-------|---------------|-----|
| **MVP (Phase 0)** | Redis + RQ | Simple, same Redis, no additional dependency |
| **Growth** | Celery + Redis | More powerful, task scheduling, periodic tasks |
| **Scale** | RabbitMQ + Celery | Durable persistent queues, clustering |

---

## 9. MEMORY ARCHITECTURE (First-Class System)

### 9.1 Memory as a Core Platform Service

Memory is redesigned as a **first-class system** with six independent layers, each with distinct storage, retrieval, and consolidation strategies.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MEMORY ARCHITECTURE                               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L1: WORKING MEMORY (Current Session)                            │    │
│  │  • Active conversation context                                   │    │
│  │  • In-process, ephemeral                                         │    │
│  │  • Lost on session end                                           │    │
│  │  • Storage: Python dict (in-memory)                              │    │
│  │  • TTL: Session duration                                         │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L2: CONVERSATION MEMORY                                       │    │
│  │  • Full message history per conversation                        │    │
│  │  • Stored in PostgreSQL                                         │    │
│  │  • Retrieved by conversation_id                                 │    │
│  │  • TTL: Forever (user can delete)                               │    │
│  │  • Retrieval: Direct ID lookup + timestamp ordering             │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L3: PROJECT MEMORY                                             │    │
│  │  • Context specific to a project/workspace                      │    │
│  │  • Shared across team members in the project                    │    │
│  │  • Stored in PostgreSQL                                         │    │
│  │  • Includes: project files, decisions, key facts                │    │
│  │  • TTL: Project lifetime                                        │    │
│  │  • Retrieval: Project ID + semantic search                      │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L4: WORKSPACE MEMORY                                           │    │
│  │  • Organization/team-wide context                               │    │
│  │  • Shared knowledge base for the workspace                      │    │
│  │  • Stored in PostgreSQL + ChromaDB                              │    │
│  │  • Includes: team conventions, shared facts, pinned knowledge   │    │
│  │  • TTL: Workspace lifetime                                      │    │
│  │  • Retrieval: Semantic search with workspace filter             │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L5: LONG-TERM MEMORY                                           │    │
│  │  • User's accumulated knowledge across all sessions             │    │
│  │  • Summarized interactions (not raw logs)                       │    │
│  │  • Stored in ChromaDB as vector embeddings                      │    │
│  │  • TTL: Forever (with consolidation)                            │    │
│  │  • Retrieval: Semantic search with reranking                    │    │
│  │  • Consolidation: Cron job every 24 hours                       │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L6: KNOWLEDGE GRAPH MEMORY                                     │    │
│  │  • Entities and relationships extracted from conversations      │    │
│  │  • Stored in PostgreSQL (nodes + edges)                         │    │
│  │  • Supports graph traversal queries                             │    │
│  │  • "What does the user know about project X?"                   │    │
│  │  • TTL: Forever                                                  │    │
│  │  • Retrieval: Graph traversal + vector similarity search        │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Memory Interface

```python
# app/memory/interface.py

class MemoryType(str, Enum):
    WORKING = "working"
    CONVERSATION = "conversation"
    PROJECT = "project"
    WORKSPACE = "workspace"
    LONG_TERM = "long_term"
    KNOWLEDGE_GRAPH = "knowledge_graph"

class MemoryEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    memory_type: MemoryType
    scope_id: str  # user_id, conversation_id, project_id, or workspace_id
    content: str
    metadata: dict = {}
    embedding: list[float] | None = None
    importance: float = 0.5  # 0.0 to 1.0, for consolidation decisions
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

class MemoryQuery(BaseModel):
    query: str
    memory_types: list[MemoryType] = list(MemoryType)
    scope_id: str | None = None
    limit: int = 10
    min_importance: float = 0.0
    include_raw: bool = False  # If False, return summarized

class MemoryResult(BaseModel):
    entries: list[MemoryEntry]
    total_count: int
    query_time_ms: float

class MemoryEngine(ABC):
    """Central memory service. All modules use this interface."""
    
    @abstractmethod
    async def store(
        self,
        memory_type: MemoryType,
        scope_id: str,
        content: str,
        metadata: dict | None = None,
        importance: float = 0.5,
    ) -> UUID:
        """Store a memory entry."""
        pass
    
    @abstractmethod
    async def retrieve(self, query: MemoryQuery) -> MemoryResult:
        """Retrieve memories matching the query."""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: UUID) -> None:
        """Delete a specific memory."""
        pass
    
    @abstractmethod
    async def delete_scope(self, memory_type: MemoryType, scope_id: str) -> None:
        """Delete all memories for a scope (e.g., delete conversation)."""
        pass
    
    @abstractmethod
    async def consolidate(self, user_id: str) -> ConsolidationReport:
        """Run consolidation: summarize, extract entities, prune old."""
        pass
    
    @abstractmethod
    async def get_context(
        self,
        user_id: str,
        conversation_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> MemoryContext:
        """Get combined context from all relevant memory layers."""
        pass
```

### 9.3 Memory Implementation by Layer

| Layer | Storage | Retrieval | TTL | Consolidation |
|-------|---------|-----------|-----|---------------|
| **L1: Working** | In-memory dict | Direct key lookup | Session end | None |
| **L2: Conversation** | PostgreSQL (messages table) | SQL query by conversation_id | Forever | None |
| **L3: Project** | PostgreSQL (project_memories) | SQL + vector search | Project lifetime | None |
| **L4: Workspace** | PostgreSQL + ChromaDB | Vector search with filter | Workspace lifetime | Weekly duplicate removal |
| **L5: Long-term** | ChromaDB | Vector search + reranking | Forever | Daily summarization |
| **L6: Knowledge Graph** | PostgreSQL + PGVector | Graph traversal + vector | Forever | Weekly entity extraction |

### 9.4 Memory Consolidation Pipeline

```python
# app/memory/consolidation.py

class MemoryConsolidator:
    """Runs periodically to consolidate memories across layers."""
    
    async def consolidate_user(self, user_id: str) -> ConsolidationReport:
        """Full consolidation pipeline for a user."""
        
        # Step 1: Summarize recent conversations (L2 → L3/L5)
        recent_convs = await self._get_recent_conversations(user_id, hours=24)
        for conv in recent_convs:
            summary = await self._summarize_conversation(conv)
            importance = await self._assess_importance(summary)
            
            if importance > 0.7:
                # High importance → Long-term memory
                await self.memory.store(
                    MemoryType.LONG_TERM,
                    user_id,
                    summary,
                    {"source": "consolidation", "conversation_id": conv.id},
                    importance=importance,
                )
            
            # Always store in project context if applicable
            if conv.project_id:
                await self.memory.store(
                    MemoryType.PROJECT,
                    conv.project_id,
                    summary,
                    {"conversation_id": conv.id},
                    importance=importance,
                )
        
        # Step 2: Extract knowledge graph entities
        new_entities = await self._extract_entities(user_id, recent_convs)
        for entity in new_entities:
            await self.knowledge_graph.upsert_entity(entity)
        
        # Step 3: Prune low-importance memories (L5)
        await self._prune_low_importance(user_id, threshold=0.1)
        
        # Step 4: Detect and merge duplicates (L5)
        duplicates = await self._find_duplicates(user_id)
        for dup in duplicates:
            await self._merge_memories(dup.keep, dup.remove)
        
        return ConsolidationReport(
            conversations_summarized=len(recent_convs),
            entities_extracted=len(new_entities),
            memories_pruned=duplicates.pruned,
            memories_merged=duplicates.merged,
        )
```

### 9.5 Memory Retrieval Strategy

```python
# app/memory/retrieval.py

class MemoryRetriever:
    """Smart memory retrieval that selects the right strategy per memory type."""
    
    async def retrieve_context(
        self,
        query: str,
        user_id: str,
        conversation_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> MemoryContext:
        """Retrieve relevant context from all applicable memory layers."""
        
        context_parts = []
        
        # L1: Working memory (current conversation state)
        if conversation_id:
            working = await self.memory.retrieve(
                MemoryQuery(
                    memory_types=[MemoryType.WORKING],
                    scope_id=conversation_id,
                    query=query,
                    limit=5,
                )
            )
            context_parts.append(working)
        
        # L2: Conversation memory (this conversation's history)
        if conversation_id:
            conversation = await self.memory.retrieve(
                MemoryQuery(
                    memory_types=[MemoryType.CONVERSATION],
                    scope_id=conversation_id,
                    query=query,
                    limit=20,
                )
            )
            context_parts.append(conversation)
        
        # L3: Project memory
        if project_id:
            project = await self.memory.retrieve(
                MemoryQuery(
                    memory_types=[MemoryType.PROJECT],
                    scope_id=project_id,
                    query=query,
                    limit=5,
                )
            )
            context_parts.append(project)
        
        # L4: Workspace memory
        if workspace_id:
            workspace = await self.memory.retrieve(
                MemoryQuery(
                    memory_types=[MemoryType.WORKSPACE],
                    scope_id=workspace_id,
                    query=query,
                    limit=5,
                )
            )
            context_parts.append(workspace)
        
        # L5: Long-term memory (user's accumulated knowledge)
        long_term = await self.memory.retrieve(
            MemoryQuery(
                memory_types=[MemoryType.LONG_TERM],
                scope_id=user_id,
                query=query,
                limit=5,
                min_importance=0.3,
            )
        )
        context_parts.append(long_term)
        
        # L6: Knowledge graph
        graph = await self.knowledge_graph.query(
            query=query,
            user_id=user_id,
            limit=5,
        )
        context_parts.append(MemoryResult(
            entries=[MemoryEntry(
                memory_type=MemoryType.KNOWLEDGE_GRAPH,
                scope_id=user_id,
                content=str(e),
            ) for e in graph],
            total_count=len(graph),
            query_time_ms=0,
        ))
        
        return MemoryContext(
            parts=context_parts,
            assembled_at=datetime.utcnow(),
        )
```

---

## 10. SEARCH ENGINE

[Content from original Section 10, updated with hybrid search design]

_See original document for Search Architecture diagram and three-pronged search approach._

### 10.1 Search Interface

```python
# app/search/interface.py

class SearchQuery(BaseModel):
    query: str
    scope: Literal["all", "conversations", "documents", "agents", "code", "web"]
    filters: SearchFilters | None = None
    page: int = 1
    per_page: int = 20
    cursor: str | None = None  # Cursor-based pagination
    include_vectors: bool = True  # Enable/disable vector search

class SearchResult(BaseModel):
    id: str
    type: Literal["conversation", "message", "document", "agent", "web_page"]
    title: str
    snippet: str
    score: float  # Relevance score from fusion
    url: str | None = None
    metadata: dict = {}
    highlights: list[str] = []  # Matched text fragments

class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    next_cursor: str | None = None
    query_time_ms: float
    search_type: Literal["keyword", "vector", "hybrid"]
```

### 10.2 Hybrid Search with RRF

```python
# app/search/hybrid.py

class HybridSearchEngine:
    """Combines BM25 (keyword) + Vector (semantic) search with Reciprocal Rank Fusion."""
    
    def __init__(self, db, vector_db, config):
        self.keyword_search = KeywordSearchEngine(db)
        self.vector_search = VectorSearchEngine(vector_db)
        self.reranker = CrossEncoderReranker()  # Phase 2+
    
    async def search(self, query: SearchQuery) -> SearchResponse:
        start = time.monotonic()
        
        # 1. Classify query type
        search_type = self._classify_query(query.query)
        
        if search_type == "keyword":
            results = await self.keyword_search.search(query)
        elif search_type == "vector":
            results = await self.vector_search.search(query)
        else:
            # 2. Execute both searches in parallel
            keyword_task = self.keyword_search.search(query)
            vector_task = self.vector_search.search(query)
            keyword_results, vector_results = await asyncio.gather(
                keyword_task, vector_task
            )
            
            # 3. Reciprocal Rank Fusion
            results = self._rrf_fusion(
                keyword_results.results,
                vector_results.results,
                k=60,  # RRF constant
            )
        
        # 4. Rerank (Phase 2+)
        if self.reranker and len(results) > 5:
            results = await self.reranker.rerank(query.query, results)
        
        return SearchResponse(
            results=results[:query.per_page],
            total=len(results),
            next_cursor=self._encode_cursor(results, query.per_page),
            query_time_ms=(time.monotonic() - start) * 1000,
            search_type=search_type,
        )
    
    @staticmethod
    def _rrf_fusion(
        keyword_results: list[SearchResult],
        vector_results: list[SearchResult],
        k: int = 60,
    ) -> list[SearchResult]:
        """Reciprocal Rank Fusion combines rankings from two sources."""
        
        scores: dict[str, float] = {}
        result_map: dict[str, SearchResult] = {}
        
        for rank, result in enumerate(keyword_results, 1):
            scores[result.id] = scores.get(result.id, 0) + 1 / (k + rank)
            result_map[result.id] = result
        
        for rank, result in enumerate(vector_results, 1):
            scores[result.id] = scores.get(result.id, 0) + 1 / (k + rank)
            if result.id not in result_map:
                result_map[result.id] = result
        
        # Sort by fused score descending
        sorted_ids = sorted(scores.keys(), key=lambda id: scores[id], reverse=True)
        
        results = []
        for id in sorted_ids:
            result = result_map[id]
            result.score = scores[id]
            results.append(result)
        
        return results
```

---

## 11. AUTHENTICATION & AUTHORIZATION

### 11.1 Auth Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AUTH ARCHITECTURE                                   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    API Gateway / Middleware                       │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │    │
│  │  │  CORS        │  │  Rate Limit  │  │  Auth Middleware     │   │    │
│  │  │  Middleware  │  │  Middleware  │  │  (JWT validation)    │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │    │
│  │                          │              │                         │    │
│  │                          ▼              ▼                         │    │
│  │                    ┌──────────────────────────────────┐           │    │
│  │                    │  Router (permission check)       │           │    │
│  │                    └──────────────────────────────────┘           │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐   │
│  │  User Service │  │  Auth        │  │  API Key Service            │   │
│  │  (CRUD)       │  │  (JWT/OAuth) │  │  (create/revoke/validate)  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    Database                                       │    │
│  │  users | sessions | api_keys | roles | permissions               │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Auth Configuration (Phase 0)

```python
# app/auth/config.py

AUTH_CONFIG = {
    # Session management
    "max_sessions_per_user": 10,
    "session_invalidation_on_password_change": True,
    
    # Account security
    "max_login_attempts": 5,
    "lockout_duration_minutes": 15,
    "password_min_length": 12,
    "require_mfa": False,  # Interface ready, Phase 2 implementation
    
    # Token security
    "access_token_expire_minutes": 15,
    "refresh_token_expire_days": 7,
    "jwt_secret_rotation_interval_days": 90,
    
    # Rate limiting
    "rate_limit_login_per_minute": 10,
    "rate_limit_register_per_hour": 3,  # Per IP
    "rate_limit_api_per_minute": 60,  # Per authenticated user
    
    # API keys
    "api_key_prefix": "mmx_",
    "api_key_max_per_user": 10,
    
    # OAuth (interface defined, Phase 2 implementation)
    "oauth_providers": {
        "google": {"enabled": False},
        "github": {"enabled": False},
        "microsoft": {"enabled": False},
    },
}

# Enterprise SSO interface (designed now, implemented Phase 15)
class SSOProvider(ABC):
    @abstractmethod
    async def authenticate(self, token: str) -> UserInfo: ...
    @abstractmethod
    async def validate_session(self, session_id: str) -> bool: ...
    @abstractmethod
    async def get_groups(self, user_id: str) -> list[str]: ...
```

---

## 12. DATABASE DESIGN

### 12.1 Core Schema (Phase 0)

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,  -- SHA-256 hash
    key_prefix VARCHAR(10) NOT NULL, -- First 10 chars for identification
    permissions JSONB DEFAULT '["read"]',
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);

-- Conversations (Phase 1)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    model VARCHAR(255),
    folder_id UUID,
    is_pinned BOOLEAN DEFAULT false,
    is_shared BOOLEAN DEFAULT false,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Cursor pagination support
    sort_key TIMESTAMPTZ DEFAULT NOW()  -- For stable cursor-based pagination
);

CREATE INDEX idx_conversations_user_sort 
    ON conversations(user_id, sort_key DESC);
CREATE INDEX idx_conversations_folder 
    ON conversations(folder_id);
CREATE INDEX idx_conversations_search 
    ON conversations USING GIN(to_tsvector('english', title));

-- Messages (Phase 1)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system, tool
    content TEXT NOT NULL,
    model VARCHAR(255),
    tokens INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- For cursor pagination within conversations
    sort_key TIMESTAMPTZ DEFAULT NOW()  
);

CREATE INDEX idx_messages_conversation 
    ON messages(conversation_id, sort_key);

-- Memory tables (Phase 6, schema designed now)
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type VARCHAR(50) NOT NULL,  -- working, conversation, project, workspace, long_term
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scope_id VARCHAR(255) NOT NULL,  -- conversation_id, project_id, or workspace_id
    content TEXT NOT NULL,
    summary TEXT,  -- For long-term memory
    importance FLOAT DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    embedding_id VARCHAR(255),  -- Reference to vector in ChromaDB
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memory_user_type ON memory_entries(user_id, memory_type);
CREATE INDEX idx_memory_scope ON memory_entries(scope_id);
CREATE INDEX idx_memory_importance ON memory_entries(importance DESC);

-- Knowledge Graph (Phase 6, schema designed now)
CREATE TABLE knowledge_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,  -- concept, person, project, technology
    name VARCHAR(500) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    embedding_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_user ON knowledge_nodes(user_id);
CREATE INDEX idx_knowledge_type ON knowledge_nodes(entity_type);

CREATE TABLE knowledge_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relationship VARCHAR(100) NOT NULL,  -- relates_to, depends_on, implements
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_node_id, target_node_id, relationship)
);

-- Event journal (for event bus persistence)
CREATE TABLE event_journal (
    id UUID PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    source VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_event_journal_topic ON event_journal(topic);
CREATE INDEX idx_event_journal_ts ON event_journal(timestamp);

-- Dead letter queue
CREATE TABLE dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL,
    topic VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    source VARCHAR(255) NOT NULL,
    error TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log (Phase 15, schema designed now)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID,
    user_id UUID,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);

-- Organizations (Phase 12, schema designed now)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    tier VARCHAR(50) DEFAULT 'free',  -- free, team, enterprise
    max_users INTEGER DEFAULT 5,
    max_storage_bytes BIGINT DEFAULT 1073741824,  -- 1GB default
    features JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',  -- owner, admin, member
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);
```

### 12.2 Migration Strategy

```python
# alembic/env.py
# Use linear sequential migrations. No branching in Phase 0.

# Migration naming convention:
# 0001_initial_schema.py
# 0002_add_conversations.py
# 0003_add_messages.py
# 0004_add_memory_tables.py
# 0005_add_knowledge_graph.py
# 0006_add_audit_logs.py
# 0007_add_organizations.py

# Each migration is reversible:
# upgrade() → apply migration
# downgrade() → revert migration
```

---

## 13. API DESIGN & VERSIONING

### 13.1 API Design Principles

- **RESTful** for CRUD operations
- **WebSocket** for real-time events
- **SSE (Server-Sent Events)** for streaming AI responses (normalized format)
- **Cursor-based pagination** for all list endpoints
- **Consistent error format** across all endpoints
- **API versioning** via URL prefix (`/api/v1/`)

### 13.2 Cursor-Based Pagination

```python
# All list endpoints use cursor-based pagination for stable results

# Request:
GET /api/v1/conversations?cursor=20260711T213000Z&limit=20

# Response:
{
    "success": true,
    "data": [...],
    "meta": {
        "next_cursor": "20260710T120000Z",  # Cursor for next page
        "has_more": true,
        "limit": 20
    }
}

# Why cursor over page/page:
# - New items don't shift page boundaries
# - Consistent results during pagination
# - No duplicate or missed items
# - Better performance (cursor uses indexed column)

# Implementation:
# Cursor = sort_key of the last item in current page
# Query: WHERE sort_key < cursor ORDER BY sort_key DESC LIMIT limit
```

### 13.3 Streaming SSE Format (Provider-Agnostic)

```python
# Every streaming endpoint returns normalized SSE events:

# event: token
# data: {"type": "token", "content": "Hello", "model": "qwen3:4b", "provider": "ollama"}

# event: token
# data: {"type": "token", "content": " world", "model": "qwen3:4b", "provider": "ollama"}

# event: done
# data: {"type": "done", "finish_reason": "stop", "usage": {"total_tokens": 42}}

# event: error
# data: {"type": "error", "error_code": "provider_timeout", "error_message": "..."}
```

### 13.4 Endpoint Structure

```
# Core
GET    /api/v1/health                          → Health check (readiness)
GET    /api/v1/ready                           → Readiness check (deps ready)
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

# Conversations (cursor paginated)
GET    /api/v1/conversations?cursor=&limit=    → List conversations
POST   /api/v1/conversations                   → Create conversation
GET    /api/v1/conversations/{id}              → Get conversation
PATCH  /api/v1/conversations/{id}              → Update conversation
DELETE /api/v1/conversations/{id}              → Delete conversation
POST   /api/v1/conversations/{id}/messages     → Add message
GET    /api/v1/conversations/{id}/messages?cursor=&limit=
POST   /api/v1/conversations/{id}/share        → Share conversation
DELETE /api/v1/conversations/{id}/share        → Unshare conversation

# Chat
POST   /api/v1/chat/completions                → Chat (non-streaming)
POST   /api/v1/chat/stream                     → Chat (streaming SSE - normalized)
GET    /api/v1/models                          → List available models
GET    /api/v1/capabilities                    → List all capabilities (dynamic)
POST   /api/v1/chat/route                      → Route to best model

# Documents
POST   /api/v1/documents/upload                → Upload document(s)
GET    /api/v1/documents?cursor=&limit=        → List documents
GET    /api/v1/documents/{id}                  → Get document details
DELETE /api/v1/documents/{id}                  → Delete document
POST   /api/v1/documents/{id}/process          → (Re)process document
POST   /api/v1/documents/chat                  → Chat with documents

# Agents
GET    /api/v1/agents?cursor=&limit=           → List agents
POST   /api/v1/agents                          → Create agent
GET    /api/v1/agents/{id}                     → Get agent
PATCH  /api/v1/agents/{id}                     → Update agent
DELETE /api/v1/agents/{id}                     → Delete agent
POST   /api/v1/agents/{id}/run                 → Execute agent
GET    /api/v1/agents/{id}/runs?cursor=&limit= → Get agent run history
GET    /api/v1/agents/{id}/state               → Get agent state machine status

# Memory
POST   /api/v1/memory/store                    → Store memory entry
POST   /api/v1/memory/retrieve                 → Query memory
DELETE /api/v1/memory/{id}                     → Delete memory
POST   /api/v1/memory/consolidate              → Trigger consolidation
GET    /api/v1/memory/context                  → Get assembled context

# Search
POST   /api/v1/search                          → Search across all scopes

# Voice (Phase 7)
POST   /api/v1/voice/stt                       → Speech-to-text
POST   /api/v1/voice/tts                       → Text-to-speech

# Plugins (Phase 11 - interface deployed now)
GET    /api/v1/plugins                         → List plugins
POST   /api/v1/plugins/install                 → Install plugin
POST   /api/v1/plugins/{id}/enable             → Enable plugin
POST   /api/v1/plugins/{id}/disable            → Disable plugin
DELETE /api/v1/plugins/{id}                    → Uninstall plugin

# Settings
GET    /api/v1/settings                        → Get all settings
PATCH  /api/v1/settings                        → Update settings

# Admin
GET    /api/v1/admin/users?cursor=&limit=      → List all users (admin)
GET    /api/v1/admin/stats                     → System statistics
GET    /api/v1/admin/logs                      → System logs
```

### 13.5 Common Response Format

```python
# Success
{
    "success": true,
    "data": { ... },
    "meta": {
        "next_cursor": "...",  # Cursor-based pagination
        "has_more": false,
        "limit": 50
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

## 14. CACHE ARCHITECTURE & OFFLINE STRATEGY

### 14.1 Caching Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CACHE ARCHITECTURE                                  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L1: Browser Cache (CDN)                                       │    │
│  │  • Static assets (JS, CSS, images) → 1 year TTL                │    │
│  │  • API responses with ETag headers (GET only)                   │    │
│  │  • Service Worker cache for offline support                     │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L2: Application Cache (Redis)                                 │    │
│  │  • Model capabilities registry → 1 hour TTL                    │    │
│  │  • User session data → 15 minute TTL                           │    │
│  │  • API response cache (GET only) → 5 minute TTL                │    │
│  │  • Rate limit counters → variable TTL                          │    │
│  │  • Conversation list (metadata) → 1 minute TTL                 │    │
│  │  • Configuration / settings → 10 minute TTL                    │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L3: Database Cache (PostgreSQL)                                │    │
│  │  • Materialized views for dashboard stats                       │    │
│  │  • Frequent aggregates (usage metrics)                          │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  L4: Offline Cache (IndexedDB - PWA)                            │    │
│  │  • Recent conversations (last 50)                               │    │
│  │  • User profile + preferences                                   │    │
│  │  • Cached model list                                            │    │
│  │  • Queued messages (for background sync)                        │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 14.2 PWA / Offline Strategy

```typescript
// frontend/service-worker.ts (Phase 0 skeleton)

const CACHE_STRATEGIES = {
    // Cache-first: Static assets (JS, CSS, fonts, images)
    staticAssets: new CacheFirst({
        cacheName: 'static-assets-v1',
        maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
    }),
    
    // Network-first: API responses
    apiResponses: new NetworkFirst({
        cacheName: 'api-cache-v1',
        maxAgeSeconds: 5 * 60, // 5 minutes
        backgroundSync: true, // Queue failed writes
    }),
    
    // Stale-while-revalidate: Model list, settings
    modelData: new StaleWhileRevalidate({
        cacheName: 'model-cache-v1',
        maxAgeSeconds: 60 * 60, // 1 hour
    }),
};

// Background sync queue for offline messages
const syncQueue = new BackgroundSyncQueue('message-queue', {
    maxRetentionTime: 24 * 60, // 24 hours in minutes
    onSync: async (entry) => {
        await fetch('/api/v1/chat/completions', {
            method: 'POST',
            body: JSON.stringify(entry.data),
        });
    },
});
```

---

## 15. STORAGE ARCHITECTURE

[Content from original Section 13, unchanged]

---

## 16. SECURITY ARCHITECTURE

### 16.1 Prompt Injection Detection

```python
# app/security/prompt_guard.py

class PromptGuard:
    """Detect and block prompt injection attempts."""
    
    # Phase 0: Pattern-based detection
    # Phase 2+: ML-based detection with fine-tuned model
    
    BLOCKED_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|commands)",
        r"forget\s+(all\s+)?(previous|prior)\s+(instructions|prompts)",
        r"you\s+are\s+not\s+bound\s+by",
        r"you\s+are\s+no\s+longer",
        r"system\s+prompt",
        r"你是一个",  # Chinese jailbreak attempts
        r"override\s+(your\s+)?(rules|guidelines|constraints)",
        r"disregard\s+(all\s+)?(rules|guidelines|constraints)",
        r"(DAN|do\s+anything\s+now)",
    ]
    
    @classmethod
    async def check(cls, messages: list[Message]) -> SafetyResult:
        """Check all messages for prompt injection."""
        for msg in messages:
            if msg.role == "user":
                for pattern in cls.BLOCKED_PATTERNS:
                    if re.search(pattern, msg.content, re.IGNORECASE):
                        return SafetyResult(
                            safe=False,
                            reason=f"Blocked pattern: {pattern}",
                            severity="high",
                        )
        
        return SafetyResult(safe=True)

class SafetyResult(BaseModel):
    safe: bool
    reason: str | None = None
    severity: Literal["low", "medium", "high"] | None = None
    action: Literal["allow", "block", "flag"] = "allow"
```

### 16.2 Security Checklist (Phase 0)

- [x] Environment variable validation at startup
- [x] CORS configured for production domains only
- [x] Rate limiting middleware (auth endpoints + API)
- [x] Request size limits on all endpoints
- [x] File upload validation (type whitelist, max size)
- [x] HTTPS enforcement
- [x] HSTS headers
- [x] Content Security Policy headers
- [x] XSS protection headers
- [x] SQL injection prevention (ORM usage, no raw queries)
- [x] JWT secret rotation support
- [x] Audit logging for auth events
- [x] Prompt injection detection (Phase 0: pattern-based)
- [x] Password strength enforcement (min 12 chars)
- [x] Account lockout after 5 failed attempts
- [ ] Secrets management (Phase 2: Vault integration)
- [ ] Dependency vulnerability scanning (CI)
- [ ] Penetration testing (Phase 2)
- [ ] GDPR data export/deletion (Phase 2)

---

## 17. FRONTEND ARCHITECTURE

### 17.1 Frontend Stack

- **Framework:** Next.js 14 (App Router)
- **UI:** Shadcn UI + Tailwind CSS
- **State:** Zustand (global) + TanStack Query (server state)
- **SSR Strategy:**
  - SSR: Dashboard, Settings (SEO needed, fast initial load)
  - CSR: Chat, Agents (interactive, streaming)
  - ISR: Documentation, Blog

### 17.2 Streaming UI Pattern

```typescript
// hooks/useStreamingChat.ts

interface UseStreamingChatOptions {
    onToken: (token: string) => void;
    onDone: (usage: Usage) => void;
    onError: (error: Error) => void;
}

function useStreamingChat(options: UseStreamingChatOptions) {
    const abortRef = useRef<AbortController>();
    
    const sendMessage = useCallback(async (messages: Message[]) => {
        abortRef.current = new AbortController();
        
        const response = await fetch('/api/v1/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages, stream: true }),
            signal: abortRef.current.signal,
        });
        
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const event = JSON.parse(line.slice(6));
                    switch (event.type) {
                        case 'token':
                            options.onToken(event.content);
                            break;
                        case 'done':
                            options.onDone(event.usage);
                            break;
                        case 'error':
                            options.onError(new Error(event.error_message));
                            break;
                    }
                }
            }
        }
    }, [options]);
    
    const cancel = useCallback(() => {
        abortRef.current?.abort();
    }, []);
    
    return { sendMessage, cancel };
}
```

### 17.3 Module Federation (Architecture Only, Phase 10+ Implementation)

```typescript
// Module Federation interface (designed now, not implemented)
// Each module is a remote entry that can be dynamically loaded

interface ModuleFederationConfig {
    name: string;          // Module identifier
    exposes: {
        [key: string]: string;  // Component name → file path
    };
    shared: string[];     // Shared dependencies (react, zustand, etc.)
}

// Future: Webpack 5 ModuleFederationPlugin
// Each module becomes independently deployable micro-frontend
// Phase 0: Route-based code splitting (dynamic imports)
// Phase 10+: Module federation for independent deployments
```

### 17.4 Error Boundary Strategy

```typescript
// components/ModuleErrorBoundary.tsx (Phase 0)

class ModuleErrorBoundary extends React.Component<
    { moduleName: string; fallback?: React.ReactNode },
    { hasError: boolean; error?: Error }
> {
    state = { hasError: false };
    
    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }
    
    componentDidCatch(error: Error, info: React.ErrorInfo) {
        // Log to monitoring service
        logger.error(`Module ${this.props.moduleName} crashed`, {
            error: error.message,
            componentStack: info.componentStack,
        });
    }
    
    render() {
        if (this.state.hasError) {
            return this.props.fallback || (
                <div className="module-error">
                    <h3>Module Error: {this.props.moduleName}</h3>
                    <p>{this.state.error?.message}</p>
                    <button onClick={() => this.setState({ hasError: false })}>
                        Retry
                    </button>
                </div>
            );
        }
        
        return this.props.children;
    }
}
```

### 17.5 PWA Manifest

```json
{
    "name": "Multimax AI Hub",
    "short_name": "Multimax",
    "description": "AI Operating System - Unified workspace for chat, coding, research, and automation",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0a0a0a",
    "theme_color": "#0a0a0a",
    "icons": [
        { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
        { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
    ],
    "categories": ["productivity", "developer-tools", "artificial-intelligence"],
    "screenshots": [...]
}
```

---

## 18. DEPLOYMENT ARCHITECTURE & ENTERPRISE INTERFACES

### 18.1 Single-Server Deployment (MVP)

[Content from original Section 15.1, Docker Compose configuration with health checks]

### 18.2 Enterprise Interfaces (Designed Now, Implemented Phase 15)

```python
# app/enterprise/interfaces.py (designed, not implemented)

class TenantIsolation(ABC):
    """Multi-tenant data isolation strategy."""
    
    @abstractmethod
    async def get_tenant_id(self, request: Request) -> str:
        """Extract tenant identifier from request."""
        pass
    
    @abstractmethod
    async def filter_by_tenant(self, query: Query, tenant_id: str) -> Query:
        """Add tenant filter to all database queries."""
        pass

class AuditLogger(ABC):
    """Enterprise audit logging interface."""
    
    @abstractmethod
    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        metadata: dict | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> None:
        """Log an auditable action."""
        pass

class ComplianceManager(ABC):
    """Compliance framework interface."""
    
    @abstractmethod
    async def create_data_export(self, user_id: str) -> str:
        """GDPR data export. Returns download URL."""
        pass
    
    @abstractmethod
    async def delete_user_data(self, user_id: str) -> None:
        """GDPR right to be forgotten."""
        pass
    
    @abstractmethod
    async def get_data_retention_policy(self) -> RetentionPolicy:
        """Get current retention policy."""
        pass

class BillingTracker(ABC):
    """Usage tracking for enterprise billing."""
    
    @abstractmethod
    async def track_usage(
        self,
        organization_id: str,
        metric: str,  # "api_calls", "tokens", "storage_bytes", "active_users"
        value: int,
    ) -> None:
        """Track a usage metric."""
        pass
    
    @abstractmethod
    async def get_current_usage(
        self,
        organization_id: str,
        metric: str,
        period: Literal["day", "month", "year"],
    ) -> int:
        """Get current usage for billing."""
        pass
```

---

## 19. MONITORING, OBSERVABILITY & LOGGING

[Content from original Section 18, unchanged]

---

## 20. TESTING STRATEGY & PHASE GATES

### 20.1 Testing Pyramid

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

### 20.2 Test Coverage Goals

| Layer | Coverage Target | Tools |
|-------|-----------------|-------|
| **Backend Services** | 90%+ | pytest, pytest-asyncio |
| **Backend Routes** | 85%+ | FastAPI TestClient |
| **Frontend Components** | 75%+ | vitest, React Testing Library |
| **Frontend Hooks** | 90%+ | vitest, @testing-library/react-hooks |
| **E2E Flows** | Critical paths | Playwright |

### 20.3 Test Organization

```python
# backend/tests/
# ├── unit/           # Fast tests, no dependencies
# │   ├── test_ai_router.py
# │   ├── test_event_bus.py
# │   └── test_memory_engine.py
# ├── integration/    # Require PostgreSQL + Redis
# │   ├── test_api.py
# │   ├── test_auth.py
# │   └── test_chat_flow.py
# ├── performance/    # k6 or locust scripts
# │   ├── scenarios/
# │   └── reports/
# ├── security/       # bandit, safety, owasp
# │   ├── test_prompt_injection.py
# │   └── test_rate_limiting.py
# └── conftest.py     # Fixtures: app, db, auth, etc.
```

---

## 21. CI/CD PIPELINE

### 21.1 CI/CD Architecture

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # === LINTING ===
  lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install ruff mypy
      - run: ruff check backend/ --output-format=github
      - run: mypy backend/ --strict

  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check

  # === SECURITY SCAN ===
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit safety
      - run: bandit -r backend/ -f json -o bandit-report.json
      - run: safety check -r backend/requirements.txt

  # === TESTS ===
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_DB: multimax_test, POSTGRES_PASSWORD: test }
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: pip install -r backend/requirements-dev.txt
      - run: pytest backend/tests/ -m "not nightly" --cov=backend/ --cov-report=xml
      - uses: codecov/codecov-action@v4

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run test -- --coverage
      - uses: codecov/codecov-action@v4

  # === BUILD ===
  docker-build:
    if: github.ref == 'refs/heads/main'
    needs: [test-backend, test-frontend, lint-backend, lint-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t multimax/backend -f docker/Dockerfile.backend .
      - run: docker build -t multimax/frontend -f docker/Dockerfile.frontend .
      - run: |
          docker tag multimax/backend ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
          docker tag multimax/frontend ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
      - run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
      - run: docker push ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
      - run: docker push ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
```

### 21.2 Environment Promotion

```
develop ──▶ CI: lint + test + security
    │
    ├──▶ staging ──▶ CI: full test suite + integration tests
    │       │
    │       ├──▶ Manual approval
    │       │
    │       ▼
    └──▶ production ──▶ CI: deploy + smoke tests
```

---

## 22. SCALABILITY & FUTURE-PROOFING

[Content from original Section 20, updated with scalability runway table]

### 22.1 Horizontal Scaling Strategy

| Component | Scaling Strategy | When to Scale |
|-----------|-----------------|---------------|
| **Frontend** | CDN caching + multiple replicas | 10K+ concurrent users |
| **Backend API** | Stateless replicas behind load balancer | 1K+ QPS |
| **PostgreSQL** | Read replicas + PgBouncer | 5K+ concurrent connections |
| **Redis** | Redis Cluster with sharding | 100K+ cache keys |
| **ChromaDB** | Distributed deployment with replication | 10M+ vectors |
| **Task Queue** | More workers, separate queues | 100K+ daily tasks |
| **File Storage** | S3-compatible object store (MinIO) | 100GB+ stored files |

### 22.2 Scalability Thresholds

```python
SCALABILITY_THRESHOLDS = {
    "users": {
        "single_db": (0, 10000),
        "read_replicas": (10000, 100000),
        "sharding": (100000, 1000000),
    },
    "vectors": {
        "chroma_single": (0, 1000000),
        "chroma_cluster": (1000000, 10000000),
        "qdrant_distributed": (10000000, None),
    },
    "file_storage": {
        "local": (0, 100 * 1024 * 1024),  # 100MB
        "minio": (100 * 1024 * 1024, 100 * 1024 * 1024 * 1024),  # 100MB-100GB
        "r2_cloudflare": (100 * 1024 * 1024 * 1024, None),  # 100GB+
    }
}
```

---

## 23. TECHNOLOGY STACK & RATIONALE

[Content from original Section 21, unchanged]

---

## 24. 5-YEAR PRODUCT ROADMAP

[Content from original Section 22, updated with architecture phase]

### 24.1 Architecture vs Implementation Timeline

```
MONTH 1-2: ARCHITECTURE PHASE ✓ (COMPLETE)
  ├── All interfaces designed
  ├── Extension points defined
  ├── Contracts specified
  ├── Schema designed (including future tables)
  ├── Enterprise interfaces defined
  ├── Plugin architecture designed
  ├── Marketplace interfaces defined
  └── Version 1.0 FROZEN

MONTH 3-4: PHASE 0 IMPLEMENTATION
  ├── Foundation: DI container, Event Bus, Config
  ├── Auth: Registration, Login, JWT, API Keys
  ├── Database: Schema, Migrations, Indexes
  ├── Infrastructure: Docker, CI/CD, Dev Container
  └── Deployment: Single-server Docker Compose

MONTH 5-6: PHASE 1 — AI Chat
  ├── Provider abstraction (Ollama + OpenAI)
  ├── Streaming with normalized SSE
  ├── Conversation management
  ├── Model selection + routing
  └── Frontend chat UI
```

### 24.2 Detailed Phase Breakdown

[Original phase content with the following updates:]
- Phase 11 (Plugin): Implementation begins, architecture already exists
- Phase 13 (Marketplace): Implementation begins, interfaces already exist
- Phase 12 (Team): Implementation begins, organization schema already exists
- Phase 15 (Enterprise): Implementation begins, interfaces already defined

---

## 25. RISK REGISTER & MITIGATION

### 25.1 Updated Risk Register

| ID | Risk | Prob | Impact | Mitigation |
|----|------|------|--------|------------|
| **R1** | Ollama cannot run on user hardware | High | Medium | AI Router supports cloud fallback; users connect own API keys |
| **R2** | ChromaDB performance degrades at scale | Medium | High | Storage abstraction allows swap to Qdrant; monitor vector count |
| **R3** | PostgreSQL becomes bottleneck | Medium | High | Read replicas + PgBouncer; schema designed for sharding from day 1 |
| **R4** | Frontend bundle size grows too large | Medium | Medium | Code splitting + dynamic imports + module federation interface |
| **R5** | Plugin security vulnerabilities | Medium | High | Three-tier plugin sandbox designed; capability permission model |
| **R6** | Community fragmentation (forks) | Low | Medium | Strong governance model; capability manifest ensures compatibility |
| **R7** | Python backend performance at scale | Medium | High | Stateless design enables horizontal scaling; Go/Rust extraction path for critical services |
| **R8** | Memory/storage costs at scale | Medium | Medium | Layered memory with TTL + consolidation; R2/B2 for zero-egress storage |
| **R9** | Feature creep / scope expansion | High | Medium | Strict phase gates (tests + docs + performance + security + refactoring) required before each phase completion |
| **R10** | Key developer departure | Medium | High | Comprehensive docs, code reviews, CI/CD, pre-commit hooks enforce standards |
| **R11** | AI model provider API changes | Medium | Medium | Provider abstraction layer isolates changes to single adapter |
| **R12** | Async event bus complexity | Medium | Low | Phase 0 uses simple PG journal + in-process delivery; upgrades to Kafka only when needed |

---

## 26. PHASE COMPLETION GATES

Every phase must pass ALL five gates before the next phase begins:

### Gate 1: Tests

- [ ] All unit tests pass (≥90% coverage for services)
- [ ] All integration tests pass (API endpoints)
- [ ] No flaky tests (run 3x consecutively)
- [ ] API contract tests pass (OpenAPI validation)
- [ ] Critical E2E flows pass

### Gate 2: Documentation

- [ ] API endpoints documented (auto-generated from code)
- [ ] Architecture Decision Records (ADRs) for significant decisions
- [ ] README updated with new features
- [ ] Configuration documentation (environment variables)
- [ ] Database schema documented (if new tables added)
- [ ] Module manifest documented (if new module added)

### Gate 3: Performance Review

- [ ] API response times within budget (<200ms non-AI, <2s first token)
- [ ] No N+1 query patterns
- [ ] Database indexes verified with `EXPLAIN ANALYZE`
- [ ] Frontend bundle size checked (<200KB initial)
- [ ] Lighthouse score ≥90 (Performance, Accessibility, Best Practices)
- [ ] No memory leaks in long-running processes

### Gate 4: Security Review

- [ ] No secrets hardcoded (verified by secret scanner)
- [ ] Input validation on all new endpoints
- [ ] Rate limiting configured for new endpoints
- [ ] Prompt injection check (if AI-facing)
- [ ] CORS configured correctly
- [ ] Authentication required for all protected endpoints
- [ ] Permission check on all data-accessing endpoints
- [ ] SQL injection not possible (ORM used, no raw queries)
- [ ] Dependency vulnerability scan passes

### Gate 5: Refactoring Review

- [ ] No TODO/FIXME comments in production code (issues created instead)
- [ ] No dead code (unused imports, functions, variables)
- [ ] No overly complex functions (cyclomatic complexity <10)
- [ ] No large files (>500 lines) — extract modules
- [ ] Follows naming conventions (PEP8 for Python, ESLint for TS)
- [ ] No duplicated logic (DRY principle)
- [ ] Type hints on all new functions
- [ ] Docstrings on all public APIs

---

## 27. VERSION 1.0 FREEZE

### 27.1 What Freezing Means

Version 1.0 of the Software Architecture Document is now **frozen**.

- No new architectural interfaces will be added
- No existing interfaces will be modified
- No extension points will be removed
- Schema definitions are locked

### 27.2 Change Process

If a change to a frozen interface is required:

1. **Document the need** — What problem requires the change?
2. **Assess impact** — Which existing/planned modules are affected?
3. **Propose change** — Updated interface specification
4. **Review** — Principal engineer review
5. **Version bump** — v1.0 → v1.1 (with migration guide)

### 27.3 What is Frozen

| Artifact | Status | Change Required |
|----------|--------|----------------|
| Core interfaces (Module, Plugin, Event) | FROZEN | v1.x bump |
| Provider abstraction | FROZEN | v1.x bump |
| Memory architecture (6 layers) | FROZEN | v1.x bump |
| Capability manifest schema | FROZEN | v1.x bump |
| API endpoint structure | FROZEN | v1.x bump |
| Database schema (core + future tables) | FROZEN | v1.x bump |
| Event topics | FROZEN | v1.x bump |
| Module manifest schema | FROZEN | v1.x bump |
| Plugin interface | FROZEN | v1.x bump |
| Enterprise interfaces | FROZEN | v1.x bump |
| Streaming format (SSE) | FROZEN | v1.x bump |
| Response format | FROZEN | v1.x bump |
| Phase gate checklist | FROZEN | v2.0 |
| Phase implementation (code) | IMPLEMENTATION | Changes expected |

---

## 28. APPENDICES

### Appendix A: Glossary

[Content from original Appendix A, updated]

| Term | Definition |
|------|------------|
| **Architecture** | Interfaces, contracts, abstractions, extension points (frozen at v1.0) |
| **Implementation** | Concrete code, database queries, UI components (built per phase) |
| **Module** | An independently deployable unit of functionality with manifest, schema, and capability declarations |
| **Plugin** | A package that extends the system with new capabilities (interface defined, implementation Phase 11) |
| **Capability Manifest** | Published by every module. Declares what the module can do. Enables dynamic discovery by AI Router and Marketplace. |
| **AI Router** | Core abstraction layer that decouples all consumers from AI model providers. Routes based on capability manifests. |
| **Agent** | An autonomous program with defined state machine (draft→active→queued→running→paused→completed→failed) |
| **Event Bus** | Publish-subscribe system with persistence (PostgreSQL), retry, and dead letter queue |
| **Memory** | First-class system with 6 layers (Working, Conversation, Project, Workspace, Long-term, Knowledge Graph) |
| **Extension Point** | A defined hook where plugins can inject behavior (e.g., `chat.before_send`, `chat.after_receive`) |
| **Phase Gate** | Mandatory quality checklist (Tests, Docs, Performance, Security, Refactoring) completed before each phase |

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
APP_VERSION=1.0.0
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

# Rate Limiting
RATE_LIMIT_LOGIN_PER_MINUTE=10
RATE_LIMIT_API_PER_MINUTE=60

# Memory
MEMORY_EPISODIC_TTL_HOURS=24
MEMORY_CONSOLIDATION_INTERVAL_HOURS=24
```

### Appendix C: Git Branching Strategy

```
main                    # Production-ready code
  ├── develop           # Integration branch
  │   ├── feature/*     # Feature branches (one per phase or sub-task)
  │   ├── bugfix/*      # Bug fixes
  │   └── refactor/*    # Refactoring
  ├── release/*         # Release candidates (v1.0, v1.1, etc.)
  └── hotfix/*          # Emergency production fixes
```

### Appendix D: Code Review Checklist

- [ ] Follows the architecture (interfaces defined in v1.0 are used, not bypassed)
- [ ] No hardcoded secrets or configuration
- [ ] Dependency injection used (no direct imports of other modules)
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
- [ ] Phase gate checklist complete
- [ ] Architecture Decision Record (ADR) created for significant decisions

### Appendix E: Architecture Decision Record (ADR) Template

```markdown
# ADR-{NNN}: {Title}

**Status:** Proposed | Accepted | Deprecated | Superseded

**Date:** {YYYY-MM-DD}

## Context
{What is the issue that we're seeing that motivates this decision?}

## Decision
{What is the change that we're proposing and/or doing?}

## Consequences
{What becomes easier or more difficult to do because of this change?}

## Compliance
{How will we verify this decision is followed?}
```

### Appendix F: ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | Architecture vs Implementation distinction | Accepted | 2026-07-11 |
| ADR-002 | Six-layer Memory Architecture | Accepted | 2026-07-11 |
| ADR-003 | Capability Manifest for dynamic discovery | Accepted | 2026-07-11 |
| ADR-004 | Plugin interfaces defined now, implemented Phase 11 | Accepted | 2026-07-11 |
| ADR-005 | Dependency Injection Container (python-dependency-injector) | Accepted | 2026-07-11 |
| ADR-006 | Persistent Event Bus with PostgreSQL journal | Accepted | 2026-07-11 |
| ADR-007 | Provider-agnostic SSE streaming format | Accepted | 2026-07-11 |
| ADR-008 | Cursor-based pagination for all list endpoints | Accepted | 2026-07-11 |
| ADR-009 | Agent lifecycle state machine | Accepted | 2026-07-11 |
| ADR-010 | Phase completion gates (Tests, Docs, Perf, Security, Refactoring) | Accepted | 2026-07-11 |
| ADR-011 | Enterprise interfaces designed now, implemented Phase 15 | Accepted | 2026-07-11 |
| ADR-012 | Version 1.0 Freeze | Accepted | 2026-07-11 |

---

## DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-07-11 | Principal Architect | Initial draft covering all architecture areas |
| **1.0.0** | **2026-07-11** | **Principal Architect** | **FROZEN: Added architecture vs implementation distinction, 6-layer memory, capability manifests, DI container, persistent event bus, streaming abstraction, agent state machine, cursor pagination, plugin interfaces, enterprise interfaces, CI/CD, offline strategy, phase gates, ADR system** |

---

**VERSION 1.0 — FROZEN**

*No architectural interfaces will be modified without a version bump and migration guide.*
*All implementation can now proceed according to the phased roadmap.*
*Every phase must pass all five gates before the next phase begins.*

*"Multimax AI Hub is the AI Operating System where one workspace unifies chat, coding, research, documents, agents, and automation across multiple AI models, so users don't have to jump between different AI tools."*