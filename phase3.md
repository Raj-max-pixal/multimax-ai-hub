# Phase 3 — Research Engine

Completed:

- Research page at `/research`.
- Web search mode.
- Deep search mode.
- Academic search intent.
- News search intent.
- Fact-check mode.
- Report mode.
- Source cards/citations.
- AI summary/report generation through Ollama.
- Copy result.
- Export report as Markdown.
- Local research history.
- Backend endpoint: `POST /api/research/search`.

Notes:

- Web search uses a local backend search flow and gracefully falls back when web search is unavailable.
