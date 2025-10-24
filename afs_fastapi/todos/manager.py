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


def reset_database_engine() -> None:
    """
    Reset the database engine and session factory.

    This function should be called in test fixtures to ensure proper isolation.
    It disposes of all existing connections and creates a fresh engine and session factory.

    Agricultural Context: Ensures test isolation for agricultural robotics platform
    where database state must be clean between independent operation scenarios.
    """
    global engine, SessionLocal

    # Dispose of existing connections
    engine.dispose()

    # Create fresh engine and session factory
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database() -> dict[str, str]:
    """
    Initialize the database by clearing all data and recreating tables.

    This function drops all existing tables and recreates them, ensuring a clean state.
    Should be called before first use of the TodoWrite system and in test fixtures
    to ensure complete database isolation.

    Supports both SQLite and PostgreSQL for agricultural robotics environments.

    Agricultural Context: Essential for test isolation in agricultural robotics
    scenarios where clean state between different operation tests is critical.
    """
    try:
        # Drop all existing tables to clear data
        Base.metadata.drop_all(bind=engine)

        # Create all tables fresh
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
        owner=str(db_node.owner or ""),
        labels=(
            [str(label.label) for label in db_node.labels if label.label is not None]
            if db_node.labels
            else []
        ),
        severity=str(db_node.severity or ""),
        work_type=str(db_node.work_type or ""),
    )
    command = None
    if db_node.command:
        command = Command(
            ac_ref=str(db_node.command.ac_ref or ""),
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


def get_node_by_id(node_id: str) -> Node | None:
    """
    Get a node from the database by its ID.

    Args:
        node_id: The ID of the node to retrieve

    Returns:
        The Node object if found, None otherwise
    """
    db = SessionLocal()
    repository = NodeRepository(db)
    try:
        db_node = repository.get(SQLAModelNode, node_id)
        if db_node:
            return _convert_db_node_to_node(db_node)
    finally:
        db.close()
    return None


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


# Layer 2: Concept functions
def add_concept(
    title: str, description: str, goal_id: str | None = None
) -> tuple[dict[str, Any] | None, str | None]:
    """Add a new Concept to the ToDoWrite system."""
    try:
        import uuid

        concept_id = f"concept-{uuid.uuid4().hex[:12]}"
        concept_data = {
            "id": concept_id,
            "layer": "Concept",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [goal_id] if goal_id else [], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(concept_data)
        if node:
            concept_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return concept_dict, None
        else:
            return None, "Failed to create concept"
    except Exception as e:
        return None, str(e)


def get_concepts() -> list[dict[str, Any]]:
    """Get all Concept-layer items."""
    todos = load_todos()
    concept_nodes = todos.get("Concept", [])

    concepts = []
    for node in concept_nodes:
        concept_dict = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "status": node.status,
            "owner": node.metadata.owner,
            "labels": node.metadata.labels,
        }
        concepts.append(concept_dict)

    return concepts


def complete_concept(concept_id: str) -> tuple[Node | None, str | None]:
    """Mark a Concept as complete."""
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        todos = load_todos()
        concepts = todos.get("Concept", [])
        concept = None
        for c in concepts:
            if c.id == concept_id:
                concept = c
                break

        if not concept:
            return None, f"Concept with ID '{concept_id}' not found"

        if concept.status == "done":
            return concept, None  # Already completed

        updated_concept = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                concept_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": concept.metadata.owner,
                        "labels": concept.metadata.labels,
                        "severity": concept.metadata.severity,
                        "work_type": concept.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_concept:
            return None, "Failed to update concept status in database"

        node = _convert_db_node_to_node(updated_concept)
        return node, None
    finally:
        db.close()


# Layer 3: Context functions
def add_context(
    title: str, description: str, concept_id: str | None = None
) -> tuple[dict[str, Any] | None, str | None]:
    """Add a new Context to the ToDoWrite system."""
    try:
        import uuid

        context_id = f"context-{uuid.uuid4().hex[:12]}"
        context_data = {
            "id": context_id,
            "layer": "Context",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [concept_id] if concept_id else [], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(context_data)
        if node:
            context_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return context_dict, None
        else:
            return None, "Failed to create context"
    except Exception as e:
        return None, str(e)


def get_contexts() -> list[dict[str, Any]]:
    """Get all Context-layer items."""
    todos = load_todos()
    context_nodes = todos.get("Context", [])

    contexts = []
    for node in context_nodes:
        context_dict = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "status": node.status,
            "owner": node.metadata.owner,
            "labels": node.metadata.labels,
        }
        contexts.append(context_dict)

    return contexts


def complete_context(context_id: str) -> tuple[Node | None, str | None]:
    """Mark a Context as complete."""
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        todos = load_todos()
        contexts = todos.get("Context", [])
        context = None
        for c in contexts:
            if c.id == context_id:
                context = c
                break

        if not context:
            return None, f"Context with ID '{context_id}' not found"

        if context.status == "done":
            return context, None  # Already completed

        updated_context = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                context_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": context.metadata.owner,
                        "labels": context.metadata.labels,
                        "severity": context.metadata.severity,
                        "work_type": context.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_context:
            return None, "Failed to update context status in database"

        node = _convert_db_node_to_node(updated_context)
        return node, None
    finally:
        db.close()


# Layer 4: Constraints functions
def add_constraint(
    title: str, description: str, context_id: str | None = None
) -> tuple[dict[str, Any] | None, str | None]:
    """Add a new Constraint to the ToDoWrite system."""
    try:
        import uuid

        constraint_id = f"constraint-{uuid.uuid4().hex[:12]}"
        constraint_data = {
            "id": constraint_id,
            "layer": "Constraints",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [context_id] if context_id else [], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(constraint_data)
        if node:
            constraint_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return constraint_dict, None
        else:
            return None, "Failed to create constraint"
    except Exception as e:
        return None, str(e)


def get_constraints() -> list[dict[str, Any]]:
    """Get all Constraints-layer items."""
    todos = load_todos()
    constraint_nodes = todos.get("Constraints", [])

    constraints = []
    for node in constraint_nodes:
        constraint_dict = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "status": node.status,
            "owner": node.metadata.owner,
            "labels": node.metadata.labels,
        }
        constraints.append(constraint_dict)

    return constraints


def complete_constraint(constraint_id: str) -> tuple[Node | None, str | None]:
    """Mark a Constraint as complete."""
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        todos = load_todos()
        constraints = todos.get("Constraints", [])
        constraint = None
        for c in constraints:
            if c.id == constraint_id:
                constraint = c
                break

        if not constraint:
            return None, f"Constraint with ID '{constraint_id}' not found"

        if constraint.status == "done":
            return constraint, None  # Already completed

        updated_constraint = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                constraint_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": constraint.metadata.owner,
                        "labels": constraint.metadata.labels,
                        "severity": constraint.metadata.severity,
                        "work_type": constraint.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_constraint:
            return None, "Failed to update constraint status in database"

        node = _convert_db_node_to_node(updated_constraint)
        return node, None
    finally:
        db.close()


# Layer 5: Requirements functions
def add_requirement(
    title: str, description: str, constraint_id: str | None = None
) -> tuple[dict[str, Any] | None, str | None]:
    """Add a new Requirement to the ToDoWrite system."""
    try:
        import uuid

        requirement_id = f"requirement-{uuid.uuid4().hex[:12]}"
        requirement_data = {
            "id": requirement_id,
            "layer": "Requirements",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [constraint_id] if constraint_id else [], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(requirement_data)
        if node:
            requirement_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return requirement_dict, None
        else:
            return None, "Failed to create requirement"
    except Exception as e:
        return None, str(e)


def get_requirements() -> list[dict[str, Any]]:
    """Get all Requirements-layer items."""
    todos = load_todos()
    requirement_nodes = todos.get("Requirements", [])

    requirements = []
    for node in requirement_nodes:
        requirement_dict = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "status": node.status,
            "owner": node.metadata.owner,
            "labels": node.metadata.labels,
        }
        requirements.append(requirement_dict)

    return requirements


def complete_requirement(requirement_id: str) -> tuple[Node | None, str | None]:
    """Mark a Requirement as complete."""
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        todos = load_todos()
        requirements = todos.get("Requirements", [])
        requirement = None
        for r in requirements:
            if r.id == requirement_id:
                requirement = r
                break

        if not requirement:
            return None, f"Requirement with ID '{requirement_id}' not found"

        if requirement.status == "done":
            return requirement, None  # Already completed

        updated_requirement = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                requirement_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": requirement.metadata.owner,
                        "labels": requirement.metadata.labels,
                        "severity": requirement.metadata.severity,
                        "work_type": requirement.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_requirement:
            return None, "Failed to update requirement status in database"

        node = _convert_db_node_to_node(updated_requirement)
        return node, None
    finally:
        db.close()


# Layer 6: Acceptance Criteria functions
def add_acceptance_criteria(
    title: str, description: str, requirement_id: str | None = None
) -> tuple[dict[str, Any] | None, str | None]:
    """Add new Acceptance Criteria to the ToDoWrite system."""
    try:
        import uuid

        ac_id = f"acceptance-{uuid.uuid4().hex[:12]}"
        ac_data = {
            "id": ac_id,
            "layer": "Acceptance Criteria",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [requirement_id] if requirement_id else [], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(ac_data)
        if node:
            ac_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return ac_dict, None
        else:
            return None, "Failed to create acceptance criteria"
    except Exception as e:
        return None, str(e)


def get_acceptance_criteria() -> list[dict[str, Any]]:
    """Get all Acceptance Criteria items."""
    todos = load_todos()
    ac_nodes = todos.get("Acceptance Criteria", [])

    acceptance_criteria = []
    for node in ac_nodes:
        ac_dict = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "status": node.status,
            "owner": node.metadata.owner,
            "labels": node.metadata.labels,
        }
        acceptance_criteria.append(ac_dict)

    return acceptance_criteria


def complete_acceptance_criteria(ac_id: str) -> tuple[Node | None, str | None]:
    """Mark Acceptance Criteria as complete."""
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        todos = load_todos()
        ac_items = todos.get("Acceptance Criteria", [])
        ac = None
        for a in ac_items:
            if a.id == ac_id:
                ac = a
                break

        if not ac:
            return None, f"Acceptance Criteria with ID '{ac_id}' not found"

        if ac.status == "done":
            return ac, None  # Already completed

        updated_ac = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                ac_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": ac.metadata.owner,
                        "labels": ac.metadata.labels,
                        "severity": ac.metadata.severity,
                        "work_type": ac.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_ac:
            return None, "Failed to update acceptance criteria status in database"

        node = _convert_db_node_to_node(updated_ac)
        return node, None
    finally:
        db.close()


# Layer 7: Interface Contract functions
def add_interface_contract(
    title: str, description: str, ac_id: str | None = None
) -> tuple[dict[str, Any] | None, str | None]:
    """Add a new Interface Contract to the ToDoWrite system."""
    try:
        import uuid

        ic_id = f"interface-{uuid.uuid4().hex[:12]}"
        ic_data = {
            "id": ic_id,
            "layer": "Interface Contract",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [ac_id] if ac_id else [], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
        }

        node = create_node(ic_data)
        if node:
            ic_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return ic_dict, None
        else:
            return None, "Failed to create interface contract"
    except Exception as e:
        return None, str(e)


def get_interface_contracts() -> list[dict[str, Any]]:
    """Get all Interface Contract items."""
    todos = load_todos()
    ic_nodes = todos.get("Interface Contract", [])

    interface_contracts = []
    for node in ic_nodes:
        ic_dict = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "status": node.status,
            "owner": node.metadata.owner,
            "labels": node.metadata.labels,
        }
        interface_contracts.append(ic_dict)

    return interface_contracts


def complete_interface_contract(ic_id: str) -> tuple[Node | None, str | None]:
    """Mark an Interface Contract as complete."""
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        todos = load_todos()
        ic_items = todos.get("Interface Contract", [])
        ic = None
        for i in ic_items:
            if i.id == ic_id:
                ic = i
                break

        if not ic:
            return None, f"Interface Contract with ID '{ic_id}' not found"

        if ic.status == "done":
            return ic, None  # Already completed

        updated_ic = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                ic_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": ic.metadata.owner,
                        "labels": ic.metadata.labels,
                        "severity": ic.metadata.severity,
                        "work_type": ic.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_ic:
            return None, "Failed to update interface contract status in database"

        node = _convert_db_node_to_node(updated_ic)
        return node, None
    finally:
        db.close()


# Layer 12: Command functions
def add_command(
    title: str,
    description: str,
    command_shell: str,
    subtask_id: str | None = None,
    ac_ref: str = "",
) -> tuple[dict[str, Any] | None, str | None]:
    """Add a new Command to the ToDoWrite system.

    Commands must be direct children of SubTasks. This enforces the hierarchy:
    Phase -> Step -> Task -> SubTask -> Command

    Agricultural Context: Commands represent executable operations in farm
    automation workflows. Enforcing proper hierarchy ensures command chains
    are well-defined and traceable through the task structure.
    """
    try:
        import uuid

        # Validate parent layer if subtask_id is provided
        if subtask_id:
            parent_node = get_node_by_id(subtask_id)
            if not parent_node:
                return None, f"Parent node with ID '{subtask_id}' not found"

            if parent_node.layer != "SubTask":
                return (
                    None,
                    f"Commands can only be children of SubTasks, not {parent_node.layer}. "
                    "Hierarchy violation: Phase -> Step -> Task -> SubTask -> Command",
                )

        command_id = f"command-{uuid.uuid4().hex[:12]}"
        command_data = {
            "id": command_id,
            "layer": "Command",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [subtask_id] if subtask_id else [], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
            "command": {
                "ac_ref": ac_ref or f"AC-{uuid.uuid4().hex[:8].upper()}",
                "run": {"shell": command_shell},
                "artifacts": [],
            },
        }

        node = create_node(command_data)
        if node:
            command_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
                "command": {
                    "ac_ref": node.command.ac_ref if node.command else "",
                    "shell": node.command.run.get("shell", "") if node.command else "",
                    "artifacts": node.command.artifacts if node.command else [],
                },
            }
            return command_dict, None
        else:
            return None, "Failed to create command"
    except Exception as e:
        return None, str(e)


def get_commands() -> list[dict[str, Any]]:
    """Get all Command-layer items."""
    todos = load_todos()
    command_nodes = todos.get("Command", [])

    commands = []
    for node in command_nodes:
        command_dict = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "status": node.status,
            "owner": node.metadata.owner,
            "labels": node.metadata.labels,
            "command": {
                "ac_ref": node.command.ac_ref if node.command else "",
                "shell": node.command.run.get("shell", "") if node.command else "",
                "artifacts": node.command.artifacts if node.command else [],
            },
        }
        commands.append(command_dict)

    return commands


def complete_command(command_id: str) -> tuple[Node | None, str | None]:
    """Mark a Command as complete."""
    db = SessionLocal()
    repository: NodeRepository = NodeRepository(db)
    try:
        from datetime import datetime

        todos = load_todos()
        commands = todos.get("Command", [])
        command = None
        for c in commands:
            if c.id == command_id:
                command = c
                break

        if not command:
            return None, f"Command with ID '{command_id}' not found"

        if command.status == "done":
            return command, None  # Already completed

        updated_command = cast(
            SQLAModelNode,
            repository.update_node_by_id(
                command_id,
                {
                    "status": "done",
                    "metadata": {
                        "owner": command.metadata.owner,
                        "labels": command.metadata.labels,
                        "severity": command.metadata.severity,
                        "work_type": command.metadata.work_type,
                        "date_completed": datetime.now().isoformat(),
                    },
                },
            ),
        )

        if not updated_command:
            return None, "Failed to update command status in database"

        node = _convert_db_node_to_node(updated_command)
        return node, None
    finally:
        db.close()
