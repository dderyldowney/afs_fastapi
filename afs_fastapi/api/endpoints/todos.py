from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from todowrite.app import LayerType, Node as ToDoWriteNode, StatusType

from afs_fastapi.core.todowrite_config import get_global_todowrite_app, get_todowrite_status

router = APIRouter()

# Get configured TodoWrite instance for API operations
todowrite_app = get_global_todowrite_app()


class LabelModel(BaseModel):
    name: str


class LinkModel(BaseModel):
    parents: list[str] = Field(default_factory=list)
    children: list[str] = Field(default_factory=list)


class MetadataModel(BaseModel):
    owner: str
    labels: list[str] = Field(default_factory=list)
    severity: str = ""
    work_type: str = ""


type NodeType = LayerType
type Status = StatusType
type Priority = Literal["low", "medium", "high", "critical"]


class ToDoWriteNodeModel(BaseModel):
    node_id: str
    node_type: NodeType
    title: str
    description: str | None = None
    status: Status
    priority: Priority
    labels: list[LabelModel]
    links: LinkModel
    metadata: MetadataModel
    parent_id: str | None = None
    children_ids: list[str]


class CreateToDoRequest(BaseModel):
    node_type: NodeType = Field(
        ..., description="Type of the ToDo item (e.g., Goal, Phase, Step, Task, SubTask)"
    )
    title: str = Field(..., description="Title of the ToDo item")
    description: str | None = Field(None, description="Detailed description of the ToDo item")
    status: Status = Field("planned", description="Current status of the ToDo item")
    priority: Priority = Field("medium", description="Priority of the ToDo item")
    parent_id: str | None = Field(None, description="ID of the parent node, if applicable")


class ToDoResponse(BaseModel):
    node_id: str = Field(..., alias="id")
    node_type: NodeType = Field(..., alias="layer")
    title: str
    description: str | None
    status: Status
    priority: Priority = Field(..., alias="severity")
    parent_id: str | None = None
    children_ids: list[str] = Field(default_factory=list)
    labels: list[LabelModel] = Field(default_factory=list)
    links: LinkModel
    metadata: MetadataModel

    @classmethod
    def from_todowrite_node(cls, node: ToDoWriteNode) -> "ToDoResponse":
        return cls(
            id=node.id,
            layer=node.layer,
            title=node.title,
            description=node.description,
            status=node.status,
            severity=node.metadata.severity,
            parent_id=node.links.parents[0] if node.links.parents else None,
            children_ids=node.links.children,
            labels=[LabelModel(name=label) for label in node.metadata.labels],
            links=LinkModel(parents=node.links.parents, children=node.links.children),
            metadata=MetadataModel(
                owner=node.metadata.owner,
                labels=node.metadata.labels,
                severity=node.metadata.severity,
                work_type=node.metadata.work_type,
            ),
        )

    @classmethod
    def from_todowrite_dict(cls, node_dict: dict) -> "ToDoResponse":
        """Convert ToDoWrite dictionary format to ToDoResponse."""
        return cls(
            id=node_dict.get("id", ""),
            layer=node_dict.get("layer", "Goal"),  # Default to Goal for get_goals() results
            title=node_dict.get("title", ""),
            description=node_dict.get("description"),
            status=node_dict.get("status", "planned"),
            severity=node_dict.get("priority", "medium"),  # get_goals() uses 'priority' field
            parent_id=None,  # Dictionary format doesn't include parent info
            children_ids=[],  # Dictionary format doesn't include children info
            labels=[LabelModel(name=label) for label in node_dict.get("labels", [])],
            links=LinkModel(parents=[], children=[]),
            metadata=MetadataModel(
                owner=node_dict.get("owner", "system"),
                labels=node_dict.get("labels", []),
                severity=node_dict.get("priority", "medium"),
                work_type="",
            ),
        )


@router.post("/", response_model=ToDoResponse, status_code=201)
async def create_todo_item(request: CreateToDoRequest) -> ToDoResponse:
    """
    Create a new ToDo item (Goal, Phase, Step, Task, SubTask).
    """
    try:
        import uuid

        node_id = str(uuid.uuid4())
        node_data = {
            "id": node_id,
            "layer": request.node_type,
            "title": request.title,
            "description": request.description,
            "status": request.status,
            "links": {"parents": [request.parent_id] if request.parent_id else [], "children": []},
            "metadata": {
                "owner": "system",  # Default owner
                "labels": [],
                "severity": request.priority,  # Map priority to severity
                "work_type": "",
            },
        }
        new_node = todowrite_app.create_node(node_data)
        return ToDoResponse.from_todowrite_node(new_node)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/goals", response_model=list[ToDoResponse])
async def get_all_goals() -> list[ToDoResponse]:
    """
    Retrieve all ToDoWrite goals.
    """
    try:
        todos_dict = todowrite_app.load_todos()
        # Extract only Goal layer nodes
        goals = todos_dict.get("Goal", [])
        return [ToDoResponse.from_todowrite_node(goal) for goal in goals]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve goals: {e}") from e


@router.post("/init_db", status_code=200)
async def initialize_todowrite_database() -> dict[str, str]:
    """
    Initialize the ToDoWrite database.
    """
    try:
        todowrite_app.init_database()
        return {"message": "ToDoWrite database initialized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {e}") from e


@router.post("/load_todos", response_model=list[ToDoResponse])
async def load_todowrite_todos() -> list[ToDoResponse]:
    """
    Load ToDo items from the ToDoWrite system.
    """
    try:
        todos_dict = todowrite_app.load_todos()
        all_todos = []
        for layer_nodes in todos_dict.values():
            for todo_node in layer_nodes:
                all_todos.append(ToDoResponse.from_todowrite_node(todo_node))
        return all_todos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load todos: {e}") from e


@router.get("/config", response_model=dict[str, str])
async def get_todowrite_config() -> dict[str, str]:
    """
    Get TodoWrite configuration status.

    Returns information about database configuration, storage preference,
    and connection status for agricultural robotics task management.
    """
    try:
        config_status = get_todowrite_status()

        # Test database connection
        try:
            todowrite_app.load_todos()
            config_status["connection_status"] = "Connected"
        except Exception as e:
            config_status["connection_status"] = f"Error: {str(e)}"

        return config_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {e}") from e
