"""Mock todowrite library for testing purposes.

This module provides mock implementations of todowrite classes and functions
to enable the library to function without the external todowrite dependency.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class StoragePreference(Enum):
    """Mock StoragePreference enum."""
    AUTO = "auto"
    POSTGRESQL_ONLY = "postgresql_only"
    SQLITE_ONLY = "sqlite_only"
    YAML_ONLY = "yaml_only"


class StatusType(Enum):
    """Mock StatusType enum."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class LayerType(Enum):
    """Mock LayerType enum."""
    GOAL = "goal"
    CONCEPT = "concept"
    CONTEXT = "context"
    CONSTRAINTS = "constraints"
    REQUIREMENTS = "requirements"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    INTERFACE_CONTRACT = "interface_contract"
    PHASE = "phase"
    STEP = "step"
    TASK = "task"
    SUBTASK = "subtask"
    COMMAND = "command"


class Node:
    """Mock Node class for todowrite."""

    def __init__(self, name: str, layer_type: LayerType, status: StatusType = StatusType.PENDING):
        self.name = name
        self.layer_type = layer_type
        self.status = status
        self.description = ""
        self.active_form = ""
        self.metadata = {}
        self.labels = []
        self.links = {"parents": [], "children": []}

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary."""
        return {
            "name": self.name,
            "layer_type": self.layer_type.value,
            "status": self.status.value,
            "description": self.description,
            "active_form": self.active_form,
            "metadata": self.metadata,
            "labels": self.labels,
            "links": self.links
        }


class ToDoWrite:
    """Mock ToDoWrite class for todowrite."""

    def __init__(self, db_url: str | None = None, auto_import: bool = True,
                 storage_preference: StoragePreference = StoragePreference.AUTO):
        self.db_url = db_url
        self.auto_import = auto_import
        self.storage_preference = storage_preference
        self.nodes: dict[str, Node] = {}

    def create_node(self, name: str, layer_type: LayerType, **kwargs) -> Node:
        """Create a new node."""
        node = Node(name, layer_type)
        for key, value in kwargs.items():
            setattr(node, key, value)
        self.nodes[name] = node
        return node

    def get_node(self, name: str) -> Node | None:
        """Get a node by name."""
        return self.nodes.get(name)

    def list_nodes(self) -> list[Node]:
        """List all nodes."""
        return list(self.nodes.values())

    def update_node_status(self, name: str, status: StatusType) -> bool:
        """Update node status."""
        if name in self.nodes:
            self.nodes[name].status = status
            return True
        return False