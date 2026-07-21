# Phase 11 — MCP & Plugin Marketplace

Completed:

- Plugin/MCP page at `/plugins`.
- Plugin catalog UI.
- Install plugin flow.
- Installed plugin list.
- MCP/integration/agent/workflow/tool categories.
- Backend endpoints:
  - `GET /api/plugins/catalog`
  - `POST /api/plugins/install`

Notes:

- Current mode stores installs in local backend memory. Future upgrade: real plugin package installation, versioning, permissions, and updates.
