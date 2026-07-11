# Multimax AI Hub

> **The world's most powerful free AI Operating System.**
>
> One platform to replace ChatGPT, Claude, Cursor, Copilot, Perplexity, NotebookLM, Browser Use, n8n, and Open WebUI.

---

## Vision

Build the world's most powerful free AI Operating System by combining the best open-source AI technologies into one unified platform.

Instead of users opening multiple AI tools separately, they should only need **one application**: **Multimax AI Hub**.

This is **not** another chatbot.
This is an **AI Operating System**.

## Features (Planned)

| Phase | Feature | Description |
|-------|---------|-------------|
| 0 | **Foundation** | Authentication, Dashboard, Docker, Settings, Database |
| 1 | **AI Chat** | Chat with streaming, markdown, code highlighting, file uploads |
| 2 | **Coding Assistant** | Code generation, bug fixing, refactoring, Git integration |
| 3 | **Research Engine** | Web search, deep research, citation support |
| 4 | **AI Agents** | Browser control, task execution, automation |
| 5 | **Document Intelligence** | PDF chat, OCR, summaries, mind maps |
| 6 | **Memory** | Long-term memory, knowledge graph, conversation recall |
| 7 | **Voice AI** | Speech-to-text, text-to-speech, voice chat |
| 8 | **Image Studio** | Image generation, editing, upscaling |
| 9 | **Video Studio** | Video generation, subtitles, avatar videos |
| 10 | **Workflow Automation** | Visual workflow builder, integrations |
| 11 | **Plugin Marketplace** | Install plugins, MCP servers, community extensions |
| 12 | **Team Workspace** | Organizations, shared chats, permissions |
| 13 | **Marketplace** | Publish agents, prompts, templates, plugins |
| 14 | **Mobile Apps** | Android, iOS, Tablet |
| 15 | **Enterprise** | SSO, audit logs, RBAC, enterprise APIs |

## Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js** | React framework |
| **TypeScript** | Type-safe JavaScript |
| **Tailwind CSS** | Utility-first CSS |
| **Shadcn UI** | Component library |
| **Vercel AI SDK** | AI streaming & tool calls |

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | Python async web framework |
| **SQLAlchemy** | ORM with async support |
| **Alembic** | Database migrations |
| **Pydantic** | Data validation & settings |
| **ChromaDB** | Vector database |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **PostgreSQL** | Primary database |
| **Redis** | Caching & rate limiting |
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Ollama** | Local AI model serving |

### AI Models (Local First)
- **Qwen 3** — Reasoning & vision
- **DeepSeek** — Coding
- **Llama 3** — Writing & general
- **Mistral** — Fast responses
- **Gemma** — Lightweight tasks
- **Phi** — Edge deployment

Users can also connect their own API keys for cloud models (OpenAI, Claude, Gemini, OpenRouter).

## Project Structure

```
multimax-ai-hub/
├── .azure/                    # Architecture documentation
│   └── architecture/
│       ├── adr/               # Architecture Decision Records
│       ├── ARCHITECTURE_REVIEW.md
│       └── SOFTWARE_ARCHITECTURE_DOCUMENT.md
├── .devcontainer/             # VS Code Dev Container
│   ├── devcontainer.json
│   └── setup.sh
├── .github/
│   └── workflows/
│       ├── ci.yml             # Continuous Integration
│       └── deploy.yml         # Deployment
├── backend/
│   ├── app/
│   │   ├── core/              # Platform core (DI, config, events, DB)
│   │   ├── shared/            # Shared interfaces & base classes
│   │   ├── workspace/         # Workspace module (example domain)
│   │   └── main.py            # Application entry point
│   ├── tests/                 # Backend tests
│   ├── migrations/            # Alembic migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/                   # Next.js application
│   ├── public/                # Static assets
│   ├── package.json
│   └── .env.example
├── docker/
│   ├── docker-compose.yml     # Multi-service orchestration
│   ├── Dockerfile.backend     # Backend image
│   └── Dockerfile.frontend    # Frontend image
├── .editorconfig
├── .pre-commit-config.yaml
├── Makefile                   # Development commands
└── README.md
```

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker & Docker Compose** (optional, for full stack)
- **Ollama** (optional, for local AI models)

### Quick Start (Development)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/multimax-ai-hub.git
cd multimax-ai-hub

# 2. Install dependencies
make setup

# 3. Start the backend
make dev-backend

# 4. In another terminal, start the frontend
make dev-frontend
```

### Full Stack with Docker

```bash
# Start all services
make dev-docker

# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Environment Setup

Copy the example environment files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Then edit the files to configure your environment.

## Development

### Commands

| Command | Description |
|---------|-------------|
| `make setup` | Install all dependencies |
| `make dev-backend` | Start backend dev server |
| `make dev-frontend` | Start frontend dev server |
| `make dev-docker` | Start all Docker services |
| `make test` | Run all tests |
| `make test-backend` | Run backend tests |
| `make test-frontend` | Run frontend tests |
| `make lint` | Run all linters |
| `make format` | Format all code |
| `make clean` | Clean build artifacts |
| `make check` | Run lint + test + build |
| `make migrate` | Run database migrations |
| `make migrate-new msg="description"` | Create a new migration |
| `make docker-logs` | View Docker logs |
| `make docker-down` | Stop Docker services |

### Code Quality

- **Ruff** for Python linting and formatting
- **ESLint** + **Prettier** for frontend code
- **MyPy** for Python type checking
- **TypeScript** for type-safe frontend
- **Pre-commit hooks** for automated checks

## Architecture

### Core Principles

1. **Domain-Driven Modules** — Each feature is an independent domain module
2. **Event-Driven Communication** — Modules communicate via an event bus
3. **AI Provider Abstraction** — Models are interchangeable behind a common interface
4. **Zero Budget** — Free and open-source technologies only
5. **Self-Hostable** — Everything runs locally with Docker

### Architecture Decisions

All significant architectural decisions are documented as **Architecture Decision Records (ADRs)** in `.azure/architecture/adr/`.

| ADR | Title | Status |
|-----|-------|--------|
| 001 | [Use Architecture Decision Records](.azure/architecture/adr/ADR-001-record-architecture-decisions.md) | ✅ Accepted |
| 002 | [Domain-Driven Module Architecture](.azure/architecture/adr/ADR-002-domain-modules.md) | ✅ Accepted |
| 003 | [AI Provider Abstraction Layer](.azure/architecture/adr/ADR-003-ai-provider-abstraction.md) | ✅ Accepted |
| 004 | [Event-Driven Communication](.azure/architecture/adr/ADR-004-event-driven-communication.md) | ✅ Accepted |
| 005 | [Zero-Budget Open Source Stack](.azure/architecture/adr/ADR-005-zero-budget-stack.md) | ✅ Accepted |

For a detailed review of the architecture, see:
- [Architecture Review](.azure/architecture/ARCHITECTURE_REVIEW.md)
- [Software Architecture Document](.azure/architecture/SOFTWARE_ARCHITECTURE_DOCUMENT.md)

## Roadmap

See [Phase 0 Implementation Plan](PHASE0_IMPLEMENTATION_PLAN.md) for the detailed roadmap.

### Phase 0 — Foundation ✅
- [x] Project architecture & ADRs
- [x] Docker configuration
- [x] Core platform (DI, config, events, DB)
- [x] Workspace module (example domain)
- [x] CI/CD & developer tooling
- [ ] Authentication system
- [ ] Dashboard UI
- [ ] Settings & theme
- [ ] Logging & monitoring
- [ ] Deployment automation

### Phase 1 — AI Chat (In Development)
- Chat interface with streaming
- Markdown & code highlighting
- File & image uploads
- Chat history management
- Prompt library & personas

### Phases 2-15
See the [full project document](#) for the complete roadmap.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Multimax AI Hub builds upon the incredible work of the open-source community:

- [Open WebUI](https://github.com/open-webui/open-webui)
- [Crawl4AI](https://github.com/unclecode/crawl4ai)
- [Browser Use](https://github.com/gregpr07/browser-use)
- [Langflow](https://github.com/logspace-ai/langflow)
- [n8n](https://github.com/n8n-io/n8n)
- [Ollama](https://github.com/ollama/ollama)
- [Continue.dev](https://github.com/continuedev/continue)
- [LiteLLM](https://github.com/BerriAI/litellm)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [Supabase](https://github.com/supabase/supabase)
- [Shadcn UI](https://github.com/shadcn-ui/ui)
- [Vercel AI SDK](https://github.com/vercel/ai)

---

<div align="center">
  <sub>Built with ❤️ by the Multimax team. </sub>
</div>