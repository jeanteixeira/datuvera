# Technical debt

Known items; recording them does not imply they are part of Project Polish.

- Pydantic v2: `.dict()` and class-based Settings config produce deprecation warnings.
- `DatasetProfile.schema` shadows `BaseModel.schema` and emits a warning.
- Profiling uses deprecated `datetime.utcnow()` and returns a naive generated timestamp.
- Starlette/httpx and AnyIO test-client integration emit deprecation warnings.
- API startup tolerates Alembic migration failure (`alembic upgrade head || true`); health does not validate database schema readiness.
- Profiling performs multiple queries per column and full-table scans; scalability/query count needs assessment.
- Demo timestamps use `now()` and depend on initialization/reset time; quality issues and counts remain deterministic.
- npm reported one high-severity vulnerability during web build. Identify the affected dependency and remediation separately; no forced upgrade was applied.
- Dependencies are duplicated/diverge between root `pyproject.toml` and API `requirements.txt`; Docker uses the latter.
- Web build installs missing TypeScript type dependencies and generates `tsconfig.json` inside the image; this weakens build reproducibility.
- Backend integration tests use the local metadata database and leave source registrations/test objects; isolate their database lifecycle later.
- Web `npm run lint` still invokes `next lint`, which is unavailable in the installed Next.js 16; configure a standalone linter in a later tooling task. Stage 08 validates TypeScript through `next build`.
