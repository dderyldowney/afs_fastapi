"""Core functionality module for AFS FastAPI.

This module contains core utilities, parsers, and configuration management
for the agricultural robotics platform including CAN bus communication,
J1939 protocol handling, and TodoWrite integration.
"""

# Core modules can be imported directly from afs_fastapi.core
from .todowrite_config import create_todowrite_app, get_global_todowrite_app, get_todowrite_status

__all__: list[str] = [
    "create_todowrite_app",
    "get_global_todowrite_app",
    "get_todowrite_status",
]
