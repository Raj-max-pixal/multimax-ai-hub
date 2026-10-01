# Vercel deployment

Vercel hosts the React/Vite frontend. The FastAPI service remains a long-running
backend container because it uses streaming responses, PostgreSQL migrations,
uploads, and future background workers.

**Production frontend:** https://multimax-ai-hub.vercel.app

The frontend deployment is live. AI, authentication, files, and other dynamic
features require the backend URL described below before they work in production.

## Required Vercel variable

Set this for Preview and Production:

```text
VITE_API_BASE_URL=https://your-backend.example.com/api
```

Never add `GEMINI_API_KEY`, database credentials, or backend secrets to a
`VITE_*` variable. Vite variables are embedded in browser JavaScript.

## Deploy

From the repository root:

```bash
npx vercel --cwd frontend
npx vercel --cwd frontend --prod
```

The SPA rewrite in `frontend/vercel.json` keeps client-side routes such as
`/chat`, `/agents`, and `/settings` working on refresh.
