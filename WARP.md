# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project: AFS FastAPI (Automated Farming System API)

What this file provides
- The essential commands you’ll actually run here (build, lint, type-check, tests, single-test invocation, API run). 
- A big-picture architecture map so future Warp runs don’t need to rediscover it by reading dozens of files.
- The key project rules relevant to agents (from README, CLAUDE.md, Copilot instructions, CI).

Common commands you’ll use

Environment and install (Python 3.12)
- Create venv and install dev extras (recommended):
  - python -m venv .venv
  - source .venv/bin/activate
  - python -m pip install -e .[dev]
- Alternative (fully pinned dev stack):
  - python -m pip install -r requirements.txt

Build and packaging
- python -m pip install build
- python -m build
- The package is afs_fastapi; console script afs-api is provided (see pyproject.toml and setup.py).

Run the API locally
- Quick start (defaults to 127.0.0.1:8000):
  - python -m afs_fastapi
  - or (after install) afs-api
- Development reload:
  - AFS_API_RELOAD=1 python -m afs_fastapi
- Environment variables supported (see afs_fastapi/__main__.py):
  - AFS_API_HOST (default 127.0.0.1)
  - AFS_API_PORT (default 8000)
  - AFS_API_RELOAD (true/false; default false)
  - AFS_API_LOG_LEVEL (debug|info|warning|error; default info)
  - Optional: AFS_CORS_ORIGINS (comma-separated) for CORS
- Make target: make run (sets AFS_API_RELOAD=1 and runs python -m afs_fastapi)

Tests
- Run all tests (pytest.ini sets defaults and testpaths=tests):
  - pytest -q
  - or python -m pytest tests/ -v --tb=short
- Run a directory:
  - python -m pytest tests/equipment -v
- Run a single file:
  - python -m pytest tests/api/test_main.py -v
- Run a single test:
  - python -m pytest tests/api/test_main.py::test_read_root -q
- Filter by keyword:
  - python -m pytest -k "vector_clock" -q

Lint, format, and types
- Lint: ruff check .
- Format (check): black --check . && isort --check-only .
- Format (apply): black . && isort .
- Type-check: pyright .
- Make targets: make lint, make format, make type, make test, make check

Pre-commit hooks (local enforcement)
- Install hooks: make precommit-install
- Run hooks on all files: make precommit-run
- These hooks enforce:
  - Code quality: Ruff, Black (check), isort (check-only), Pyright
  - Mandatory TDD and safety validators from .claude/hooks/ (see CLAUDE.md and AGENTS.md)

CI expectations (what must pass)
- GitHub Actions run on Python 3.12 and execute:
  - ruff check ., black --check ., isort --check-only ., pyright ., pytest -q
  - TDD enforcement and Safety validation scripts (.claude/hooks/*)

Big-picture architecture

Entrypoint and application
- Package entrypoint: afs_fastapi/__main__.py
  - Reads AFS_API_* env vars and runs Uvicorn against "afs_fastapi.api.main:app".
- FastAPI app: afs_fastapi/api/main.py
  - Meta endpoints: /, /health, /version
  - Domain endpoints:
    - Equipment: /equipment/tractor/{tractor_id}
    - Monitoring: /monitoring/soil/{sensor_id}, /monitoring/water/{sensor_id}
  - AI pipeline endpoints: /ai/* (optimize equipment/monitoring/fleet; statistics/health)
  - CRDT endpoints: /crdt/* for field segment allocation (see FieldAllocationCRDT)
  - Optional CORS via AFS_CORS_ORIGINS

Domain model and services (the core of “how it works”)
- Equipment domain (afs_fastapi/equipment/*)
  - FarmTractor is the central equipment model with a to_response() that produces the API-facing Pydantic model FarmTractorResponse.
  - ISOBUS and safety primitives mirror ISO 11783 and ISO 18497 concerns.
- Monitoring (afs_fastapi/monitoring/*)
  - SoilMonitor and WaterMonitor expose read/get_* methods; pluggable backends via interfaces.
  - Response schemas live under afs_fastapi/monitoring/schemas.py.
- Services and synchronization (afs_fastapi/services/*)
  - ai_processing_manager and related pipeline modules implement optimization/processing for messages.
  - Synchronization and distributed coordination primitives (e.g., vector clock, CRDT manager) back multi-tractor operations and field allocation. API handlers in api/main.py call into these.
- Models
  - Some API models (e.g., FieldSegment) are defined under the repository-level models/ directory (import resolved via pytest.ini pythonpath=.). API handlers consume these directly.

Testing layout and patterns
- Pytest configuration resides in pytest.ini (strict markers, modern import mode, asyncio fixture scope).
- Tests are under tests/ with integration, functional, features, library, api, equipment, monitoring, protocols, safety, services, and cli groupings. FastAPI endpoints are covered in tests/api/test_main.py (via TestClient).
- The repository emphasizes Test-First Development; pre-commit hooks and CI enforce TDD and safety checks.

Rules and references for agents (important excerpts)
- From README.md
  - Project targets: multi-tractor coordination, ISOBUS compliance, and strict TDD with zero technical debt.
  - Running the API: python -m afs_fastapi; environment overrides listed above.
- From CLAUDE.md and AGENTS.md
  - Universal agent requirements are defined in AGENTS.md. Mandatory TDD: write failing tests first (RED), implement minimal passing code (GREEN), then refactor. These are enforced by local hooks and CI.
  - “Format-first” generation: code and docs should be produced already compliant with formatter/linter/type-checker expectations.
  - Commit hygiene: Conventional commits and separation of concerns are expected; safety validation is part of the gate.
- From .github/copilot-instructions.md
  - Entrypoint (python -m afs_fastapi) and key files: afs_fastapi/api/main.py, afs_fastapi/__main__.py, afs_fastapi/equipment/farm_tractors.py, afs_fastapi/monitoring/.
  - Environment variables: AFS_API_HOST, AFS_API_PORT, AFS_API_RELOAD, AFS_API_LOG_LEVEL, optional AFS_CORS_ORIGINS.

Pointers
- README.md: project overview, capabilities, installation, run instructions, and security notes.
- WORKFLOW.md and TDD_WORKFLOW.md: authoritative testing and TDD methodology references.
- AGENTS.md and CLAUDE.md: mandatory agent rules, TDD/safety enforcement details, and session guidance.
- .pre-commit-config.yaml: the local enforcement configuration you’ll trigger via make precommit-run.
