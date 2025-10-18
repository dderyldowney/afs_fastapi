"""
This module is responsible for managing the ToDoWrite data.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

PLANS_DIR = Path(__file__).parent / "plans"

LayerType = Literal[
    "Goal",
    "Concept",
    "Context",
    "Constraints",
    "Requirements",
    "AcceptanceCriteria",
    "InterfaceContract",
    "Phase",
    "Step",
    "Task",
    "SubTask",
    "Command",
]
"""The type of a ToDoWrite layer."""

StatusType = Literal["planned", "in_progress", "blocked", "done", "rejected"]
"""The status of a ToDoWrite node."""

@dataclass
class Link:
    """Represents the links between ToDoWrite nodes."""
    parents: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)

@dataclass
class Metadata:
    """Represents the metadata of a ToDoWrite node."""
    owner: str
    labels: list[str] = field(default_factory=list)
    severity: str = ""
    work_type: str = ""

@dataclass
class Command:
    """Represents a command to be executed."""
    ac_ref: str
    run: dict[str, Any]
    artifacts: list[str] = field(default_factory=list)

@dataclass
class Node:
    """Represents a node in the ToDoWrite system."""
    id: str
    layer: LayerType
    title: str
    description: str
    links: Link
    metadata: Metadata
    status: StatusType = "planned"
    command: Command | None = None

def load_todos() -> dict[str, list[Node]]:
    """
    Loads all the ToDoWrite data from the YAML files in the plans directory.

    Returns:
        A dictionary containing the loaded ToDoWrite data.
    """
    todos: dict[str, list[Node]] = {}
    for layer in os.listdir(PLANS_DIR):
        layer_dir = PLANS_DIR / layer
        if layer_dir.is_dir():
            todos[layer] = []
            for filename in os.listdir(layer_dir):
                if filename.endswith(".yaml"):
                    with open(layer_dir / filename) as f:
                        data = yaml.safe_load(f)
                        links_data = data.get("links", {})
                        metadata_data = data.get("metadata", {})
                        command_data = data.get("command")
                        node = Node(
                            id=data["id"],
                            layer=data["layer"],
                            title=data["title"],
                            description=data["description"],
                            links=Link(**links_data),
                            metadata=Metadata(**metadata_data),
                            status=data.get("status", "planned"),
                            command=Command(**command_data) if command_data else None,
                        )
                        todos[layer].append(node)
    return todos

def get_active_items(todos: dict[str, list[Node]]) -> dict[str, Node]:
    """
    Gets the active items from the ToDoWrite data.

    Args:
        todos: The ToDoWrite data.

    Returns:
        A dictionary containing the active items.
    """
    active_items: dict[str, Node] = {}
    for layer, nodes in todos.items():
        for node in nodes:
            if node.status == "in_progress":
                active_items[layer] = node
    return active_items