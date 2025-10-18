"""
This module is responsible for managing the ToDoWrite data.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.todos.db.config import DATABASE_URL
from afs_fastapi.todos.db.models import Base
from afs_fastapi.todos.db.repository import NodeRepository

LayerType = Literal[
    "Goal",
    "Concept",
    "Context",
    "Constraints",
    "Requirements",
    "Acceptance Criteria",
    "Interface Contract",
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


@dataclass
class GoalItem:
    """Represents a Goal-layer item for agricultural robotics strategic planning."""

    id: str
    title: str
    description: str
    status: StatusType
    category: str = "general"
    priority: str = "medium"
    owner: str = ""
    labels: list[str] = field(default_factory=list)

    @classmethod
    def from_node(cls, node: Node) -> "GoalItem":
        """Create GoalItem from a Node."""
        return cls(
            id=node.id,
            title=node.title,
            description=node.description,
            status=node.status,
            category=node.metadata.labels[0] if node.metadata.labels else "general",
            priority=node.metadata.severity or "medium",
            owner=node.metadata.owner,
            labels=node.metadata.labels,
        )


@dataclass
class PhaseItem:
    """Represents a Phase-layer item for agricultural robotics project phases."""

    id: str
    title: str
    description: str
    status: StatusType
    owner: str = ""
    labels: list[str] = field(default_factory=list)

    @classmethod
    def from_node(cls, node: Node) -> "PhaseItem":
        """Create PhaseItem from a Node."""
        return cls(
            id=node.id,
            title=node.title,
            description=node.description,
            status=node.status,
            owner=node.metadata.owner,
            labels=node.metadata.labels,
        )


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database() -> None:
    """
    Initialize the database by creating all tables.

    This function creates all the tables defined in the models if they don't exist.
    Should be called before first use of the TodoWrite system.
    """
    Base.metadata.create_all(bind=engine)


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


def get_goals() -> list[dict[str, Any]]:
    """
    Get all Goal-layer items for strategic planning.

    Returns:
        A list of goal dictionaries compatible with strategic-status command.
    """
    todos = load_todos()
    goal_nodes = todos.get("Goal", [])

    goals = []
    for node in goal_nodes:
        goal_dict = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "status": node.status,
            "category": node.metadata.labels[0] if node.metadata.labels else "general",
            "priority": node.metadata.severity or "medium",
            "owner": node.metadata.owner,
            "labels": node.metadata.labels,
        }
        goals.append(goal_dict)

    return goals


def get_phases() -> list[PhaseItem]:
    """
    Get all Phase-layer items for project management.

    Returns:
        A list of PhaseItem objects.
    """
    todos = load_todos()
    phase_nodes = todos.get("Phase", [])

    return [PhaseItem.from_node(node) for node in phase_nodes]


def get_goals_typed() -> list[GoalItem]:
    """
    Get all Goal-layer items as typed GoalItem objects.

    Returns:
        A list of GoalItem objects.
    """
    todos = load_todos()
    goal_nodes = todos.get("Goal", [])

    return [GoalItem.from_node(node) for node in goal_nodes]