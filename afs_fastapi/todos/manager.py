
"""
This module is responsible for managing the ToDoWrite data.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from afs_fastapi.todos.database import create_connection

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
    Loads all the ToDoWrite data from the database.

    Returns:
        A dictionary containing the loaded ToDoWrite data.
    """
    conn = create_connection()
    todos: dict[str, list[Node]] = {}
    if conn is not None:
        c = conn.cursor()
        c.execute("SELECT * FROM nodes")
        nodes_data = c.fetchall()
        for node_data in nodes_data:
            node_id = node_data[0]

            # Get links
            c.execute("SELECT parent_id FROM links WHERE child_id = ?", (node_id,))
            parents = [row[0] for row in c.fetchall()]
            c.execute("SELECT child_id FROM links WHERE parent_id = ?", (node_id,))
            children = [row[0] for row in c.fetchall()]
            links = Link(parents=parents, children=children)

            # Get labels
            c.execute("SELECT label FROM labels WHERE node_id = ?", (node_id,))
            labels = [row[0] for row in c.fetchall()]

            # Get command
            c.execute("SELECT ac_ref, run FROM commands WHERE node_id = ?", (node_id,))
            command_data = c.fetchone()
            command = None
            if command_data:
                c.execute("SELECT artifact FROM artifacts WHERE command_id = ?", (node_id,))
                artifacts = [row[0] for row in c.fetchall()]
                command = Command(ac_ref=command_data[0], run=eval(command_data[1]), artifacts=artifacts)

            node = Node(
                id=node_id,
                layer=node_data[1],
                title=node_data[2],
                description=node_data[3],
                links=links,
                metadata=Metadata(owner=node_data[5], labels=labels, severity=node_data[6], work_type=node_data[7]),
                status=node_data[4],
                command=command,
            )
            if node.layer not in todos:
                todos[node.layer] = []
            todos[node.layer].append(node)
        conn.close()
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
