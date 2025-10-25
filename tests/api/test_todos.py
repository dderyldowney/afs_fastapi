import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from afs_fastapi.api.main import app


@pytest_asyncio.fixture(name="client")
async def client_fixture():
    with TestClient(app=app) as client:
        yield client


@pytest.mark.asyncio
async def test_initialize_todowrite_database(client: TestClient):
    response = client.post("/todos/init_db")
    assert response.status_code == 200
    assert response.json() == {"message": "ToDoWrite database initialized successfully."}


@pytest.mark.asyncio
async def test_create_todo_item(client: TestClient):
    # Ensure database is initialized before creating items
    client.post("/todos/init_db")

    todo_data = {
        "node_type": "Goal",
        "title": "Test Goal",
        "description": "This is a test goal.",
        "status": "planned",
        "priority": "high",
        "parent_id": None,
    }
    response = client.post("/todos/", json=todo_data)
    if response.status_code != 201:
        print(response.json())
    assert response.status_code == 201
    data = response.json()
    print(data)
    assert data["title"] == "Test Goal"
    assert data["node_type"] == "Goal"
    assert "node_id" in data


@pytest.mark.asyncio
async def test_get_all_goals(client: TestClient):
    # Ensure database is initialized and a goal exists
    client.post("/todos/init_db")
    todo_data = {
        "node_type": "Goal",
        "title": "Another Test Goal",
        "description": "Another test goal description.",
        "status": "planned",
        "priority": "medium",
        "parent_id": None,
    }
    client.post("/todos/", json=todo_data)

    response = client.get("/todos/goals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(goal["title"] == "Another Test Goal" for goal in data)


@pytest.mark.asyncio
async def test_load_todowrite_todos(client: TestClient):
    # Ensure database is initialized and some todos exist
    client.post("/todos/init_db")
    todo_data = {
        "node_type": "Task",
        "title": "Loadable Task",
        "description": "A task to be loaded.",
        "status": "in_progress",
        "priority": "low",
        "parent_id": None,
    }
    client.post("/todos/", json=todo_data)

    response = client.post("/todos/load_todos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(todo["title"] == "Loadable Task" for todo in data)
