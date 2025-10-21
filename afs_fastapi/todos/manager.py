"""
This module is responsible for managing the ToDoWrite data.
"""

from dataclasses import dataclass, field
from typing import Any, Literal, cast

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.todos.db.config import AGRICULTURAL_DB_SETTINGS, DATABASE_URL, is_postgresql
from afs_fastapi.todos.db.models import Base, Node as SQLAModelNode
from afs_fastapi.todos.db.repository import NodeRepository

# ...

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


def _validate_literal(value: str, literal_type: Any) -> str:

    if value not in literal_type.__args__:

        raise ValueError(f"Invalid literal value: {value}. Expected one of {literal_type.__args__}")

    return value


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


# Configure database engine based on database type
def create_database_engine():
    """Create SQLAlchemy engine with appropriate settings for database type."""
    if is_postgresql():
        settings = AGRICULTURAL_DB_SETTINGS["postgresql"]
        return create_engine(DATABASE_URL, **settings)
    else:  # SQLite default
        settings = AGRICULTURAL_DB_SETTINGS["sqlite"]
        return create_engine(DATABASE_URL, **settings)


engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database() -> dict[str, str]:
    """
    Initialize the database by creating all tables.

    This function creates all the tables defined in the models if they don't exist.
    Should be called before first use of the TodoWrite system.

    Supports both SQLite and PostgreSQL for agricultural robotics environments.
    """
    try:
        Base.metadata.create_all(bind=engine)

        # Log database type for agricultural operations tracking
        if is_postgresql():
            db_type = "PostgreSQL (Production Agricultural Database)"
        else:
            db_type = "SQLite (Development/Local Agricultural Database)"

        return {"status": "success", "database_type": db_type, "url": DATABASE_URL}
    except Exception as e:
        return {"status": "error", "error": str(e), "database_url": DATABASE_URL}


def get_database_info() -> dict[str, Any]:
    """
    Get information about the current database configuration.

    Returns:
        Dictionary with database type, URL, and connection status
    """
    info = {
        "database_type": "PostgreSQL" if is_postgresql() else "SQLite",
        "database_url": DATABASE_URL,
        "is_production": is_postgresql(),
        "supports_concurrent_access": is_postgresql(),
        "agricultural_optimized": True,
    }

    try:
        # Test connection
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            info["connection_status"] = "connected"
            info["test_query"] = "success"
    except Exception as e:
        info["connection_status"] = "error"
        info["error"] = str(e)

    return info


def _convert_db_node_to_node(db_node: SQLAModelNode) -> Node:
    parent_ids: list[str] = (
        [str(cast(SQLAModelNode, parent).id) for parent in db_node.parents if parent.id is not None]
        if db_node.parents is not None
        else []
    )
    child_ids: list[str] = (
        [str(cast(SQLAModelNode, child).id) for child in db_node.children if child.id is not None]
        if db_node.children is not None
        else []
    )
    links = Link(parents=parent_ids, children=child_ids)

    metadata = Metadata(
        owner=db_node.owner or "",
        labels=(
            [str(label.label) for label in db_node.labels if label.label is not None]
            if db_node.labels
            else []
        ),
        severity=db_node.severity or "",
        work_type=db_node.work_type or "",
    )
    command = None
    if db_node.command:
        command = Command(
            ac_ref=db_node.command.ac_ref or "",
            run=eval(db_node.command.run) if db_node.command.run else {},
            artifacts=(
                [
                    str(artifact.artifact)
                    for artifact in db_node.command.artifacts
                    if artifact.artifact is not None
                ]
                if db_node.command.artifacts
                else []
            ),
        )
    return Node(
        id=str(db_node.id),
        layer=cast(LayerType, _validate_literal(str(db_node.layer), LayerType)),
        title=str(db_node.title),
        description=str(db_node.description),
        links=links,
        metadata=metadata,
        status=cast(StatusType, _validate_literal(str(db_node.status), StatusType)),
        command=command,
    )


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
        db_nodes = repository.list(SQLAModelNode)
        for db_node_item in db_nodes:
            db_node = cast(SQLAModelNode, db_node_item)
            node = _convert_db_node_to_node(db_node)
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


def get_active_phase() -> dict[str, Any] | None:
    """
    Gets the active phase from the ToDoWrite data.

    Returns:
        A dictionary containing the active phase, or None if no phase is active.
    """
    todos = load_todos()
    active_items = get_active_items(todos)
    if "Phase" in active_items:
        phase_node = active_items["Phase"]
        return {
            "id": phase_node.id,
            "title": phase_node.title,
            "description": phase_node.description,
            "status": phase_node.status,
            "tasks": [],  # Placeholder for tasks
        }
    return None


def create_node(node_data: dict[str, Any]) -> Node:
    db = SessionLocal()
    repository = NodeRepository(db)
    try:
        db_node = cast(SQLAModelNode, repository.create(node_data))
        return _convert_db_node_to_node(db_node)
    finally:
        db.close()


def update_node(node_id: str, node_data: dict[str, Any]) -> tuple[Node | None, str | None]:
    db = SessionLocal()
    repository = NodeRepository(db)
    try:
        db_node = cast(SQLAModelNode, repository.update_node_by_id(node_id, node_data))
        if db_node:
            return _convert_db_node_to_node(db_node), None
        return None, "Node not found or failed to update"
    except Exception as e:
        return None, str(e)
    finally:
        db.close()


def delete_node(node_id: str) -> None:
    db = SessionLocal()
    repository = NodeRepository(db)
    try:
        repository.delete_node_by_id(node_id)
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


def add_goal(title: str, description: str) -> tuple[dict[str, Any] | None, str | None]:
    """
    Add a new Goal.
    """
    try:
        import uuid

        goal_id = f"goal-{uuid.uuid4().hex[:12]}"
        goal_data = {
            "id": goal_id,
            "layer": "Goal",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(goal_data)
        if node:
            goal_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return goal_dict, None
        else:
            return None, "Failed to create goal"
    except Exception as e:
        return None, str(e)


def add_phase(
    goal_id: str, title: str, description: str
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Add a new Phase to the specified Goal.
    """
    try:
        import uuid

        phase_id = f"phase-{uuid.uuid4().hex[:12]}"
        phase_data = {
            "id": phase_id,
            "layer": "Phase",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [goal_id], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(phase_data)
        if node:
            phase_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return phase_dict, None
        else:
            return None, "Failed to create phase"
    except Exception as e:
        return None, str(e)


def add_subtask(
    task_id: str,
    title: str,
    description: str,
    command: str | None = None,
    command_type: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Add a new SubTask to the specified Task.
    """
    try:
        import dataclasses
        import uuid

        subtask_id = f"subtask-{uuid.uuid4().hex[:12]}"
        subtask_data = {
            "id": subtask_id,
            "layer": "SubTask",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [task_id], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }
        if command:
            subtask_data["command"] = {
                "ac_ref": "",
                "run": {"command": command, "type": command_type or "bash"},
                "artifacts": [],
            }

        node = create_node(subtask_data)
        if node:
            subtask_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
                "command": dataclasses.asdict(node.command) if node.command else None,
            }
            return subtask_dict, None
        else:
            return None, "Failed to create subtask"
    except Exception as e:
        return None, str(e)


def add_step(
    phase_id: str, name: str, description: str
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Add a new Step to the specified Phase.

    Args:
        phase_id: The ID of the parent Phase.
        name: The name of the Step.
        description: The description of the Step.

    Returns:
        A tuple of (new_step_dict, error_message).
    """
    try:
        import uuid

        step_id = f"step-{uuid.uuid4().hex[:12]}"
        step_data = {
            "id": step_id,
            "layer": "Step",
            "title": name,
            "description": description,
            "status": "planned",
            "links": {"parents": [phase_id], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(step_data)
        if node:
            step_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return step_dict, None
        else:
            return None, "Failed to create step"
    except Exception as e:
        return None, str(e)


def add_task(
    step_id: str, title: str, description: str
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Add a new Task to the specified Step.

    Args:
        step_id: The ID of the parent Step.
        title: The title of the Task.
        description: The description of the Task.

    Returns:
        A tuple of (new_task_dict, error_message).
    """
    try:
        import uuid

        task_id = f"task-{uuid.uuid4().hex[:12]}"
        task_data = {
            "id": task_id,
            "layer": "Task",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [step_id], "children": []},
            "metadata": {
                "owner": "system",
                "severity": "",
                "work_type": "",
                "labels": [],
            },
        }

        node = create_node(task_data)
        if node:
            task_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return task_dict, None
        else:
            return None, "Failed to create task"
    except Exception as e:
        return None, str(e)


def complete_goal(goal_id: str) -> tuple[Node | None, str | None]:
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        # First, load the goal to get its current state
        todos = load_todos()
        goals = todos.get("Goal", [])
        goal = None
        for g in goals:
            if g.id == goal_id:
                goal = g
                break

        if not goal:
            return None, f"Goal with ID '{goal_id}' not found"

        if goal.status == "done":
            return goal, None  # Already completed

        # Update the goal status to 'done' and add completion timestamp
        updated_goal = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                goal_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": goal.metadata.owner,
                        "labels": goal.metadata.labels,
                        "severity": goal.metadata.severity,
                        "work_type": goal.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_goal:
            return None, "Failed to update goal status in database"

        node = _convert_db_node_to_node(updated_goal)
        return node, None
    finally:
        db.close()


def complete_phase(phase_id: str) -> tuple[Node | None, str | None]:
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        # First, load the phase to get its current state
        todos = load_todos()
        phases = todos.get("Phase", [])
        phase = None
        for p in phases:
            if p.id == phase_id:
                phase = p
                break

        if not phase:
            return None, f"Phase with ID '{phase_id}' not found"

        if phase.status == "done":
            return phase, None  # Already completed

        # Update the phase status to 'done' and add completion timestamp
        updated_phase = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                phase_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": phase.metadata.owner,
                        "labels": phase.metadata.labels,
                        "severity": phase.metadata.severity,
                        "work_type": phase.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_phase:
            return None, "Failed to update phase status in database"

        node = _convert_db_node_to_node(updated_phase)
        return node, None
    finally:
        db.close()
