from typing import Literal, TypeAlias

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from todowrite.manager import (
    LayerType,
    Node as ToDoWriteNode,
    StatusType,
    create_node,
    get_goals,
    init_database,
    load_todos,
)

router = APIRouter()


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


NodeType: TypeAlias = LayerType
Status: TypeAlias = StatusType
Priority: TypeAlias = Literal["low", "medium", "high", "critical"]


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
        new_node = create_node(node_data)
        return ToDoResponse.from_todowrite_node(new_node)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/goals", response_model=list[ToDoResponse])
async def get_all_goals() -> list[ToDoResponse]:
    """
    Retrieve all ToDoWrite goals.
    """
    goals = get_goals()
    return [ToDoResponse.from_todowrite_node(goal) for goal in goals]


@router.post("/init_db", status_code=200)
async def initialize_todowrite_database() -> dict[str, str]:
    """
    Initialize the ToDoWrite database.
    """
    try:
        init_database()
        return {"message": "ToDoWrite database initialized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {e}") from e


@router.post("/load_todos", response_model=list[ToDoResponse])
async def load_todowrite_todos() -> list[ToDoResponse]:
    """
    Load ToDo items from the ToDoWrite system.
    """
    try:
        todos_dict = load_todos()
        all_todos = []
        for layer_nodes in todos_dict.values():
            for todo_node in layer_nodes:
                all_todos.append(ToDoResponse.from_todowrite_node(todo_node))
        return all_todos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load todos: {e}") from e
