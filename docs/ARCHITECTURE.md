# Architecture

- Monorepo with `apps/api` (FastAPI) and `web` (Next.js)
- PostgreSQL for persistence (docker-compose service)
- Backend organized with `app/core`, `app/api/v1`, `app/db`, `app/models`, `app/schemas`
