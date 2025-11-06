# docs/verification/create_library_inventory.py
import ast
import json
from pathlib import Path


def analyze_library_structure():
    """Analyze the complete library structure and create inventory."""
    library_root = Path("afs_fastapi")

    inventory = {
        "modules": [],
        "classes": [],
        "functions": [],
        "endpoints": [],
        "models": [],
        "database_schemas": []
    }

    for py_file in library_root.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file) as f:
            try:
                tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        inventory["classes"].append({
                            "name": node.name,
                            "file": str(py_file.relative_to(library_root)),
                            "line": node.lineno,
                            "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        })
                    elif isinstance(node, ast.FunctionDef):
                        inventory["functions"].append({
                            "name": node.name,
                            "file": str(py_file.relative_to(library_root)),
                            "line": node.lineno
                        })

            except SyntaxError as e:
                print(f"Syntax error in {py_file}: {e}")

    return inventory

if __name__ == "__main__":
    inventory = analyze_library_structure()
    with open("docs/verification/component_mapping.json", "w") as f:
        json.dump(inventory, f, indent=2)