# Contributing to Datuvera

1. Fork/clone the repository and create a focused branch, such as `fix/demo-connection`.
2. Copy `.env.example` to `.env` and run `make up` (Git, Docker Compose v2 and Make required). Existing installations should first follow the README volume-preservation instructions.
3. Make a small change and preserve the existing API and architecture unless the change explicitly requires otherwise.
4. Run `make test`; for Python changes, first run `python3 -m compileall -q apps/api/app` or its container equivalent. Run `make build` for web/container changes and manually check the affected UI flow.
5. Open a PR describing the problem, resulting behavior and validation. Include a screenshot for visible UI changes when useful.

Use four spaces in Python, explicit Pydantic models, safely quoted SQL identifiers and parameterized SQL values. Do not return/log source passwords, commit `.env` or add real secrets. Add meaningful tests for behavior changes. Keep deterministic profiling/quality independent of LLMs.

Report bugs with reproduction steps and expected/actual results. Discuss larger changes in an issue before implementation. Known limitations are tracked in `docs/technical-debt.md`; no dependency upgrades are required for unrelated contributions.
