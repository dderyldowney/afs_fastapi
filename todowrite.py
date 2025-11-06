"""Mock todowrite package initialization.

This file serves as a mock todowrite package to enable the AFS FastAPI
library to function without the external todowrite dependency.
"""

from __future__ import annotations

from afs_fastapi.core.todowrite_mock import (
    LayerType,
    Node,
    StatusType,
    StoragePreference,
    ToDoWrite,
)

# Export both Node and ToDoWriteNode for compatibility
ToDoWriteNode = Node

__all__ = [
    "LayerType",
    "Node",
    "ToDoWriteNode",
    "StatusType",
    "StoragePreference",
    "ToDoWrite",
]