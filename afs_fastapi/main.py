"""
FastAPI application module.

- Provides `app` for ASGI servers (uvicorn, hypercorn, fastapi CLI).
- Keep *only* FastAPI app construction and include_routers here.
"""

from fastapi import FastAPI

app = FastAPI(title="AFS FastAPI", version="0.1.6")


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok"}
