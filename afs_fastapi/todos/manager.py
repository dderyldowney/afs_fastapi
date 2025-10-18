"""
This module is responsible for managing the ToDoWrite data.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.todos.db.config import DATABASE_URL
from afs_fastapi.todos.db.repository import NodeRepository

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


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def load_todos() -> dict[str, list[Node]]:
    """
    Loads all the ToDoWrite data from the database.

    Returns:
        A dictionary containing the loaded ToDoWrite data.
    """
    db = SessionLocal()
    repository = NodeRepository(db)
    todos: dict[str, list[Node]] = {}
    try:
        db_nodes = repository.list()
        for db_node in db_nodes:
            links = Link(
                parents=[parent.id for parent in db_node.parents],
                children=[child.id for child in db_node.children],
            )
            metadata = Metadata(
                owner=db_node.owner,
                labels=[label.label for label in db_node.labels],
                severity=db_node.severity,
                work_type=db_node.work_type,
            )
            command = None
            if db_node.command:
                command = Command(
                    ac_ref=db_node.command.ac_ref,
                    run=eval(db_node.command.run),
                    artifacts=[artifact.artifact for artifact in db_node.command.artifacts],
                )
            node = Node(
                id=db_node.id,
                layer=db_node.layer,
                title=db_node.title,
                description=db_node.description,
                links=links,
                metadata=metadata,
                status=db_node.status,
                command=command,
            )
            if node.layer not in todos:
                todos[node.layer] = []
            todos[node.layer].append(node)
    finally:
        db.close()
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


def create_node(node_data: dict[str, Any]) -> Node:
    db = SessionLocal()
    repository = NodeRepository(db)
    try:
        db_node = repository.create(node_data)
        return Node(
            id=db_node.id,
            layer=db_node.layer,
            title=db_node.title,
            description=db_node.description,
            links=Link(
                parents=[link.parent_id for link in db_node.parents],
                children=[link.child_id for link in db_node.children],
            ),
            metadata=Metadata(
                owner=db_node.owner,
                labels=[label.label for label in db_node.labels],
                severity=db_node.severity,
                work_type=db_node.work_type,
            ),
            status=db_node.status,
            command=(
                Command(
                    ac_ref=db_node.command.ac_ref,
                    run=eval(db_node.command.run),
                    artifacts=[artifact.artifact for artifact in db_node.command.artifacts],
                )
                if db_node.command
                else None
            ),
        )
    finally:
        db.close()


def update_node(node_id: str, node_data: dict[str, Any]) -> Node | None:
    db = SessionLocal()
    repository = NodeRepository(db)
    try:
        db_node = repository.update(node_id, node_data)
        if db_node:
            return Node(
                id=db_node.id,
                layer=db_node.layer,
                title=db_node.title,
                description=db_node.description,
                links=Link(
                    parents=[link.parent_id for link in db_node.parents],
                    children=[link.child_id for link in db_node.children],
                ),
                metadata=Metadata(
                    owner=db_node.owner,
                    labels=[label.label for label in db_node.labels],
                    severity=db_node.severity,
                    work_type=db_node.work_type,
                ),
                status=db_node.status,
                command=(
                    Command(
                        ac_ref=db_node.command.ac_ref,
                        run=eval(db_node.command.run),
                        artifacts=[artifact.artifact for artifact in db_node.command.artifacts],
                    )
                    if db_node.command
                    else None
                ),
            )
        return None
    finally:
        db.close()


def delete_node(node_id: str) -> None:
    db = SessionLocal()
    repository = NodeRepository(db)
    try:
        repository.delete(node_id)
    finally:
        db.close()
