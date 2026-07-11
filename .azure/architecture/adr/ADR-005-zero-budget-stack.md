# ADR-005: Zero-Budget Open Source Stack

## Status

Accepted

## Context

Multimax AI Hub must be developed with zero budget — no paid APIs, no expensive cloud
services, no enterprise software. Everything must be self-hostable using free and
open-source technologies. This applies to the development process and the final product.

## Decision

We commit to a **Zero-Budget Open Source Stack**:

### Database
- **PostgreSQL** via Docker (local) or Supabase free tier (hosted)
- **ChromaDB** for vector storage (self-hosted via Docker)

### AI Models
- **Ollama** for local inference (Qwen, DeepSeek, Llama, Mistral, etc.)
- **Whisper** for speech-to-text (local)
- Users can bring their own API keys for cloud models (OpenAI, Anthropic, etc.)

### Infrastructure
- **Docker + Docker Compose** for local deployment
- **Vercel free tier** for frontend hosting (if needed)
- **Cloudflare** for DNS and CDN (free tier)
- **GitHub Actions** for CI/CD (free for public repos)

### Development
- **VS Code** with Dev Containers
- **Postman/Insomnia** for API testing (or HTTPie)
- **GitHub** for source control and project management

### Prohibited
- Paid API services (unless absolutely necessary and user-provided keys)
- Paid cloud services (Supabase free tier is acceptable)
- Proprietary software dependencies
- Vendor lock-in

## Consequences

- Positive: Zero cost barrier for development and deployment
- Positive: Full control over infrastructure
- Positive: Community-friendly — anyone can self-host
- Positive: No risk of unexpected API billing
- Negative: Requires more in-house expertise for DevOps
- Negative: Self-hosted components require maintenance
- Negative: Some features may need paid services in production at scale
- Neutral: Migration path to paid services exists if needed later