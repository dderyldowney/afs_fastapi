"""Data models module for AFS FastAPI.

This module contains Pydantic models and data structures for agricultural
sensor data, equipment specifications, and system configurations.
"""

# Models can be imported directly from afs_fastapi.models
from .field_segment import FieldSegment

__all__: list[str] = [
    "FieldSegment",
]
