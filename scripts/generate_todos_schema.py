import json
import os

from pydantic import TypeAdapter

from afs_fastapi.core.todos_manager import TodosData


def generate_schema():
    """Generates and saves the JSON schema for TodosData."""
    adapter = TypeAdapter(TodosData)
    json_schema = adapter.json_schema()

    # Define project_root here, as it's needed for schema_dir
    # This assumes the script is run from the project root or afs_fastapi is installed
    project_root = os.getcwd()

    schema_dir = os.path.join(project_root, ".claude")
    os.makedirs(schema_dir, exist_ok=True)
    schema_file_path = os.path.join(schema_dir, "todos_schema.json")

    with open(schema_file_path, "w") as f:
        json.dump(json_schema, f, indent=2)

    print(f"JSON schema for TodosData saved to {schema_file_path}")


if __name__ == "__main__":
    generate_schema()
