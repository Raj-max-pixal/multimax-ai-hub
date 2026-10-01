# Production deployment: Vercel + Render + Supabase

This setup keeps the SPA on Vercel, runs the FastAPI application as a Render
Web Service, and uses Supabase PostgreSQL and Storage. No credentials belong in
this repository.

## Render

Create a Render Blueprint from the repository root using `render.yaml`. The
Blueprint configures the service root as `backend`, runs Alembic in the
pre-deploy step, and starts the application using Render's assigned `PORT`.
The `sync: false` values must be added to the Render service's secret
environment: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, and
`GEMINI_API_KEY` (the latter is only needed for Gemini inference). Use the
Supabase PostgreSQL connection string supported by the project's network and
connection limits. Do not put these values in a checked-in file.

The first migration creates the complete application schema, followed by the
profile-field migration. Before deploying migrations, confirm the Supabase
database is fresh or take a backup and baseline it if it already has application
tables/data. Do not mark the baseline as applied without comparing the live
schema to `backend/migrations/versions/3ff0865da455_initial_production_schema.py`.

The profile photo endpoint requires a Supabase Storage bucket named
`profile-avatars`. Create it in the Supabase Dashboard with public reads enabled
(avatars are displayed without a signed-in session) and a 5 MB file limit.
Uploads themselves go through the authenticated FastAPI endpoint and use the
service-role key only on Render; never expose that key to Vercel or the browser.
The endpoint accepts JPEG, PNG, and WebP, validates content signatures, and
stores objects under the authenticated user's ID.

## Vercel

Set `VITE_API_BASE_URL` to the deployed Render origin plus `/api`, for example
`https://<render-service>.onrender.com/api`, in the Vercel Production
environment. This value is public configuration, not a secret. Redeploy the
frontend after setting it. The current CORS allow-list is
`https://multimax-ai-hub.vercel.app`; update `API_CORS_ORIGINS` on Render if the
production Vercel domain changes.

## Go-live checks

After the Render service is deployed and the database migration succeeds,
verify `/health/ready`, registration/login, authenticated profile reads and
updates, duplicate usernames with differing case, and profile-image upload.
Then set the Render URL in Vercel and test login → profile edit → save → reload.
Production smoke tests require live provider credentials and a test account;
they must not be run against a database containing user data without an
approved test account and backup.
