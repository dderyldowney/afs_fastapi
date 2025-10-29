"""API endpoints module for AFS FastAPI.

This module contains all FastAPI router endpoints for the agricultural
robotics platform including equipment management, fleet coordination,
safety systems, and monitoring capabilities.
"""

# Endpoints can be imported directly from afs_fastapi.api.endpoints
from . import equipment, fleet, safety, todos  # noqa: F401

__all__: list[str] = [
    "equipment",
    "fleet",
    "safety",
    "todos",
]
