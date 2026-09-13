# Datuvera

Know your data. Trust your data.

Open-source data profiling and quality platform for modern data stacks, enhanced with AI.

## Quick Start

1. Copy env example:

```bash
cp .env.example .env
```

2. Start with Docker Compose:

```bash
docker compose up --build
```

## Project Structure

- apps/api: FastAPI backend
- web: Next.js frontend
- docker: container helpers
- docs: documentation
- examples: example integrations

## Endpoints

- `GET /health` - service health
- `GET /api/v1/info` - basic service info

## Makefile

- `make up` - start services
- `make down` - stop services
- `make build` - build images
- `make logs` - follow logs
- `make test` - run tests

## Roadmap (initial)

- Project skeleton
- Core API and frontend
- Add connectors and profiling engine

MIT License
