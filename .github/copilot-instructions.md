# AFS-FastAPI Copilot instructions

This repository exposes simple equipment and monitoring APIs using FastAPI. The document below gives concise, repository-specific guidance for AI coding agents: entrypoint, key files, conventions, quick commands, and small examples.

## Entrypoint

Run the package as a module:

    python -m afs_fastapi

Uvicorn serves the application from `afs_fastapi.api.main:app` when run via the package entrypoint.

## Configuration

Environment variables:

- AFS_API_HOST
- AFS_API_PORT
- AFS_API_RELOAD
- AFS_API_LOG_LEVEL
- Optional: AFS_CORS_ORIGINS

## Key files

- `afs_fastapi/api/main.py` — API handlers and app setup
- `afs_fastapi/__main__.py` — CLI entry that reads env vars and starts the server
- `afs_fastapi/equipment/farm_tractors.py` — domain model `FarmTractor` (use `to_response()` to convert to API model)
- `afs_fastapi/monitoring/` — monitoring interfaces, monitors, and schemas

## Conventions

- Keep domain objects separate from Pydantic response models; use `to_response()` where available.
- Monitoring backends implement `read(sensor_id: str) -> Dict[str, float]` and are injected into monitors. Feature and unit tests use dummy backends by default.
- Preserve public response shapes; if you change them, update tests under `tests/unit/`.

## Quick commands

Create a virtualenv, install deps, and run tests and type checks:

    python -m venv .venv

    source .venv/bin/activate
    pip install -r requirements.txt
    pytest tests/
    pyright afs_fastapi/ tests/
    black --check afs_fastapi/ tests/
    flake8 afs_fastapi/ tests/
    isort --check-only afs_fastapi/ tests/
