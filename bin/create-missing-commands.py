#!/usr/bin/env python3
"""
Create all missing ToDoWrite layer commands systematically.
"""

import os
from pathlib import Path

# Define the layers and their command patterns
LAYERS = [
    {"name": "context", "layer": "Context", "icon": "🌍"},
    {"name": "constraint", "layer": "Constraints", "icon": "⚠️"},
    {"name": "requirement", "layer": "Requirements", "icon": "📋"},
    {"name": "acceptance", "layer": "Acceptance Criteria", "icon": "✅"},
    {"name": "interface", "layer": "Interface Contract", "icon": "🔌"},
    {"name": "phase", "layer": "Phase", "icon": "📅"},
    {"name": "command", "layer": "Command", "icon": "⚡"},
]

def create_status_command(layer_info):
    """Create a status command for a layer."""
    name = layer_info["name"]
    layer = layer_info["layer"]
    icon = layer_info["icon"]
    
    # Handle special cases for function names
    if name == "acceptance":
        get_func = "get_acceptance_criteria"
        plural = "acceptance_criteria"
    elif name == "interface":
        get_func = "get_interface_contracts"
        plural = "interface_contracts"
    elif name == "constraint":
        get_func = "get_constraints"
        plural = "constraints"
    elif name == "requirement":
        get_func = "get_requirements"
        plural = "requirements"
    else:
        get_func = f"get_{name}s"
        plural = f"{name}s"
    
    content = f'''#!/usr/bin/env python3
# type: ignore

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from todowrite import ToDoWrite  # noqa: E402
from todowrite.database.models import Node  # noqa: E402


def main():
    # Initialize ToDoWrite app instance
    app = ToDoWrite()
    parser = argparse.ArgumentParser(description="Display status of all {layer}s in the ToDoWrite system.")
    parser.add_argument("--{name}-id", type=str, help="Show details for a specific {name} ID.")
    args = parser.parse_args()

    if getattr(args, "{name}_id", None):
        # Show specific {name} details
        todos = app.load_todos()
        {plural} = todos.get("{layer}", [])
        {name} = None
        for item in {plural}:
            if item.id == getattr(args, "{name}_id"):
                {name} = item
                break

        if not {name}:
            print(f"Error: {layer} with ID '{{getattr(args, '{name}_id')}}' not found.")
            sys.exit(1)

        print(f"{icon} {layer} Details: {{{name}.id}}")
        print("=" * 50)
        print(f"Title: {{{name}.title}}")
        print(f"Description: {{{name}.description}}")
        print(f"Status: {{{name}.status}}")
        print(f"Owner: {{{name}.metadata.owner}}")
        print(f"Labels: {{', '.join({name}.metadata.labels) if {name}.metadata.labels else 'None'}}")
        print(f"Parents: {{', '.join({name}.links.parents) if {name}.links.parents else 'None'}}")
        print(f"Children: {{', '.join({name}.links.children) if {name}.links.children else 'None'}}")
    else:
        # Show all {plural}
        {plural} = {get_func}()
        
        if not {plural}:
            print("No {plural} found in the ToDoWrite system.")
            return

        print("{icon} All {layer}s Status")
        print("=" * 50)
        
        for item in {plural}:
            status_icon = "✓" if item["status"] == "done" else "○" if item["status"] == "active" else "·"
            print(f"{{status_icon}} {{item['id']}}")
            print(f"   Title: {{item['title']}}")
            print(f"   Status: {{item['status']}}")
            print()

        print(f"Total {layer}s: {{len({plural})}}")
        completed = len([item for item in {plural} if item["status"] == "done"])
        active = len([item for item in {plural} if item["status"] == "active"])
        planned = len([item for item in {plural} if item["status"] == "planned"])
        print(f"Completed: {{completed}}, Active: {{active}}, Planned: {{planned}}")


if __name__ == "__main__":
    main()'''
    
    return content

def main():
    # Initialize ToDoWrite app instance
    app = ToDoWrite()
    """Create all missing status commands."""
    bin_dir = Path(__file__).parent
    
    print("🏗️  Creating missing ToDoWrite status commands...")
    
    for layer_info in LAYERS:
        name = layer_info["name"]
        
        # Create status command
        status_file = bin_dir / f"{name}-status"
        if not status_file.exists():
            status_file.write_text(create_status_command(layer_info))
            status_file.chmod(0o755)
            print(f"✓ Created {name}-status")
    
    print("✅ All missing status commands created!")

if __name__ == "__main__":
    main()
