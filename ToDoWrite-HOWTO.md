# ToDoWrite System: Complete User Guide

> **A practical guide to using the 12-layer hierarchical task management system for agricultural robotics development**

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Understanding the 12-Layer Hierarchy](#understanding-the-12-layer-hierarchy)
3. [Core Concepts & Data Structures](#core-concepts--data-structures)
4. [Command-Line Interface (CLI) Usage](#command-line-interface-cli-usage)
5. [Python Module Programming Interface](#python-module-programming-interface)
6. [Detailed Layer Management (CRUD Operations)](#detailed-layer-management-crud-operations)
7. [ToDoWrite Node JSON Schema](#todowrite-node-json-schema)
8. [Workflow & Process Diagrams](#workflow--process-diagrams)
9. [Getting Started](#getting-started)
10. [Daily Development Workflow](#daily-development-workflow)
11. [Agricultural Robotics Examples](#agricultural-robotics-examples)
12. [Advanced Integration Patterns](#advanced-integration-patterns)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)

---

## Introduction

The ToDoWrite system is a **12-layer hierarchical task management framework** designed specifically for safety-critical agricultural robotics development. It provides systematic project breakdown from strategic goals down to executable commands, ensuring proper documentation, traceability, and compliance with agricultural safety standards.

### Key Principles

- **📝 Layers 1-11: Pure Planning** - Declarative documentation only (no execution)
- **⚡ Layer 12: Commands Only** - The single executable layer
- **🔗 Full Traceability** - Every item links to parents and children
- **🌾 Agricultural Focus** - Built for multi-tractor coordination and ISO compliance
- **🛡️ Safety-Critical** - Designed for agricultural automation safety standards

---

## Understanding the 12-Layer Hierarchy

### The Strategic-to-Tactical Pyramid

```
🎯 STRATEGIC PLANNING (Layers 1-4)
├── 1. Goal           ← Business outcomes & mission intent
├── 2. Concept        ← High-level architectural ideas
├── 3. Context        ← Environment, actors, assumptions
└── 4. Constraints    ← Standards, safety, legal limits

📋 SPECIFICATION (Layers 5-7)
├── 5. Requirements   ← Atomic, testable statements
├── 6. Acceptance Criteria ← Objective pass/fail tests
└── 7. Interface Contract ← APIs, protocols, data formats

🚀 IMPLEMENTATION (Layers 8-11)
├── 8. Phase          ← Major delivery milestones
├── 9. Step           ← Single-concern implementation units
├── 10. Task          ← Individual contributor work
└── 11. SubTask       ← Granular planning elements

⚡ EXECUTION (Layer 12)
└── 12. Command       ← ONLY executable layer (scripts, CLI, APIs)
```

### Layer Responsibilities

| Layer | Purpose | Example | Executable? |
|-------|---------|---------|-------------|
| Goal | Strategic outcomes | "Implement autonomous tractor coordination" | ❌ |
| Concept | Big-picture ideas | "Multi-agent coordination architecture" | ❌ |
| Context | Environmental factors | "500-acre corn fields with GPS coverage" | ❌ |
| Constraints | Limits & standards | "ISO 11783 compliance, <50ms latency" | ❌ |
| Requirements | Testable specifications | "CAN bus 250kbps with message validation" | ❌ |
| Acceptance Criteria | Pass/fail tests | "Address claim completes within 2 seconds" | ❌ |
| Interface Contract | Technical contracts | "JSON schema for tractor position data" | ❌ |
| Phase | Development phases | "Hardware Integration Phase" | ❌ |
| Step | Implementation steps | "Configure CAN bus interfaces" | ❌ |
| Task | Work assignments | "Install CAN transceivers on tractors" | ❌ |
| SubTask | Granular planning | "Test CAN message throughput" | ❌ |
| Command | Executable code | `sudo ip link set can0 type can bitrate 250000` | ✅ |

### Flexible Entry, Strict Adherence

The ToDoWrite system is designed to accommodate various project initiation points. Users are **not mandated to begin at the 'Goal' layer**; you may choose to start defining your project at any layer that best suits your current planning context (e.g., 'Project', 'Phase', or even 'Task').

**However, regardless of your chosen starting layer, the following strict rules apply:**

1.  **Full Hierarchy Definition:** All subsequent layers, from your chosen starting point down through to, and including, the 'Command' layer (Layer 12), **MUST be fully defined**. No layers in the hierarchy can be skipped or left undefined.
2.  **Strict Parent-Child Relationships:** Every node must have a clearly defined parent (unless it's the top-most node of your chosen starting hierarchy) and, if applicable, children. The hierarchical flow (e.g., Phase -> Step -> Task -> SubTask -> Command) must be strictly maintained.
3.  **Single-Concern Principle:** Each node at every layer must adhere to the single-concern principle. A 'Step' should represent one distinct implementation unit, a 'Task' one piece of individual work, and so on. This ensures clarity, modularity, and traceability.
4.  **Layer Integrity Validation:** The system will enforce layer integrity. Any attempt to define a child node without its direct parent, or to define a layer out of sequence, will result in a validation error.
5.  **Complete Hierarchy to Command:** The ultimate objective for any defined work is to trace it down to executable 'Command' nodes. This ensures that all planning eventually leads to actionable implementation.

This flexibility allows for agile planning while guaranteeing the structural integrity and comprehensive traceability essential for safety-critical agricultural robotics development.

---

## Command-Line Interface (CLI) Usage

The ToDoWrite system provides a comprehensive set of command-line tools for managing all 12 layers of the hierarchy. This section covers practical usage patterns for intermediate programmers.

### Command Discovery and Overview

```bash
# View all available commands organized by layer
./bin/todowrite-commands

# View commands for a specific layer
./bin/todowrite-commands --layer Goal
./bin/todowrite-commands --layer Phase

# View commands by operation type
./bin/todowrite-commands --operation add
./bin/todowrite-commands --operation status
```

### Layer-Specific Command Patterns

Each layer follows consistent CRUD (Create, Read, Update, Delete) patterns:

#### Strategic Planning Layers (1-7)

```bash
# Goal Layer (Layer 1)
./bin/goal-add "Autonomous Multi-Tractor Coordination"
./bin/goal-status                    # List all goals
./bin/goal-status --goal-id goal-123 # Specific goal details
./bin/goal-complete goal-123
./bin/goal-delete goal-123 --confirm

# Concept Layer (Layer 2)
./bin/concept-add "Distributed Control Architecture" --goal-id goal-123
./bin/concept-status

# Context Layer (Layer 3)
./bin/context-status

# Requirements Layer (Layer 5)
./bin/requirement-status

# Acceptance Criteria Layer (Layer 6)
./bin/acceptance-status

# Interface Contract Layer (Layer 7)
./bin/interface-status
```

#### Implementation Layers (8-11)

```bash
# Phase Layer (Layer 8)
./bin/phase-add "Hardware Integration Phase" --goal-id goal-123
./bin/phase-status
./bin/phase-complete phase-456
./bin/phase-delete phase-456

# Step Layer (Layer 9)
./bin/step-add "Configure CAN Bus Network" --description "Set up 250kbps CAN network"
./bin/step-status
./bin/step-activate step-789
./bin/step-complete step-789

# Task Layer (Layer 10)
./bin/task-add "Install CAN Transceivers" --description "Mount hardware on tractors"
./bin/task-status
./bin/task-activate task-101
./bin/task-complete task-101
./bin/task-pause task-101
./bin/task-resume task-101

# SubTask Layer (Layer 11)
./bin/subtask-add "Test CAN Message Throughput" --description "Validate 250kbps performance"
./bin/subtask-status
./bin/subtask-complete subtask-202
```

#### Execution Layer (12)

```bash
# Command Layer (Layer 12) - The only executable layer
./bin/command-add "Configure CAN Interface" "sudo ip link set can0 type can bitrate 250000" \
  --description "Set CAN bus to 250kbps" \
  --subtask-id subtask-202

./bin/command-status
./bin/command-execute command-303                    # Execute command
./bin/command-execute command-303 --dry-run          # Preview execution
./bin/command-execute command-303 --auto-complete    # Auto-mark complete on success
```

### Workflow Integration Commands

```bash
# System status and management
./bin/todo-status              # Complete system overview
./bin/strategic-status         # Strategic goals progress
./bin/loadsession             # Initialize development session
./bin/savesession             # Save current state
./bin/whereweare              # Current project status

# Session management with pause structure
./bin/quality-check-and-pause "Task completion" "Next: Hardware testing"
./bin/strategic-milestone-pause "Phase 1 Complete" "complete"
```

### Advanced CLI Usage Patterns

#### Hierarchical Workflow Example

```bash
# 1. Create strategic foundation
./bin/goal-add "Implement Precision Agriculture System"
GOAL_ID=$(./bin/goal-status | grep "goal-" | head -1 | awk '{print $2}')

# 2. Add implementation phases
./bin/phase-add "Sensor Integration" --goal-id $GOAL_ID
PHASE_ID=$(./bin/phase-status | grep "phase-" | head -1 | awk '{print $2}')

# 3. Break down into steps
./bin/step-add "Install GPS Modules" --description "RTK-GPS installation on tractors"
STEP_ID=$(./bin/step-status | grep "step-" | head -1 | awk '{print $2}')

# 4. Create specific tasks
./bin/task-add "Mount GPS Antenna" --description "Physical installation"
TASK_ID=$(./bin/task-status | grep "task-" | head -1 | awk '{print $2}')

# 5. Define executable commands
./bin/command-add "Test GPS Signal" "gpsd -D 5 -N -n /dev/ttyUSB0" \
  --description "Validate GPS receiver functionality"
```

#### Batch Operations and Scripting

```bash
#!/bin/bash
# Example: Batch status check across all layers

echo "=== ToDoWrite System Status ==="
echo "Goals: $(./bin/goal-status | grep "Total Goals" | cut -d: -f2)"
echo "Phases: $(./bin/phase-status | grep "Total Phases" | cut -d: -f2)"
echo "Tasks: $(./bin/task-status | grep "Total Tasks" | cut -d: -f2)"
echo "Commands: $(./bin/command-status | grep "Total Commands" | cut -d: -f2)"

# Find and execute all planned commands
./bin/command-status | grep "planned" | awk '{print $2}' | while read cmd_id; do
    echo "Executing: $cmd_id"
    ./bin/command-execute $cmd_id --auto-complete
done
```

---

## Python Module Programming Interface

For programmatic access, the ToDoWrite system provides a comprehensive Python API through the `afs_fastapi.todos.manager` module. This section demonstrates integration patterns for intermediate Python developers.

### Core Manager Functions

```python
from afs_fastapi.todos.manager import (
    # Node management
    create_node, update_node, delete_node, load_todos,

    # Layer-specific functions
    add_goal, get_goals, complete_goal,
    add_concept, get_concepts, complete_concept,
    add_phase, get_phases, complete_phase,
    add_step, add_task, add_subtask,
    add_command, get_commands, complete_command,

    # System functions
    get_active_items, get_active_phase,
    init_database, get_database_info
)
```

### Basic CRUD Operations

#### Creating Nodes Programmatically

```python
# Strategic layer creation
new_goal, error = add_goal(
    title="Autonomous Field Operations",
    description="Enable tractors to perform field operations without human intervention"
)

if error:
    print(f"Error creating goal: {error}")
else:
    goal_id = new_goal["id"]
    print(f"Created goal: {goal_id}")

# Implementation layer creation with parent linking
new_phase, error = add_phase(
    goal_id=goal_id,
    title="Sensor Integration Phase",
    description="Install and configure all required sensors"
)

if new_phase:
    phase_id = new_phase["id"]

    # Create step under phase
    new_step, error = add_step(
        phase_id=phase_id,
        name="GPS Module Installation",
        description="Install RTK-GPS modules on all tractors"
    )
```

#### Reading and Querying Data

```python
# Load all todos and filter by layer
todos = load_todos()
goals = todos.get("Goal", [])
phases = todos.get("Phase", [])
commands = todos.get("Command", [])

# Get active items across all layers
active_items = get_active_items(todos)
active_phase = active_items.get("Phase")

if active_phase:
    print(f"Currently working on: {active_phase.title}")

# Get typed data for specific layers
goal_items = get_goals()  # Returns list of dictionaries
phase_items = get_phases()  # Returns list of PhaseItem objects

# Filter and search
agricultural_goals = [g for g in goal_items if "agricultural" in g.get("labels", [])]
high_priority_phases = [p for p in phase_items if p.metadata.severity == "high"]
```

#### Updating and Completing Nodes

```python
# Update node metadata
updated_node, error = update_node(goal_id, {
    "status": "in_progress",
    "metadata": {
        "owner": "agricultural-team",
        "labels": ["autonomous", "field-ops", "safety-critical"],
        "severity": "high",
        "work_type": "implementation"
    }
})

# Complete nodes with automatic timestamping
completed_goal, error = complete_goal(goal_id)
if completed_goal:
    print(f"Goal completed: {completed_goal.title}")
    print(f"Completion time: {completed_goal.metadata.date_completed}")
```

### Advanced Programming Patterns

#### Hierarchical Data Processing

```python
def analyze_project_hierarchy(goal_id: str) -> dict:
    """Analyze complete project hierarchy from goal down to commands."""
    todos = load_todos()

    # Find goal
    goals = todos.get("Goal", [])
    goal = next((g for g in goals if g.id == goal_id), None)
    if not goal:
        return {"error": "Goal not found"}

    # Traverse hierarchy
    analysis = {
        "goal": {"id": goal.id, "title": goal.title, "status": goal.status},
        "phases": [],
        "total_commands": 0,
        "completed_commands": 0
    }

    # Find child phases
    phases = todos.get("Phase", [])
    goal_phases = [p for p in phases if goal_id in p.links.parents]

    for phase in goal_phases:
        phase_data = {
            "id": phase.id,
            "title": phase.title,
            "status": phase.status,
            "steps": []
        }

        # Find child steps
        steps = todos.get("Step", [])
        phase_steps = [s for s in steps if phase.id in s.links.parents]

        for step in phase_steps:
            # Continue traversal through tasks -> subtasks -> commands
            commands = find_commands_for_step(step.id, todos)
            analysis["total_commands"] += len(commands)
            analysis["completed_commands"] += len([c for c in commands if c.status == "done"])

            phase_data["steps"].append({
                "id": step.id,
                "title": step.title,
                "command_count": len(commands)
            })

        analysis["phases"].append(phase_data)

    return analysis

def find_commands_for_step(step_id: str, todos: dict) -> list:
    """Find all commands that trace back to a specific step."""
    commands = []

    # Get tasks for step
    tasks = todos.get("Task", [])
    step_tasks = [t for t in tasks if step_id in t.links.parents]

    for task in step_tasks:
        # Get subtasks for task
        subtasks = todos.get("SubTask", [])
        task_subtasks = [st for st in subtasks if task.id in st.links.parents]

        for subtask in task_subtasks:
            # Get commands for subtask
            all_commands = todos.get("Command", [])
            subtask_commands = [c for c in all_commands if subtask.id in c.links.parents]
            commands.extend(subtask_commands)

    return commands
```

#### Batch Operations and Automation

```python
def create_agricultural_project_template(project_name: str) -> dict:
    """Create a complete agricultural project template."""

    # Create strategic foundation
    goal, error = add_goal(
        title=f"{project_name} - Agricultural Automation",
        description=f"Implement autonomous agricultural operations for {project_name}"
    )

    if error:
        return {"error": f"Failed to create goal: {error}"}

    goal_id = goal["id"]
    project_structure = {"goal_id": goal_id, "phases": []}

    # Define standard agricultural phases
    standard_phases = [
        ("Planning & Design", "System architecture and component selection"),
        ("Hardware Integration", "Install sensors, actuators, and communication systems"),
        ("Software Development", "Implement control algorithms and safety systems"),
        ("Field Testing", "Validate system performance in agricultural conditions"),
        ("Deployment", "Full-scale implementation and monitoring")
    ]

    for phase_title, phase_desc in standard_phases:
        phase, error = add_phase(goal_id, phase_title, phase_desc)
        if phase:
            project_structure["phases"].append({
                "id": phase["id"],
                "title": phase_title,
                "steps": []
            })

    return project_structure

def execute_command_pipeline(command_ids: list[str],
                           stop_on_error: bool = True) -> dict:
    """Execute a series of commands in sequence."""
    import subprocess

    results = {"executed": [], "failed": [], "skipped": []}
    todos = load_todos()
    commands = todos.get("Command", [])

    for cmd_id in command_ids:
        # Find command
        command = next((c for c in commands if c.id == cmd_id), None)
        if not command:
            results["skipped"].append({"id": cmd_id, "reason": "Command not found"})
            continue

        if not command.command or not command.command.run:
            results["skipped"].append({"id": cmd_id, "reason": "No executable command"})
            continue

        shell_cmd = command.command.run.get("shell", "")
        if not shell_cmd:
            results["skipped"].append({"id": cmd_id, "reason": "Empty shell command"})
            continue

        try:
            # Execute command
            result = subprocess.run(
                shell_cmd, shell=True, capture_output=True, text=True, timeout=300
            )

            execution_result = {
                "id": cmd_id,
                "title": command.title,
                "command": shell_cmd,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

            if result.returncode == 0:
                results["executed"].append(execution_result)
                # Auto-complete successful commands
                complete_command(cmd_id)
            else:
                results["failed"].append(execution_result)
                if stop_on_error:
                    break

        except subprocess.TimeoutExpired:
            results["failed"].append({
                "id": cmd_id,
                "title": command.title,
                "error": "Command timeout (300s)"
            })
            if stop_on_error:
                break
        except Exception as e:
            results["failed"].append({
                "id": cmd_id,
                "title": command.title,
                "error": str(e)
            })
            if stop_on_error:
                break

    return results
```

#### Integration with External Systems

```python
def export_to_project_management(goal_id: str, format: str = "json") -> dict:
    """Export ToDoWrite hierarchy to external project management format."""

    hierarchy = analyze_project_hierarchy(goal_id)

    if format == "json":
        return hierarchy
    elif format == "gantt":
        # Convert to Gantt chart format
        gantt_data = {
            "project": hierarchy["goal"]["title"],
            "tasks": []
        }

        for phase in hierarchy["phases"]:
            gantt_data["tasks"].append({
                "id": phase["id"],
                "name": phase["title"],
                "type": "phase",
                "children": [step["id"] for step in phase["steps"]]
            })

            for step in phase["steps"]:
                gantt_data["tasks"].append({
                    "id": step["id"],
                    "name": step["title"],
                    "type": "step",
                    "parent": phase["id"],
                    "duration": step.get("command_count", 1)  # Estimate based on commands
                })

        return gantt_data

    return {"error": "Unsupported format"}

def sync_with_git_issues(goal_id: str, repo_url: str) -> dict:
    """Synchronize ToDoWrite tasks with Git repository issues."""
    # This would integrate with GitHub/GitLab APIs
    # Implementation depends on specific Git platform

    todos = load_todos()
    tasks = todos.get("Task", [])

    # Find tasks related to the goal (through hierarchy)
    goal_tasks = find_tasks_for_goal(goal_id, todos)

    sync_results = {"created": [], "updated": [], "errors": []}

    for task in goal_tasks:
        if task.status == "planned":
            # Create new issue
            issue_data = {
                "title": task.title,
                "body": task.description,
                "labels": task.metadata.labels + ["todowrite", "agricultural"]
            }
            # API call to create issue would go here
            sync_results["created"].append(task.id)

    return sync_results
```

---

## Core Concepts & Data Structures

The ToDoWrite system manages `Node` objects, each representing an item in the 12-layer hierarchy. Each `Node` has a consistent structure:

*   **`id` (string):** Unique identifier (e.g., `GOAL-MYPROJECT`, `PH-INIT`, `TSK-CAN001`).
*   **`layer` (LayerType):** The hierarchical level (e.g., "Goal", "Phase", "SubTask").
*   **`title` (string):** A concise name for the node.
*   **`description` (string):** Detailed explanation of the node.
*   **`links` (Link):** Defines parent-child relationships.
    *   **`parents` (list[str]):** IDs of parent nodes.
    *   **`children` (list[str]):** IDs of child nodes.
*   **`metadata` (Metadata):** Additional descriptive information.
    *   **`owner` (string):** Responsible team or individual.
    *   **`labels` (list[str]):** Categorization tags (e.g., "agricultural", "safety-critical").
    *   **`severity` (string):** Importance/impact ("low", "med", "high").
    *   **`work_type` (string):** Type of work ("architecture", "spec", "implementation", etc.).
*   **`status` (StatusType):** Current state ("planned", "in_progress", "blocked", "done", "rejected").
*   **`command` (Command | None):** For "Command" layer nodes, defines the executable action.
    *   **`ac_ref` (string):** Reference to an Acceptance Criteria node.
    *   **`run` (dict):** Details of the command to execute (e.g., `shell`, `workdir`, `env`).
    *   **`artifacts` (list[str]):** Expected output files from command execution.

---

## Detailed Layer Management (CRUD Operations)

This section demonstrates how to perform Create, Read, Update, and Delete (CRUD) operations for each layer using the `afs_fastapi.todos.manager` Python module. These operations form the programmatic interface to the ToDoWrite system.

### General Notes on Usage:
*   All examples assume you are running Python from the project root.
*   `load_todos()` is used to retrieve the current state of the system.
*   `update_node()` and `delete_node()` are generic and apply to all layers.
*   `create_node()` is a generic function for creating any node type.
*   `json.dumps(..., indent=2)` is used for pretty-printing output.

### 1. Goal Layer (Strategic outcomes & mission intent)

```python
from afs_fastapi.todos.manager import add_goal, load_todos, update_node, delete_node, create_node
import json

# --- CREATE a Goal ---
print("--- Creating a new Goal ---")
new_goal, error = add_goal(
    title="Develop Autonomous Planting System",
    description="Implement a fully autonomous system for precision seed planting in varied agricultural terrains."
)
if new_goal:
    print(json.dumps(new_goal, indent=2))
    goal_id = new_goal["id"]
else:
    print(f"Error creating goal: {error}")
    goal_id = "GOAL-AUTONOMOUS-PLANTING" # Fallback for demonstration if creation fails

# --- READ Goals ---
print("\n--- Reading all Goals ---")
all_goals = load_todos().get("Goal", [])
for goal in all_goals:
    if goal.id == goal_id: # Find the newly created goal
        print(json.dumps(dataclasses.asdict(goal), indent=2))

# --- UPDATE a Goal ---
print(f"\n--- Updating Goal: {goal_id} status to 'in_progress' ---")
# First, retrieve the existing node to get its current links and metadata
goal_node_to_update = next((g for g in all_goals if g.id == goal_id), None)
if goal_node_to_update:
    node_data = {
        "status": "in_progress",
        "links": {"parents": goal_node_to_update.links.parents, "children": goal_node_to_update.links.children},
        "metadata": {"owner": "planting-team", "labels": ["autonomous", "planting"], "severity": "high", "work_type": "architecture"}
    }
    updated_goal, error = update_node(goal_id, node_data)
    if updated_goal:
        print(json.dumps(dataclasses.asdict(updated_goal), indent=2))
    else:
        print(f"Error updating goal: {error}")

# --- DELETE a Goal ---
print(f"\n--- Deleting Goal: {goal_id} ---")
delete_node(goal_id)
print(f"Goal {goal_id} deleted.")
# Verify deletion
remaining_goals = load_todos().get("Goal", [])
if not any(g.id == goal_id for g in remaining_goals):
    print(f"Goal {goal_id} successfully removed from system.")
```

### 2. Concept Layer (High-level architectural ideas)

```python
from afs_fastapi.todos.manager import create_node, load_todos, update_node, delete_node
import json

concept_id = "CON-PLANTING-ARCH"
goal_id_parent = "GOAL-AUTONOMOUS-PLANTING" # Assuming this goal exists or is created

# --- CREATE a Concept ---
print("--- Creating a new Concept ---")
concept_data = {
    "id": concept_id,
    "layer": "Concept",
    "title": "Modular Robotics Architecture for Planting",
    "description": "Design a modular software and hardware architecture for autonomous planting robots.",
    "status": "planned",
    "links": {"parents": [goal_id_parent], "children": []},
    "metadata": {"owner": "architecture-team", "labels": ["robotics", "modular"], "severity": "high", "work_type": "architecture"}
}
new_concept = create_node(concept_data)
if new_concept:
    print(json.dumps(dataclasses.asdict(new_concept), indent=2))
else:
    print(f"Error creating concept.")

# --- READ Concepts ---
print("\n--- Reading all Concepts ---")
all_concepts = load_todos().get("Concept", [])
for concept in all_concepts:
    print(json.dumps(dataclasses.asdict(concept), indent=2))

# --- UPDATE a Concept ---
print(f"\n--- Updating Concept: {concept_id} status to 'in_progress' ---")
concept_node_to_update = next((c for c in all_concepts if c.id == concept_id), None)
if concept_node_to_update:
    node_data = {
        "status": "in_progress",
        "links": {"parents": concept_node_to_update.links.parents, "children": concept_node_to_update.links.children},
        "metadata": {"owner": concept_node_to_update.metadata.owner, "labels": concept_node_to_update.metadata.labels, "severity": "high", "work_type": "architecture"}
    }
    updated_concept, error = update_node(concept_id, node_data)
    if updated_concept:
        print(json.dumps(dataclasses.asdict(updated_concept), indent=2))
    else:
        print(f"Error updating concept: {error}")

# --- DELETE a Concept ---
print(f"\n--- Deleting Concept: {concept_id} ---")
delete_node(concept_id)
print(f"Concept {concept_id} deleted.")
```

### 3. Context Layer (Environment, actors, assumptions)

```python
from afs_fastapi.todos.manager import create_node, load_todos, update_node, delete_node
import json

context_id = "CTX-FIELD-ENV"
concept_id_parent = "CON-PLANTING-ARCH" # Assuming this concept exists or is created

# --- CREATE a Context ---
print("--- Creating a new Context ---")
context_data = {
    "id": context_id,
    "layer": "Context",
    "title": "Typical Field Environment for Planting",
    "description": "Operating conditions include varied soil types, GPS availability, and potential for uneven terrain.",
    "status": "planned",
    "links": {"parents": [concept_id_parent], "children": []},
    "metadata": {"owner": "planning-team", "labels": ["environment", "field"], "severity": "med", "work_type": "spec"}
}
new_context = create_node(context_data)
if new_context:
    print(json.dumps(dataclasses.asdict(new_context), indent=2))

# --- READ Contexts ---
print("\n--- Reading all Contexts ---")
all_contexts = load_todos().get("Context", [])
for context in all_contexts:
    print(json.dumps(dataclasses.asdict(context), indent=2))

# --- UPDATE a Context ---
print(f"\n--- Updating Context: {context_id} description ---")
context_node_to_update = next((c for c in all_contexts if c.id == context_id), None)
if context_node_to_update:
    node_data = {
        "description": "Operating conditions include varied soil types, GPS availability (RTK), and potential for uneven terrain, with average temperatures between 10-25°C.",
        "links": {"parents": context_node_to_update.links.parents, "children": context_node_to_update.links.children},
        "metadata": {"owner": context_node_to_update.metadata.owner, "labels": context_node_to_update.metadata.labels, "severity": context_node_to_update.metadata.severity, "work_type": context_node_to_update.metadata.work_type}
    }
    updated_context, error = update_node(context_id, node_data)
    if updated_context:
        print(json.dumps(dataclasses.asdict(updated_context), indent=2))

# --- DELETE a Context ---
print(f"\n--- Deleting Context: {context_id} ---")
delete_node(context_id)
print(f"Context {context_id} deleted.")
```

### 4. Constraints Layer (Standards, safety, legal limits)

```python
from afs_fastapi.todos.manager import create_node, load_todos, update_node, delete_node
import json

constraint_id = "CST-ISO11783"
context_id_parent = "CTX-FIELD-ENV" # Assuming this context exists or is created

# --- CREATE a Constraint ---
print("--- Creating a new Constraint ---")
constraint_data = {
    "id": constraint_id,
    "layer": "Constraints",
    "title": "ISO 11783 Compliance for Communication",
    "description": "All inter-robot communication must adhere to ISO 11783 (ISOBUS) standards.",
    "status": "planned",
    "links": {"parents": [context_id_parent], "children": []},
    "metadata": {"owner": "safety-team", "labels": ["iso", "safety"], "severity": "high", "work_type": "spec"}
}
new_constraint = create_node(constraint_data)
if new_constraint:
    print(json.dumps(dataclasses.asdict(new_constraint), indent=2))

# --- READ Constraints ---
print("\n--- Reading all Constraints ---")
all_constraints = load_todos().get("Constraints", [])
for constraint in all_constraints:
    print(json.dumps(dataclasses.asdict(constraint), indent=2))

# --- UPDATE a Constraint ---
print(f"\n--- Updating Constraint: {constraint_id} work_type ---")
constraint_node_to_update = next((c for c in all_constraints if c.id == constraint_id), None)
if constraint_node_to_update:
    node_data = {
        "metadata": {"owner": constraint_node_to_update.metadata.owner, "labels": constraint_node_to_update.metadata.labels, "severity": constraint_node_to_update.metadata.severity, "work_type": "validation"},
        "links": {"parents": constraint_node_to_update.links.parents, "children": constraint_node_to_update.links.children}
    }
    updated_constraint, error = update_node(constraint_id, node_data)
    if updated_constraint:
        print(json.dumps(dataclasses.asdict(updated_constraint), indent=2))

# --- DELETE a Constraint ---
print(f"\n--- Deleting Constraint: {constraint_id} ---")
delete_node(constraint_id)
print(f"Constraint {constraint_id} deleted.")
```

### 5. Requirements Layer (Atomic, testable statements)

```python
from afs_fastapi.todos.manager import create_node, load_todos, update_node, delete_node
import json

requirement_id = "R-GPS-ACCURACY"
constraint_id_parent = "CST-ISO11783" # Assuming this constraint exists or is created

# --- CREATE a Requirement ---
print("--- Creating a new Requirement ---")
requirement_data = {
    "id": requirement_id,
    "layer": "Requirements",
    "title": "GPS Positioning Accuracy within 2cm",
    "description": "The autonomous planting system shall maintain GPS positioning accuracy within 2cm (RTK-corrected) during operation.",
    "status": "planned",
    "links": {"parents": [constraint_id_parent], "children": []},
    "metadata": {"owner": "engineering-team", "labels": ["gps", "accuracy"], "severity": "high", "work_type": "spec"}
}
new_requirement = create_node(requirement_data)
if new_requirement:
    print(json.dumps(dataclasses.asdict(new_requirement), indent=2))

# --- READ Requirements ---
print("\n--- Reading all Requirements ---")
all_requirements = load_todos().get("Requirements", [])
for req in all_requirements:
    print(json.dumps(dataclasses.asdict(req), indent=2))

# --- UPDATE a Requirement ---
print(f"\n--- Updating Requirement: {requirement_id} description ---")
req_node_to_update = next((r for r in all_requirements if r.id == requirement_id), None)
if req_node_to_update:
    node_data = {
        "description": "The autonomous planting system shall maintain GPS positioning accuracy within 2cm (RTK-corrected) during operation, across all field conditions.",
        "links": {"parents": req_node_to_update.links.parents, "children": req_node_to_update.links.children},
        "metadata": {"owner": req_node_to_update.metadata.owner, "labels": req_node_to_update.metadata.labels, "severity": req_node_to_update.metadata.severity, "work_type": req_node_to_update.metadata.work_type}
    }
    updated_req, error = update_node(requirement_id, node_data)
    if updated_req:
        print(json.dumps(dataclasses.asdict(updated_req), indent=2))

# --- DELETE a Requirement ---
print(f"\n--- Deleting Requirement: {requirement_id} ---")
delete_node(requirement_id)
print(f"Requirement {requirement_id} deleted.")
```

### 6. Acceptance Criteria Layer (Objective pass/fail tests)

```python
from afs_fastapi.todos.manager import create_node, load_todos, update_node, delete_node
import json

ac_id = "AC-GPS-001"
requirement_id_parent = "R-GPS-ACCURACY" # Assuming this requirement exists or is created

# --- CREATE Acceptance Criteria ---
print("--- Creating new Acceptance Criteria ---")
ac_data = {
    "id": ac_id,
    "layer": "Acceptance Criteria",
    "title": "GPS Accuracy Test: 95% of points within 2cm",
    "description": "Given a static test setup with RTK correction, when 100 GPS readings are taken over 5 minutes, then 95% of readings shall be within 2cm of the known ground truth.",
    "status": "planned",
    "links": {"parents": [requirement_id_parent], "children": []},
    "metadata": {"owner": "qa-team", "labels": ["gps", "test"], "severity": "high", "work_type": "validation"}
}
new_ac = create_node(ac_data)
if new_ac:
    print(json.dumps(dataclasses.asdict(new_ac), indent=2))

# --- READ Acceptance Criteria ---
print("\n--- Reading all Acceptance Criteria ---")
all_acs = load_todos().get("Acceptance Criteria", [])
for ac in all_acs:
    print(json.dumps(dataclasses.asdict(ac), indent=2))

# --- UPDATE Acceptance Criteria ---
print(f"\n--- Updating Acceptance Criteria: {ac_id} status ---")
ac_node_to_update = next((a for a in all_acs if a.id == ac_id), None)
if ac_node_to_update:
    node_data = {
        "status": "in_progress",
        "links": {"parents": ac_node_to_update.links.parents, "children": ac_node_to_update.links.children},
        "metadata": {"owner": ac_node_to_update.metadata.owner, "labels": ac_node_to_update.metadata.labels, "severity": ac_node_to_update.metadata.severity, "work_type": ac_node_to_update.metadata.work_type}
    }
    updated_ac, error = update_node(ac_id, node_data)
    if updated_ac:
        print(json.dumps(dataclasses.asdict(updated_ac), indent=2))

# --- DELETE Acceptance Criteria ---
print(f"\n--- Deleting Acceptance Criteria: {ac_id} ---")
delete_node(ac_id)
print(f"Acceptance Criteria {ac_id} deleted.")
```

### 7. Interface Contract Layer (APIs, protocols, data formats)

```python
from afs_fastapi.todos.manager import create_node, load_todos, update_node, delete_node
import json

ic_id = "IC-GPS-DATA"
requirement_id_parent = "R-GPS-ACCURACY" # Assuming this requirement exists or is created

# --- CREATE an Interface Contract ---
print("--- Creating a new Interface Contract ---")
ic_data = {
    "id": ic_id,
    "layer": "Interface Contract",
    "title": "GPS Data Exchange Protocol",
    "description": "Define JSON schema for GPS position data exchange between planting robots and base station.",
    "status": "planned",
    "links": {"parents": [requirement_id_parent], "children": []},
    "metadata": {"owner": "dev-team", "labels": ["api", "json"], "severity": "med", "work_type": "spec"}
}
new_ic = create_node(ic_data)
if new_ic:
    print(json.dumps(dataclasses.asdict(new_ic), indent=2))

# --- READ Interface Contracts ---
print("\n--- Reading all Interface Contracts ---")
all_ics = load_todos().get("Interface Contract", [])
for ic in all_ics:
    print(json.dumps(dataclasses.asdict(ic), indent=2))

# --- UPDATE an Interface Contract ---
print(f"\n--- Updating Interface Contract: {ic_id} description ---")
ic_node_to_update = next((i for i in all_ics if i.id == ic_id), None)
if ic_node_to_update:
    node_data = {
        "description": "Define JSON schema for GPS position data exchange (latitude, longitude, altitude, timestamp, accuracy) between planting robots and base station, using MQTT.",
        "links": {"parents": ic_node_to_update.links.parents, "children": ic_node_to_update.links.children},
        "metadata": {"owner": ic_node_to_update.metadata.owner, "labels": ic_node_to_update.metadata.labels, "severity": ic_node_to_update.metadata.severity, "work_type": ic_node_to_update.metadata.work_type}
    }
    updated_ic, error = update_node(ic_id, node_data)
    if updated_ic:
        print(json.dumps(dataclasses.asdict(updated_ic), indent=2))

# --- DELETE an Interface Contract ---
print(f"\n--- Deleting Interface Contract: {ic_id} ---")
delete_node(ic_id)
print(f"Interface Contract {ic_id} deleted.")
```

### 8. Phase Layer (Major delivery milestones)

```python
from afs_fastapi.todos.manager import add_phase, load_todos, update_node, delete_node
import json

phase_id = "PH-GPS-INTEGRATION"
goal_id_parent = "GOAL-AUTONOMOUS-PLANTING" # Assuming this goal exists or is created

# --- CREATE a Phase ---
print("--- Creating a new Phase ---")
new_phase, error = add_phase(
    goal_id=goal_id_parent,
    title="GPS Integration Phase",
    description="Integrate RTK-GPS modules and develop software for accurate positioning."
)
if new_phase:
    print(json.dumps(new_phase, indent=2))
    phase_id = new_phase["id"]
else:
    print(f"Error creating phase: {error}")
    phase_id = "PH-GPS-INTEGRATION" # Fallback for demonstration if creation fails

# --- READ Phases ---
print("\n--- Reading all Phases ---")
all_phases = load_todos().get("Phase", [])
for phase in all_phases:
    print(json.dumps(dataclasses.asdict(phase), indent=2))

# --- UPDATE a Phase ---
print(f"\n--- Updating Phase: {phase_id} status to 'in_progress' ---")
phase_node_to_update = next((p for p in all_phases if p.id == phase_id), None)
if phase_node_to_update:
    node_data = {
        "status": "in_progress",
        "links": {"parents": phase_node_to_update.links.parents, "children": phase_node_to_update.links.children},
        "metadata": {"owner": "dev-team", "labels": ["gps", "integration"], "severity": "high", "work_type": "implementation"}
    }
    updated_phase, error = update_node(phase_id, node_data)
    if updated_phase:
        print(json.dumps(dataclasses.asdict(updated_phase), indent=2))

# --- DELETE a Phase ---
print(f"\n--- Deleting Phase: {phase_id} ---")
delete_node(phase_id)
print(f"Phase {phase_id} deleted.")
```

### 9. Step Layer (Single-concern implementation units)

```python
from afs_fastapi.todos.manager import add_step, load_todos, update_node, delete_node
import json

step_id = "STP-RTK-SETUP"
phase_id_parent = "PH-GPS-INTEGRATION" # Assuming this phase exists or is created

# --- CREATE a Step ---
print("--- Creating a new Step ---")
new_step, error = add_step(
    phase_id=phase_id_parent,
    name="RTK-GPS Module Setup",
    description="Configure and calibrate RTK-GPS modules on planting robots."
)
if new_step:
    print(json.dumps(new_step, indent=2))
    step_id = new_step["id"]
else:
    print(f"Error creating step: {error}")
    step_id = "STP-RTK-SETUP" # Fallback for demonstration if creation fails

# --- READ Steps ---
print("\n--- Reading all Steps ---")
all_steps = load_todos().get("Step", [])
for step in all_steps:
    print(json.dumps(dataclasses.asdict(step), indent=2))

# --- UPDATE a Step ---
print(f"\n--- Updating Step: {step_id} status to 'in_progress' ---")
step_node_to_update = next((s for s in all_steps if s.id == step_id), None)
if step_node_to_update:
    node_data = {
        "status": "in_progress",
        "links": {"parents": step_node_to_update.links.parents, "children": step_node_to_update.links.children},
        "metadata": {"owner": "hardware-team", "labels": ["gps", "hardware"], "severity": "high", "work_type": "implementation"}
    }
    updated_step, error = update_node(step_id, node_data)
    if updated_step:
        print(json.dumps(dataclasses.asdict(updated_step), indent=2))

# --- DELETE a Step ---
print(f"\n--- Deleting Step: {step_id} ---")
delete_node(step_id)
print(f"Step {step_id} deleted.")
```

### 10. Task Layer (Individual contributor work)

```python
from afs_fastapi.todos.manager import add_task, load_todos, update_node, delete_node
import json

task_id = "TSK-GPS-CALIBRATION"
step_id_parent = "STP-RTK-SETUP" # Assuming this step exists or is created

# --- CREATE a Task ---
print("--- Creating a new Task ---")
new_task, error = add_task(
    step_id=step_id_parent,
    title="Perform RTK-GPS Calibration",
    description="Execute field calibration procedure for RTK-GPS modules on all robots."
)
if new_task:
    print(json.dumps(new_task, indent=2))
    task_id = new_task["id"]
else:
    print(f"Error creating task: {error}")
    task_id = "TSK-GPS-CALIBRATION" # Fallback for demonstration if creation fails

# --- READ Tasks ---
print("\n--- Reading all Tasks ---")
all_tasks = load_todos().get("Task", [])
for task in all_tasks:
    print(json.dumps(dataclasses.asdict(task), indent=2))

# --- UPDATE a Task ---
print(f"\n--- Updating Task: {task_id} status to 'in_progress' ---")
task_node_to_update = next((t for t in all_tasks if t.id == task_id), None)
if task_node_to_update:
    node_data = {
        "status": "in_progress",
        "links": {"parents": task_node_to_update.links.parents, "children": task_node_to_update.links.children},
        "metadata": {"owner": "technician-a", "labels": ["calibration", "gps"], "severity": "high", "work_type": "implementation"}
    }
    updated_task, error = update_node(task_id, node_data)
    if updated_task:
        print(json.dumps(dataclasses.asdict(updated_task), indent=2))

# --- DELETE a Task ---
print(f"\n--- Deleting Task: {task_id} ---")
delete_node(task_id)
print(f"Task {task_id} deleted.")
```

### 11. SubTask Layer (Smallest planning granule)

```python
from afs_fastapi.todos.manager import add_subtask, load_todos, update_node, delete_node
import json

subtask_id = "SUB-GPS-TEST-LOG"
task_id_parent = "TSK-GPS-CALIBRATION" # Assuming this task exists or is created

# --- CREATE a SubTask ---
print("--- Creating a new SubTask ---")
new_subtask, error = add_subtask(
    task_id=task_id_parent,
    title="Log GPS Calibration Data",
    description="Record GPS readings during calibration to a CSV file for analysis.",
    command="python log_gps_data.py --output calibration_log.csv",
    command_type="python"
)
if new_subtask:
    print(json.dumps(new_subtask, indent=2))
    subtask_id = new_subtask["id"]
else:
    print(f"Error creating subtask: {error}")
    subtask_id = "SUB-GPS-TEST-LOG" # Fallback for demonstration if creation fails

# --- READ SubTasks ---
print("\n--- Reading all SubTasks ---")
all_subtasks = load_todos().get("SubTask", [])
for subtask in all_subtasks:
    print(json.dumps(dataclasses.asdict(subtask), indent=2))

# --- UPDATE a SubTask ---
print(f"\n--- Updating SubTask: {subtask_id} status to 'done' ---")
subtask_node_to_update = next((s for s in all_subtasks if s.id == subtask_id), None)
if subtask_node_to_update:
    node_data = {
        "status": "done",
        "links": {"parents": subtask_node_to_update.links.parents, "children": subtask_node_to_update.links.children},
        "metadata": {"owner": subtask_node_to_update.metadata.owner, "labels": subtask_node_to_update.metadata.labels, "severity": subtask_node_to_update.metadata.severity, "work_type": subtask_node_to_update.metadata.work_type},
        "command": dataclasses.asdict(subtask_node_to_update.command) if subtask_node_to_update.command else None
    }
    updated_subtask, error = update_node(subtask_id, node_data)
    if updated_subtask:
        print(json.dumps(dataclasses.asdict(updated_subtask), indent=2))

# --- DELETE a SubTask ---
print(f"\n--- Deleting SubTask: {subtask_id} ---")
delete_node(subtask_id)
print(f"SubTask {subtask_id} deleted.")
```

### 12. Command Layer (ONLY executable layer)

```python
from afs_fastapi.todos.manager import create_node, load_todos, update_node, delete_node
import json

command_id = "CMD-GPS-LOG"
subtask_id_parent = "SUB-GPS-TEST-LOG" # Assuming this subtask exists or is created

# --- CREATE a Command ---
print("--- Creating a new Command ---")
# Commands are typically created implicitly via add_subtask or a dedicated tool.
# Here, we demonstrate direct creation for completeness.
command_data = {
    "id": command_id,
    "layer": "Command",
    "title": "Execute GPS Data Logging Script",
    "description": "Runs the Python script to log GPS data.",
    "status": "planned",
    "links": {"parents": [subtask_id_parent], "children": []},
    "metadata": {"owner": "dev-ops", "labels": ["script", "execution"], "severity": "med", "work_type": "ops"},
    "command": {
        "ac_ref": "AC-GPS-001", # Reference to an Acceptance Criteria
        "run": {"command": "python log_gps_data.py --output final_log.csv", "type": "python"},
        "artifacts": ["final_log.csv"]
    }
}
new_command = create_node(command_data)
if new_command:
    print(json.dumps(dataclasses.asdict(new_command), indent=2))

# --- READ Commands ---
print("\n--- Reading all Commands ---")
all_commands = load_todos().get("Command", [])
for cmd in all_commands:
    print(json.dumps(dataclasses.asdict(cmd), indent=2))

# --- UPDATE a Command ---
print(f"\n--- Updating Command: {command_id} command details ---")
cmd_node_to_update = next((c for c in all_commands if c.id == command_id), None)
if cmd_node_to_update:
    node_data = {
        "command": {
            "ac_ref": cmd_node_to_update.command.ac_ref,
            "run": {"command": "python log_gps_data.py --output final_log_v2.csv --verbose", "type": "python"},
            "artifacts": ["final_log_v2.csv", "log_summary.txt"]
        },
        "links": {"parents": cmd_node_to_update.links.parents, "children": cmd_node_to_update.links.children},
        "metadata": {"owner": cmd_node_to_update.metadata.owner, "labels": cmd_node_to_update.metadata.labels, "severity": cmd_node_to_update.metadata.severity, "work_type": cmd_node_to_update.metadata.work_type}
    }
    updated_cmd, error = update_node(command_id, node_data)
    if updated_cmd:
        print(json.dumps(dataclasses.asdict(updated_cmd), indent=2))

# --- DELETE a Command ---
print(f"\n--- Deleting Command: {command_id} ---")
delete_node(command_id)
print(f"Command {command_id} deleted.")
```

---

## ToDoWrite Node JSON Schema

The following JSON Schema defines the structure and validation rules for all nodes within the ToDoWrite system. This schema ensures consistency and adherence to the 12-layer architecture.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ToDoWrite Node",
  "type": "object",
  "required": ["id", "layer", "title", "description", "links"],
  "properties": {
    "id": {"type":"string","pattern":"^(GOAL|CON|CTX|CST|R|AC|IF|PH|STP|TSK|SUB|CMD)-[A-Z0-9_-]+$"},
    "layer": {"type":"string","enum":["Goal","Concept","Context","Constraints","Requirements","AcceptanceCriteria","InterfaceContract","Phase","Step","Task","SubTask","Command"]},
    "title": {"type":"string","minLength":1},
    "description": {"type":"string"},
    "metadata": {
      "type":"object",
      "properties": {
        "owner": {"type":"string"},
        "labels": {"type":"array","items":{"type":"string"}},
        "severity": {"type":"string","enum":["low","med","high"]},
        "work_type": {"type":"string","enum":["architecture","spec","interface","validation","implementation","docs","ops","refactor","chore","test"]}
      },
      "additionalProperties": true
    },
    "links": {
      "type":"object",
      "required":["parents","children"],
      "properties": {
        "parents": {"type":"array","items":{"type":"string"}},
        "children": {"type":"array","items":{"type":"string"}}
      }
    },
    "command": {
      "type":"object",
      "properties": {
        "ac_ref": {"type":"string","pattern":"^AC-[A-Z0-9_-]+$"},
        "run": {
          "type":"object",
          "properties": {
            "shell": {"type":"string"},
            "workdir": {"type":"string"},
            "env": {"type":"object","additionalProperties":{"type":"string"}}
          },
          "required":["shell"]
        },
        "artifacts": {"type":"array","items":{"type":"string"}}
      },
      "required":["ac_ref","run"],
      "additionalProperties": false
    }
  },
  "allOf": [
    {
      "if": {"properties": {"layer": {"const":"Command"}}}
      "then": {"required":["command"]}
    },
    {
      "if": {"properties": {"layer": {"enum":["Goal","Concept","Context","Constraints","Requirements","AcceptanceCriteria","InterfaceContract","Phase","Step","Task","SubTask"]}}}
      "then": {"not": {"required":["command"]}}
    }
  ],
  "additionalProperties": false
}
```

---

## Workflow & Process Diagrams

The ToDoWrite system enforces a strict top-down workflow, ensuring that strategic intent flows through detailed specifications down to executable actions. While visual diagrams are not directly generatable here, the process can be described as follows:

1.  **Strategic Planning (Goal -> Concept -> Context -> Constraints):**
    *   Work begins with defining a high-level **Goal** (e.g., "Implement Autonomous Planting System").
    *   This leads to **Concept** development (e.g., "Modular Robotics Architecture").
    *   The **Context** of operation is established (e.g., "Typical Field Environment").
    *   **Constraints** are identified (e.g., "ISO 11783 Compliance").
    *   *Flow:* Each layer informs and provides a parent for the next, ensuring alignment.

2.  **Specification (Requirements -> Acceptance Criteria -> Interface Contract):**
    *   Based on Constraints and higher-level planning, detailed **Requirements** are formulated (e.g., "GPS Positioning Accuracy within 2cm").
    *   For each Requirement, objective **Acceptance Criteria** are defined (e.g., "GPS Accuracy Test: 95% of points within 2cm").
    *   Technical **Interface Contracts** are specified for inter-component communication (e.g., "GPS Data Exchange Protocol").
    *   *Flow:* Requirements are derived from Constraints, Acceptance Criteria from Requirements, and Interface Contracts from Requirements/Concepts.

3.  **Implementation (Phase -> Step -> Task -> SubTask):**
    *   The work is broken down into major **Phases** (e.g., "GPS Integration Phase").
    *   Each Phase consists of outcome-focused **Steps** (e.g., "RTK-GPS Module Setup").
    *   Steps are composed of individual **Tasks** (e.g., "Perform RTK-GPS Calibration").
    *   Tasks are further granularized into **SubTasks**, the smallest planning unit (e.g., "Log GPS Calibration Data").
    *   *Flow:* A strict parent-child hierarchy is maintained, guiding the breakdown of work.

4.  **Execution (Command):**
    *   The **Command** layer is the only executable layer. Commands are typically associated with **SubTasks** or directly derived from **Acceptance Criteria**.
    *   Commands define the actual scripts or CLI actions to be performed (e.g., `python log_gps_data.py`).
    *   *Flow:* Commands are the leaf nodes of the execution tree, producing verifiable artifacts that confirm the completion of higher-level Acceptance Criteria and Requirements.

**Traceability:**
The `links` attribute in each node ensures full forward and backward traceability. This means you can trace a `Command` back through its `SubTask`, `Task`, `Step`, `Phase`, `Interface Contract`/`Acceptance Criteria`/`Requirement`, `Constraint`, `Context`, `Concept`, and ultimately to its originating `Goal`. This is crucial for safety-critical systems and compliance.

---

## Getting Started

### 1. Check System Status

```bash
# View overall system status
./bin/todo-status

# Check strategic progress
./bin/strategic-status
```

### 2. Initial Project Setup (Using Python Interface)

The recommended way to interact with the ToDoWrite system programmatically is through the `afs_fastapi.todos.manager` module.

```python
# Example: Creating a new Goal, Phase, Step, Task, and SubTask
from afs_fastapi.todos.manager import add_goal, add_phase, add_step, add_task, add_subtask
import json

# Create a Goal
new_goal, error = add_goal(
    title="Implement Autonomous Multi-Tractor Coordination",
    description="Enable 3+ tractors to coordinate field operations autonomously while maintaining ISO 11783 safety compliance"
)
if new_goal:
    goal_id = new_goal["id"]
    print(f"Created Goal: {goal_id}")

    # Create a Phase under the Goal
    new_phase, error = add_phase(
        goal_id=goal_id,
        title="Communication Infrastructure Development",
        description="Establish robust communication channels between tractors and base station."
    )
    if new_phase:
        phase_id = new_phase["id"]
        print(f"Created Phase: {phase_id}")

        # Create a Step under the Phase
        new_step, error = add_step(
            phase_id=phase_id,
            name="CAN Bus Network Setup",
            description="Configure and verify CAN bus communication on all tractors."
        )
        if new_step:
            step_id = new_step["id"]
            print(f"Created Step: {step_id}")

            # Create a Task under the Step
            new_task, error = add_task(
                step_id=step_id,
                title="Install CAN Transceivers",
                description="Physically install and connect CAN transceivers on each tractor."
            )
            if new_task:
                task_id = new_task["id"]
                print(f"Created Task: {task_id}")

                # Create a SubTask under the Task (with an associated Command)
                new_subtask, error = add_subtask(
                    task_id=task_id,
                    title="Verify CAN Bus Wiring",
                    description="Perform continuity and resistance checks on CAN bus wiring.",
                    command="sudo ip link set can0 type can bitrate 250000 && sudo ip link set can0 up",
                    command_type="bash"
                )
                if new_subtask:
                    print(f"Created SubTask with Command: {new_subtask['id']}")
                else:
                    print(f"Error creating SubTask: {error}")
            else:
                print(f"Error creating Task: {error}")
        else:
            print(f"Error creating Step: {error}")
    else:
        print(f"Error creating Phase: {error}")
else:
    print(f"Error creating Goal: {error}")
```

### 3. Verify Your Setup

```bash
# Check that everything is working
./bin/strategic-status  # Should show your goal
./bin/todo-status       # Should show current active items
```

---

## Daily Development Workflow

### 🌅 Morning Standup Routine

```bash
#!/bin/bash
# Save this as ./scripts/morning-standup.sh

echo "🌾 AFS FastAPI Daily Standup Dashboard"
echo "======================================"

echo "📊 Strategic Progress:"
./bin/strategic-status

echo -e "\n🔄 Current Development State:"
./bin/todo-status

echo -e "\n⚡ Ready for Execution:"
./bin/step-status
```

### 🔨 Active Development Session

#### Starting Work on a Specific Task

```bash
# 1. Activate the work hierarchy (if using CLI tools that support activation)
# Note: Direct activation commands like step-activate/task-activate are typically
# handled by higher-level CLI wrappers or by updating node status directly.
# Example: Update a phase/step/task status to 'in_progress' using Python manager.

# 2. Check what needs to be done
./bin/todo-status                 # Overview
./bin/step-status                 # Current step details

# 3. Work on implementation
# (Write code, run tests, execute commands)

# 4. Execute specific commands (Layer 12 only)
# Commands are defined within SubTasks. To execute, retrieve the command from the SubTask
# and run it via your shell.
# Example (Python to get command):
# python -c 'from afs_fastapi.todos.manager import load_todos; import json; subtask_id = "SUB-YOUR-ID"; todos = load_todos(); subtask = next((s for s in todos.get("SubTask", []) if s.id == subtask_id), None); if subtask and subtask.command: print(subtask.command.run["command"])"
# Then manually execute the printed command in your shell.
```

#### Example Development Session: CAN Bus Implementation

```bash
# Scenario: Working on CAN bus configuration for tractor coordination

# 1. Check current status
./bin/todo-status

# 2. Work on current step (e.g., "CAN Bus Network Setup")
# You would have previously created this step and set its status to 'in_progress'

# 3. Add today's tasks
# Example using Python:
# python -c 'from afs_fastapi.todos.manager import add_task; new_task, err = add_task("STP-CAN-BUS-ID", "Configure CAN0 interface on Tractor-001", "Set up the CAN0 interface."); print(new_task["id"] if new_task else err)'

# 4. Add executable commands (as SubTasks)
# Example using Python:
# python -c 'from afs_fastapi.todos.manager import add_subtask; new_subtask, err = add_subtask("TSK-CAN-CONFIG-ID", "Enable CAN module", "sudo modprobe can && sudo modprobe can-raw", command="sudo modprobe can && sudo modprobe can-raw", command_type="bash"); print(new_subtask["id"] if new_subtask else err)'

# 5. Execute the commands (one by one as needed)
# Retrieve command from SubTask and execute manually.
# Example: sudo modprobe can && sudo modprobe can-raw

# 6. Mark completion as you finish
# python -c 'from afs_fastapi.todos.manager import update_node; node_data = {"status": "done", "links": ..., "metadata": ...}; update_node("TSK-CAN-CONFIG-ID", node_data)'
```

### 🔄 Progress Tracking During the Day

```bash
# Quick status check (run anytime)
./bin/todo-status

# Update progress on current work using Python manager functions
# Example: Mark a Task complete
# python -c 'from afs_fastapi.todos.manager import load_todos, update_node; task_id = "TSK-YOUR-ID"; todos = load_todos(); task_node = next((t for t in todos.get("Task", []) if t.id == task_id), None); if task_node: node_data = {"status": "done", "links": {"parents": task_node.links.parents, "children": task_node.links.children}, "metadata": {"owner": task_node.metadata.owner, "labels": task_node.metadata.labels, "severity": task_node.metadata.severity, "work_type": task_node.metadata.work_type}}; updated_node, error = update_node(task_id, node_data); print(updated_node.id if updated_node else error)'
```

### 🌅 End-of-Day Routine

```bash
#!/bin/bash
# Save this as ./scripts/end-of-day.sh

echo "📊 End of Day Development Summary"
echo "=================================="

# 1. Sync todo state
echo "💾 Syncing todo state..."
./bin/todo-sync

# 2. Check overall progress
echo "📈 Strategic Progress:"
./bin/strategic-status

# 3. Save session state
echo "💾 Saving session state..."
./bin/saveandpush "End of day: $(date '+%Y-%m-%d') development progress"

echo "✅ Day complete! All progress saved."
```

---

## Agricultural Robotics Examples

### Example 1: Multi-Tractor Field Coordination Project

#### Strategic Setup

```python
# 1. Create strategic goal
from afs_fastapi.todos.manager import add_goal
import json

new_goal, error = add_goal(
    title="Multi-Tractor Field Coordination System",
    description="Coordinate 5 John Deere tractors for autonomous corn harvesting with real-time position sharing and collision avoidance"
)
if new_goal:
    print(f"Created Goal: {new_goal['id']}")
```

#### Implementation Breakdown

```python
# Example: Creating a Phase, Step, Task, and SubTask for CAN Bus setup
from afs_fastapi.todos.manager import add_phase, add_step, add_task, add_subtask
import json

goal_id_parent = "GOAL-FIELD-COORDINATION" # Assuming this goal exists

# Create Phase
new_phase, error = add_phase(
    goal_id=goal_id_parent,
    title="Communication Infrastructure",
    description="Set up and verify all communication channels."
)
if new_phase:
    phase_id = new_phase["id"]
    print(f"Created Phase: {phase_id}")

    # Create Step
    new_step, error = add_step(
        phase_id=phase_id,
        name="CAN Bus Network Setup",
        description="Configure CAN bus interfaces and network topology."
    )
    if new_step:
        step_id = new_step["id"]
        print(f"Created Step: {step_id}")

        # Create Task
        new_task, error = add_task(
            step_id=step_id,
            title="Install CAN Transceivers on all Tractors",
            description="Physically install and connect CAN transceivers."
        )
        if new_task:
            task_id = new_task["id"]
            print(f"Created Task: {task_id}")

            # Create Executable SubTask
            new_subtask, error = add_subtask(
                task_id=task_id,
                title="Setup CAN interface",
                description="Execute commands to bring up CAN0 interface.",
                command="sudo ip link set can0 type can bitrate 250000 && sudo ip link set can0 up",
                command_type="bash"
            )
            if new_subtask:
                print(f"Created SubTask with Command: {new_subtask['id']}")
```

### Example 2: Safety Compliance Project

#### ISO 11783 Compliance Tracking

```python
# Strategic goal for compliance
from afs_fastapi.todos.manager import add_goal, add_step, add_task, add_subtask
import json

new_goal, error = add_goal(
    title="Achieve ISO 11783 Agricultural Communication Compliance",
    description="Ensure all tractor communication systems meet ISO 11783 standards for agricultural equipment interoperability"
)
if new_goal:
    goal_id = new_goal["id"]
    print(f"Created Goal: {goal_id}")

    # Safety-specific steps and tasks
    new_step, error = add_step(
        phase_id="PH-COMPLIANCE-ID", # Assuming a compliance phase exists
        name="Emergency Stop System Implementation",
        description="Implement and test emergency stop functionality."
    )
    if new_step:
        step_id = new_step["id"]
        print(f"Created Step: {step_id}")

        new_task, error = add_task(
            step_id=step_id,
            title="Implement Stop Signal Propagation via CAN",
            description="Develop software to propagate emergency stop signals over CAN bus."
        )
        if new_task:
            task_id = new_task["id"]
            print(f"Created Task: {task_id}")

            # Safety validation command (as SubTask)
            new_subtask, error = add_subtask(
                task_id=task_id,
                title="Test Emergency Stop Response Time",
                description="Execute automated test to measure emergency stop response time.",
                command="python test_emergency_stop.py --max-response-time 500ms",
                command_type="python"
            )
            if new_subtask:
                print(f"Created SubTask with Command: {new_subtask['id']}")
```

### Example 3: Daily Agricultural Operations

#### Typical Day: Corn Harvesting Coordination

```bash
# Morning: Check system status
./bin/todo-status                    # Overall progress

# Active work: GPS coordination feature
# Example: Add a task and subtask for GPS position sharing
# python -c 'from afs_fastapi.todos.manager import add_task, add_subtask; task_id = "TSK-GPS-SHARE"; step_id = "STP-GPS-COORD"; new_task, err = add_task(step_id, "Implement GPS position sharing between tractors", "Develop and integrate GPS sharing logic."); print(new_task["id"] if new_task else err); new_subtask, err = add_subtask(new_task["id"], "Read GPS from John Deere API", "python read_gps_data.py --tractor JD001", command="python read_gps_data.py --tractor JD001", command_type="python"); print(new_subtask["id"] if new_subtask else err)'

# Testing: Field validation
# Example: Add a task and subtask for field testing
# python -c 'from afs_fastapi.todos.manager import add_task, add_subtask; task_id = "TSK-FIELD-TEST"; step_id = "STP-FIELD-VALIDATION"; new_task, err = add_task(step_id, "Test 3-tractor coordination in south field", "Conduct field tests for coordination."); print(new_task["id"] if new_task else err); new_subtask, err = add_subtask(new_task["id"], "Deploy coordination software", "ansible-playbook deploy-coordination.yml", command="ansible-playbook deploy-coordination.yml", command_type="bash"); print(new_subtask["id"] if new_subtask else err)'

# End of day: Save progress
./bin/saveandpush "GPS coordination feature complete, field testing successful"
```

---

## Advanced Integration Patterns

This section covers advanced usage patterns for integrating the ToDoWrite system with external tools and workflows, building on the CLI and Python API foundations covered earlier.

### CI/CD Pipeline Integration

The ToDoWrite system integrates seamlessly with continuous integration workflows:

```yaml
# .github/workflows/todowrite-validation.yml
name: ToDoWrite Validation
on: [push, pull_request]

jobs:
  validate-hierarchy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Validate ToDoWrite Structure
        run: |
          python -c "
          from afs_fastapi.todos.manager import load_todos, get_goals
          todos = load_todos()
          goals = get_goals()
          print(f'✓ Loaded {len(goals)} strategic goals')

          # Validate all goals have phases
          for goal in goals:
              phases = [p for p in todos.get('Phase', []) if goal['id'] in p.links.parents]
              if not phases:
                  raise ValueError(f'Goal {goal[\"id\"]} has no phases')
          print('✓ All goals have implementation phases')
          "

      - name: Execute Planned Commands
        run: |
          # Find and execute all validation commands
          python -c "
          from afs_fastapi.todos.manager import get_commands
          import subprocess

          commands = get_commands()
          validation_commands = [c for c in commands if 'test' in c['title'].lower()]

          for cmd in validation_commands:
              if cmd['status'] == 'planned':
                  print(f'Executing: {cmd[\"title\"]}')
                  result = subprocess.run(cmd['command']['shell'], shell=True)
                  if result.returncode != 0:
                      raise RuntimeError(f'Command failed: {cmd[\"title\"]}')
          "
```

### Docker Integration

```dockerfile
# Dockerfile.todowrite
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Initialize ToDoWrite database
RUN python -c "from afs_fastapi.todos.manager import init_database; init_database()"

# Expose management interface
EXPOSE 8000
CMD ["python", "-m", "afs_fastapi"]
```

```bash
# Docker Compose for development
# docker-compose.todowrite.yml
version: '3.8'
services:
  todowrite:
    build:
      context: .
      dockerfile: Dockerfile.todowrite
    ports:
      - "8000:8000"
    volumes:
      - ./ToDoWrite:/app/ToDoWrite
      - ./bin:/app/bin
    environment:
      - TODOWRITE_DB_URL=postgresql://user:pass@db:5432/todowrite
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: todowrite
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - todowrite_data:/var/lib/postgresql/data

volumes:
  todowrite_data:
```

### IDE Integration Patterns

#### VS Code Integration

```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "ToDoWrite: System Status",
            "type": "shell",
            "command": "./bin/todo-status",
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "ToDoWrite: Execute Commands",
            "type": "shell",
            "command": "python",
            "args": ["-c", "from afs_fastapi.todos.manager import get_commands; [print(f'./bin/command-execute {c[\"id\"]}') for c in get_commands() if c['status'] == 'planned']"],
            "group": "build"
        },
        {
            "label": "ToDoWrite: Create Phase",
            "type": "shell",
            "command": "./bin/phase-add",
            "args": ["${input:phaseTitle}", "--goal-id", "${input:goalId}"],
            "group": "build"
        }
    ],
    "inputs": [
        {
            "id": "phaseTitle",
            "description": "Phase title",
            "default": "New Development Phase",
            "type": "promptString"
        },
        {
            "id": "goalId",
            "description": "Parent Goal ID",
            "type": "promptString"
        }
    ]
}
```

#### PyCharm/IntelliJ Integration

```python
# todowrite_plugin.py - Custom PyCharm plugin integration
import subprocess
from typing import List, Dict

class ToDoWriteIntegration:
    """PyCharm plugin integration for ToDoWrite system."""

    @staticmethod
    def get_project_structure() -> Dict:
        """Get current project structure for IDE display."""
        result = subprocess.run(
            ["python", "-c", "from afs_fastapi.todos.manager import load_todos; import json; print(json.dumps(load_todos()))"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout) if result.returncode == 0 else {}

    @staticmethod
    def create_task_from_todo(todo_comment: str, file_path: str, line_number: int):
        """Convert TODO comment to ToDoWrite task."""
        # Extract TODO content
        todo_text = todo_comment.replace("# TODO:", "").strip()

        # Create task via CLI
        subprocess.run([
            "./bin/task-add", todo_text,
            "--description", f"From {file_path}:{line_number}"
        ])
```

### Monitoring and Alerting

```python
# monitoring/todowrite_metrics.py
from afs_fastapi.todos.manager import load_todos, get_goals, get_commands
import time
import json

def collect_metrics():
    """Collect ToDoWrite system metrics for monitoring."""
    todos = load_todos()
    goals = get_goals()
    commands = get_commands()

    metrics = {
        "timestamp": time.time(),
        "goals": {
            "total": len(goals),
            "completed": len([g for g in goals if g["status"] == "done"]),
            "in_progress": len([g for g in goals if g["status"] == "in_progress"]),
            "planned": len([g for g in goals if g["status"] == "planned"])
        },
        "commands": {
            "total": len(commands),
            "executed": len([c for c in commands if c["status"] == "done"]),
            "pending": len([c for c in commands if c["status"] == "planned"])
        },
        "hierarchy_health": {
            "orphaned_nodes": count_orphaned_nodes(todos),
            "max_depth": calculate_max_depth(todos),
            "completion_rate": calculate_completion_rate(todos)
        }
    }

    return metrics

def count_orphaned_nodes(todos: dict) -> int:
    """Count nodes without proper parent-child relationships."""
    orphaned = 0
    for layer, nodes in todos.items():
        if layer == "Goal":
            continue  # Goals can be root nodes
        for node in nodes:
            if not node.links.parents:
                orphaned += 1
    return orphaned

def calculate_completion_rate(todos: dict) -> float:
    """Calculate overall project completion rate."""
    total_nodes = sum(len(nodes) for nodes in todos.values())
    completed_nodes = sum(
        len([n for n in nodes if n.status == "done"])
        for nodes in todos.values()
    )
    return completed_nodes / total_nodes if total_nodes > 0 else 0.0

# Prometheus metrics export
def export_prometheus_metrics():
    """Export metrics in Prometheus format."""
    metrics = collect_metrics()

    prometheus_output = f"""
# HELP todowrite_goals_total Total number of goals
# TYPE todowrite_goals_total gauge
todowrite_goals_total {metrics['goals']['total']}

# HELP todowrite_goals_completed Number of completed goals
# TYPE todowrite_goals_completed gauge
todowrite_goals_completed {metrics['goals']['completed']}

# HELP todowrite_commands_pending Number of pending commands
# TYPE todowrite_commands_pending gauge
todowrite_commands_pending {metrics['commands']['pending']}

# HELP todowrite_completion_rate Overall completion rate
# TYPE todowrite_completion_rate gauge
todowrite_completion_rate {metrics['hierarchy_health']['completion_rate']}
"""

    return prometheus_output.strip()
```

### Error Handling and Debugging Patterns

#### Robust Error Handling in Python

```python
from afs_fastapi.todos.manager import add_goal, add_phase, load_todos
import logging
from typing import Optional, Tuple, Dict, Any

# Configure logging for ToDoWrite operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("todowrite")

class ToDoWriteError(Exception):
    """Base exception for ToDoWrite operations."""
    pass

class HierarchyValidationError(ToDoWriteError):
    """Raised when hierarchy validation fails."""
    pass

class NodeCreationError(ToDoWriteError):
    """Raised when node creation fails."""
    pass

def safe_create_goal(title: str, description: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Safely create a goal with comprehensive error handling."""
    try:
        logger.info(f"Creating goal: {title}")

        # Validate inputs
        if not title or not title.strip():
            raise ValueError("Goal title cannot be empty")

        if len(title) > 200:
            raise ValueError("Goal title too long (max 200 characters)")

        # Attempt creation
        goal, error = add_goal(title.strip(), description.strip())

        if error:
            logger.error(f"Goal creation failed: {error}")
            raise NodeCreationError(f"Failed to create goal: {error}")

        if not goal:
            raise NodeCreationError("Goal creation returned None without error")

        logger.info(f"Successfully created goal: {goal['id']}")
        return goal, None

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return None, f"Validation error: {e}"
    except NodeCreationError as e:
        logger.error(f"Creation error: {e}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Unexpected error creating goal: {e}")
        return None, f"Unexpected error: {e}"

def validate_hierarchy_integrity() -> Dict[str, Any]:
    """Validate the integrity of the entire ToDoWrite hierarchy."""
    try:
        todos = load_todos()
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        # Check for orphaned nodes
        for layer_name, nodes in todos.items():
            if layer_name == "Goal":
                continue  # Goals can be root nodes

            for node in nodes:
                if not node.links.parents:
                    validation_results["errors"].append(
                        f"Orphaned {layer_name} node: {node.id} ({node.title})"
                    )
                    validation_results["valid"] = False

        # Check for broken parent-child relationships
        all_node_ids = set()
        for nodes in todos.values():
            all_node_ids.update(node.id for node in nodes)

        for layer_name, nodes in todos.items():
            for node in nodes:
                # Check parent references
                for parent_id in node.links.parents:
                    if parent_id not in all_node_ids:
                        validation_results["errors"].append(
                            f"Broken parent reference: {node.id} -> {parent_id}"
                        )
                        validation_results["valid"] = False

                # Check child references
                for child_id in node.links.children:
                    if child_id not in all_node_ids:
                        validation_results["errors"].append(
                            f"Broken child reference: {node.id} -> {child_id}"
                        )
                        validation_results["valid"] = False

        # Generate statistics
        validation_results["statistics"] = {
            "total_nodes": sum(len(nodes) for nodes in todos.values()),
            "layers_with_data": len([layer for layer, nodes in todos.items() if nodes]),
            "completion_rate": calculate_completion_rate(todos)
        }

        return validation_results

    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation failed: {e}"],
            "warnings": [],
            "statistics": {}
        }

# CLI debugging commands
def debug_node_relationships(node_id: str) -> None:
    """Debug parent-child relationships for a specific node."""
    todos = load_todos()

    # Find the node
    target_node = None
    target_layer = None

    for layer_name, nodes in todos.items():
        for node in nodes:
            if node.id == node_id:
                target_node = node
                target_layer = layer_name
                break
        if target_node:
            break

    if not target_node:
        print(f"❌ Node {node_id} not found")
        return

    print(f"🔍 Debugging Node: {node_id}")
    print(f"   Layer: {target_layer}")
    print(f"   Title: {target_node.title}")
    print(f"   Status: {target_node.status}")
    print()

    # Check parents
    print("👆 Parent Nodes:")
    if not target_node.links.parents:
        print("   (No parents - this is a root node)")
    else:
        for parent_id in target_node.links.parents:
            parent_node = find_node_by_id(parent_id, todos)
            if parent_node:
                print(f"   ✓ {parent_id}: {parent_node.title}")
            else:
                print(f"   ❌ {parent_id}: NOT FOUND (broken reference)")

    print()
    print("👇 Child Nodes:")
    if not target_node.links.children:
        print("   (No children)")
    else:
        for child_id in target_node.links.children:
            child_node = find_node_by_id(child_id, todos)
            if child_node:
                print(f"   ✓ {child_id}: {child_node.title}")
            else:
                print(f"   ❌ {child_id}: NOT FOUND (broken reference)")

def find_node_by_id(node_id: str, todos: dict) -> Optional[Any]:
    """Find a node by ID across all layers."""
    for nodes in todos.values():
        for node in nodes:
            if node.id == node_id:
                return node
    return None
```

#### CLI Debugging Commands

```bash
#!/bin/bash
# bin/todowrite-debug

case "$1" in
    "validate")
        echo "🔍 Validating ToDoWrite hierarchy integrity..."
        python -c "
from todowrite_debug import validate_hierarchy_integrity
import json
result = validate_hierarchy_integrity()
print(json.dumps(result, indent=2))
if not result['valid']:
    exit(1)
"
        ;;

    "node")
        if [ -z "$2" ]; then
            echo "Usage: $0 node <node_id>"
            exit 1
        fi
        echo "🔍 Debugging node: $2"
        python -c "
from todowrite_debug import debug_node_relationships
debug_node_relationships('$2')
"
        ;;

    "orphans")
        echo "🔍 Finding orphaned nodes..."
        python -c "
from afs_fastapi.todos.manager import load_todos
todos = load_todos()
orphans = []
for layer_name, nodes in todos.items():
    if layer_name == 'Goal':
        continue
    for node in nodes:
        if not node.links.parents:
            orphans.append((layer_name, node.id, node.title))

if orphans:
    print('❌ Found orphaned nodes:')
    for layer, node_id, title in orphans:
        print(f'   {layer}: {node_id} - {title}')
else:
    print('✅ No orphaned nodes found')
"
        ;;

    "stats")
        echo "📊 ToDoWrite System Statistics"
        python -c "
from afs_fastapi.todos.manager import load_todos, get_goals, get_commands
todos = load_todos()
goals = get_goals()
commands = get_commands()

print(f'Goals: {len(goals)}')
print(f'Total Nodes: {sum(len(nodes) for nodes in todos.values())}')
print(f'Commands: {len(commands)}')
print(f'Layers with Data: {len([layer for layer, nodes in todos.items() if nodes])}')

# Completion statistics
for layer_name, nodes in todos.items():
    if nodes:
        completed = len([n for n in nodes if n.status == 'done'])
        total = len(nodes)
        print(f'{layer_name}: {completed}/{total} ({completed/total*100:.1f}% complete)')
"
        ;;

    *)
        echo "ToDoWrite Debug Utility"
        echo "Usage: $0 {validate|node|orphans|stats}"
        echo ""
        echo "Commands:"
        echo "  validate     - Validate hierarchy integrity"
        echo "  node <id>    - Debug specific node relationships"
        echo "  orphans      - Find orphaned nodes"
        echo "  stats        - Show system statistics"
        ;;
esac
```

---

## Best Practices

### 🛡️ Safety-First Development for Agricultural Robotics

1.  **Always Start with Safety Constraints:**
    ```bash
    # Define safety requirements before any implementation
    ./bin/constraint-add "Emergency Stop Response" \
      --description "All equipment must respond to emergency stop within 500ms"

    # Link safety constraints to acceptance criteria
    ./bin/acceptance-add "Emergency Stop Test" \
      --description "Verify <500ms response time under all conditions"
    ```

2.  **Establish Traceability from Goals to Commands:**
    ```bash
    # Every executable command should trace back to strategic goals
    ./bin/strategic-status  # Verify goal alignment

    # Use the hierarchy validation
    ./bin/todowrite-debug validate
    ```

3.  **Document Before Implementing (Layers 1-11 Planning):**
    ```bash
    # Complete planning layers before execution
    ./bin/goal-add "Autonomous Harvesting System"
    ./bin/concept-add "Vision-Based Navigation" --goal-id goal-123
    ./bin/requirement-add "GPS Accuracy ±2cm" --constraint-id constraint-456

    # Only Layer 12 executes - keep commands atomic and testable
    ./bin/command-add "Test GPS Accuracy" "python test_gps_precision.py" \
      --description "Validate GPS meets ±2cm requirement"
    ```

### 🔄 CLI and Python API Integration Patterns

1.  **Daily Development Rhythm:**
    ```bash
    # Morning: System overview
    ./bin/loadsession
    ./bin/todo-status
    ./bin/strategic-status

    # Development: Use appropriate interface
    ./bin/task-add "Implement CAN driver"  # CLI for simple operations

    # Complex operations: Use Python API
    python -c "
    from afs_fastapi.todos.manager import create_agricultural_project_template
    template = create_agricultural_project_template('Corn Harvester Fleet')
    print(f'Created project: {template[\"goal_id\"]}')
    "

    # Evening: Save progress
    ./bin/saveandpush 'Daily progress: CAN driver implementation'
    ```

2.  **Choose the Right Interface:**
    ```bash
    # CLI for simple, interactive operations
    ./bin/phase-add "Testing Phase" --goal-id goal-123
    ./bin/command-execute command-456 --auto-complete

    # Python API for complex, programmatic operations
    python -c "
    from afs_fastapi.todos.manager import execute_command_pipeline
    results = execute_command_pipeline(['cmd-1', 'cmd-2', 'cmd-3'])
    print(f'Executed: {len(results[\"executed\"])} commands')
    "
    ```

3.  **Error Handling and Validation:**
    ```bash
    # Regular integrity checks
    ./bin/todowrite-debug validate
    ./bin/todowrite-debug orphans

    # Debug specific issues
    ./bin/todowrite-debug node goal-123

    # Use safe creation patterns in Python
    python -c "
    from todowrite_debug import safe_create_goal
    goal, error = safe_create_goal('New Goal', 'Description')
    if error:
        print(f'Error: {error}')
    else:
        print(f'Created: {goal[\"id\"]}')
    "
    ```

### 🌾 Agricultural Robotics Specific Practices

1.  **Multi-Equipment Coordination:**
    ```bash
    # Create equipment-specific phases
    ./bin/phase-add "Tractor Fleet Coordination" --goal-id goal-agricultural
    ./bin/step-add "Configure Inter-Tractor Communication"
    ./bin/task-add "Install CAN Bus Network"
    ./bin/command-add "Test CAN Throughput" "cansend can0 123#DEADBEEF"
    ```

2.  **Safety-Critical Command Validation:**
    ```bash
    # Always test commands in dry-run mode first
    ./bin/command-execute emergency-stop-test --dry-run

    # Use validation commands before field deployment
    ./bin/command-add "Validate Safety Systems" \
      "python validate_emergency_systems.py --strict" \
      --description "Comprehensive safety system validation"
    ```

3.  **Field Operation Workflows:**
    ```python
    # Python API for complex field operations
    from afs_fastapi.todos.manager import (
        create_agricultural_project_template,
        execute_command_pipeline,
        validate_hierarchy_integrity
    )

    # Create field operation project
    project = create_agricultural_project_template("Corn Field Harvest - Section 7")

    # Validate before field deployment
    validation = validate_hierarchy_integrity()
    if not validation["valid"]:
        raise RuntimeError(f"Validation failed: {validation['errors']}")

    # Execute pre-operation checks
    safety_commands = ["cmd-safety-check", "cmd-gps-validation", "cmd-can-test"]
    results = execute_command_pipeline(safety_commands, stop_on_error=True)

    if results["failed"]:
        raise RuntimeError("Safety checks failed - aborting field operation")
    ```

### 🚀 Performance and Scalability Considerations

1.  **Database Optimization:**
    ```python
    # Use batch operations for large datasets
    from afs_fastapi.todos.manager import create_node

    # Batch create nodes instead of individual calls
    nodes_to_create = [
        {"id": f"task-{i}", "layer": "Task", "title": f"Task {i}", ...}
        for i in range(100)
    ]

    # Use database transactions for consistency
    from afs_fastapi.todos.db.config import create_database_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_database_engine()
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # Batch operations within transaction
        for node_data in nodes_to_create:
            create_node(node_data)
        session.commit()
    ```

2.  **CLI Command Optimization:**
    ```bash
    # Use specific queries instead of loading all data
    ./bin/goal-status --goal-id specific-goal  # Instead of ./bin/goal-status

    # Batch command execution
    ./bin/command-status | grep "planned" | awk '{print $2}' | \
      xargs -I {} ./bin/command-execute {} --auto-complete
    ```

3.  **Memory Management for Large Projects:**
    ```python
    # Stream large datasets instead of loading everything
    def process_large_hierarchy():
        todos = load_todos()

        # Process layer by layer to manage memory
        for layer_name in ["Goal", "Phase", "Step", "Task", "SubTask", "Command"]:
            nodes = todos.get(layer_name, [])
            for node in nodes:
                # Process individual nodes
                yield process_node(node)
                # Allow garbage collection
                del node
    ```

### 🌾 Agricultural Context Integration

1.  **Equipment-Specific Planning:**
    ```bash
    # Consider specific tractor models, GPS systems, etc.
    ./bin/context-add "John Deere 8R Series Fleet" \
      --description "5 tractors with StarFire 6000 GPS, ISO 11783 compatible"

    ./bin/constraint-add "Equipment Compatibility" \
      --description "All systems must work with existing John Deere ISOBUS"
    ```

2.  **Field Condition Awareness:**
    ```bash
    # Factor in weather, terrain, crop conditions
    ./bin/context-add "500-acre Corn Field - Section 7" \
      --description "Rolling terrain, GPS coverage verified, harvest season conditions"
    # Example: "Test coordination in muddy field conditions"
    ```

3.  **Compliance Documentation:**
    ```bash
    # Always link to relevant agricultural standards
    # Example: ISO 11783, ISO 25119, ASABE standards
    ```

### 🔗 Traceability Maintenance

1.  **Parent-Child Relationships:**
    ```bash
    # Every item should have clear parents and children
    # Goals → Concepts → Contexts → Constraints → Requirements → Acceptance Criteria → Interface Contracts → Phases → Steps → Tasks → SubTasks → Commands
    ```

2.  **Acceptance Criteria Links:**
    ```bash
    # Commands must link to acceptance criteria
    # Ensures every execution has a purpose and test
    ```

3.  **Strategic Alignment:**
    ```bash
    # Regular alignment checks
    ./bin/strategic-status  # Are we achieving goals?
    ```

---

## Troubleshooting

This section covers common issues when using both the CLI and Python API interfaces of the ToDoWrite system.

### CLI Command Issues

#### "Command not found" or Permission Denied

```bash
# Ensure commands are executable
chmod +x bin/goal-add bin/phase-add bin/task-add

# Check if command exists
ls -la bin/ | grep goal-add

# Verify Python path in commands
head -1 bin/goal-add  # Should show correct Python shebang
```

#### "No strategic goals found"

```bash
# Check if database is initialized
python -c "from afs_fastapi.todos.manager import get_database_info; print(get_database_info())"

# Create a strategic goal using CLI
./bin/goal-add "Test Goal" --description "Initial test goal"

# Or using Python API
python -c "
from afs_fastapi.todos.manager import add_goal
goal, error = add_goal('Test Goal', 'Initial test goal')
print(f'Created: {goal[\"id\"]}' if goal else f'Error: {error}')
"
```

#### "Database connection errors"

```bash
# Check database status
python -c "
from afs_fastapi.todos.manager import get_database_info
try:
    info = get_database_info()
    print(f'Database OK: {info}')
except Exception as e:
    print(f'Database Error: {e}')
"

# Reinitialize database (WARNING: This will clear all existing data!)
python -c "
from afs_fastapi.todos.manager import init_database
result = init_database()
print(f'Database initialized: {result}')
"
```

#### "Import errors with Python API"

```bash
# Verify Python path and module installation
python -c "import sys; print('\\n'.join(sys.path))"

# Check if module is accessible
python -c "
try:
    from afs_fastapi.todos.manager import load_todos
    print('✓ Module import successful')
except ImportError as e:
    print(f'✗ Import error: {e}')
"

# Add project root to Python path if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### "Commands not executing"

```bash
# Verify command layer structure
./bin/command-status

# Check specific command details
./bin/command-status --command-id command-123

# Test command execution with dry-run
./bin/command-execute command-123 --dry-run

# Debug command execution issues
python -c "
from afs_fastapi.todos.manager import load_todos
todos = load_todos()
commands = todos.get('Command', [])
for cmd in commands:
    if cmd.command and cmd.command.run:
        print(f'{cmd.id}: {cmd.command.run.get(\"shell\", \"No shell command\")}')
    else:
        print(f'{cmd.id}: No executable command defined')
"
```

### Python API Issues

#### "Node creation fails silently"

```python
# Use error handling patterns
from afs_fastapi.todos.manager import add_goal

goal, error = add_goal("Test Goal", "Description")
if error:
    print(f"Creation failed: {error}")
    # Check common issues:
    # 1. Database connection
    # 2. Invalid characters in title/description
    # 3. Database permissions
else:
    print(f"Success: {goal['id']}")
```

#### "Hierarchy validation errors"

```python
# Use the debugging utilities
from todowrite_debug import validate_hierarchy_integrity

validation = validate_hierarchy_integrity()
if not validation["valid"]:
    print("Validation errors:")
    for error in validation["errors"]:
        print(f"  - {error}")

    print("Warnings:")
    for warning in validation["warnings"]:
        print(f"  - {warning}")
```

#### "Performance issues with large datasets"

```python
# Use pagination for large queries
from afs_fastapi.todos.manager import load_todos

def load_todos_paginated(layer_name: str, page_size: int = 100):
    """Load todos in chunks to manage memory."""
    todos = load_todos()
    nodes = todos.get(layer_name, [])

    for i in range(0, len(nodes), page_size):
        yield nodes[i:i + page_size]

# Process in chunks
for chunk in load_todos_paginated("Task", 50):
    # Process chunk
    for task in chunk:
        process_task(task)
```

### Diagnostic Commands and Getting Help

#### System Health Checks

```bash
# Comprehensive system status
./bin/todo-status           # Overall system health
./bin/strategic-status      # Strategic goals progress
./bin/todowrite-commands    # Available commands overview

# Detailed debugging
./bin/todowrite-debug validate    # Hierarchy integrity check
./bin/todowrite-debug stats       # System statistics
./bin/todowrite-debug orphans     # Find orphaned nodes
```

#### Database Diagnostics

```bash
# Check database connectivity
python -c "
from afs_fastapi.todos.manager import get_database_info, load_todos
try:
    db_info = get_database_info()
    print(f'✓ Database: {db_info}')

    todos = load_todos()
    total_nodes = sum(len(nodes) for nodes in todos.values())
    print(f'✓ Loaded {total_nodes} nodes across {len(todos)} layers')
except Exception as e:
    print(f'✗ Database issue: {e}')
"

# Database file verification (SQLite)
ls -la *.db 2>/dev/null || echo "No local database files found"
```

#### Command-Specific Debugging

```bash
# Debug specific layer commands
./bin/goal-status --goal-id goal-123
./bin/phase-status --phase-id phase-456
./bin/task-status --task-id task-789

# Debug node relationships
./bin/todowrite-debug node goal-123

# Test command execution
./bin/command-execute command-456 --dry-run
```

#### Python API Debugging

```python
# Comprehensive system check
def system_health_check():
    """Perform comprehensive ToDoWrite system health check."""
    from afs_fastapi.todos.manager import (
        get_database_info, load_todos, get_goals, get_commands
    )

    try:
        # Database connectivity
        db_info = get_database_info()
        print(f"✓ Database connected: {db_info}")

        # Data loading
        todos = load_todos()
        print(f"✓ Loaded {len(todos)} layers")

        # Layer-specific checks
        goals = get_goals()
        commands = get_commands()

        print(f"✓ Goals: {len(goals)}")
        print(f"✓ Commands: {len(commands)}")

        # Hierarchy validation
        from todowrite_debug import validate_hierarchy_integrity
        validation = validate_hierarchy_integrity()

        if validation["valid"]:
            print("✓ Hierarchy validation passed")
        else:
            print(f"✗ Hierarchy issues: {len(validation['errors'])} errors")
            for error in validation["errors"][:3]:  # Show first 3 errors
                print(f"  - {error}")

        return True

    except Exception as e:
        print(f"✗ System check failed: {e}")
        return False

# Run health check
if __name__ == "__main__":
    system_health_check()
```

#### Common Resolution Steps

1. **Reset and Reinitialize (Nuclear Option)**
   ```bash
   # Backup existing data
   cp todos.db todos.db.backup 2>/dev/null || echo "No database to backup"

   # Reinitialize system
   python -c "
   from afs_fastapi.todos.manager import init_database
   result = init_database()
   print(f'Database reinitialized: {result}')
   "

   # Verify initialization
   ./bin/todo-status
   ```

2. **Permission and Path Issues**
   ```bash
   # Fix command permissions
   find bin/ -name "*.py" -exec chmod +x {} \;
   find bin/ -type f ! -name "*.py" -exec chmod +x {} \;

   # Verify Python path
   python -c "import sys; print('Project root in path:', '$(pwd)' in sys.path)"

   # Add to path if needed
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Development Environment Issues**
   ```bash
   # Check Python version
   python --version  # Should be 3.12+

   # Verify dependencies
   pip list | grep -E "(sqlalchemy|pydantic|fastapi)"

   # Check virtual environment
   which python
   echo $VIRTUAL_ENV
   ```

---

## Conclusion

The ToDoWrite system provides a **comprehensive 12-layer hierarchical task management framework** specifically designed for safety-critical agricultural robotics development. This guide has covered both command-line and programmatic interfaces to give intermediate programmers complete control over their agricultural automation projects.

### Key Capabilities Covered

#### **🖥️ Command-Line Interface (CLI)**
-   ✅ **Complete CRUD operations** across all 12 layers
-   ✅ **100% command coverage** with 46 implemented commands
-   ✅ **Hierarchical workflow support** from strategic goals to executable commands
-   ✅ **Agricultural-specific tooling** for multi-tractor coordination
-   ✅ **Integrated debugging utilities** for system validation

#### **🐍 Python Programming Interface**
-   ✅ **Full programmatic access** via `afs_fastapi.todos.manager` module
-   ✅ **Batch operations and automation** for complex agricultural workflows
-   ✅ **Advanced integration patterns** with CI/CD, Docker, and IDEs
-   ✅ **Error handling and validation** with comprehensive debugging tools
-   ✅ **Performance optimization** for large-scale agricultural operations

#### **🌾 Agricultural Robotics Focus**
-   ✅ **Safety-first development** with structured constraint management
-   ✅ **Equipment-specific planning** for John Deere, Case IH, and other platforms
-   ✅ **ISO 11783 compliance tracking** through acceptance criteria
-   ✅ **Multi-equipment coordination** with CAN bus and GPS integration
-   ✅ **Field operation workflows** with safety validation pipelines

### Integration Flexibility

The ToDoWrite system supports multiple integration approaches:

- **Interactive Development**: Use CLI commands for daily task management
- **Automated Workflows**: Leverage Python API for CI/CD integration
- **Hybrid Approaches**: Combine CLI and Python for optimal productivity
- **External Tool Integration**: Connect with project management and monitoring systems

### Next Steps for Implementation

1. **Start with CLI exploration**: Use `./bin/todowrite-commands` to discover available tools
2. **Create your first agricultural project**: Follow the hierarchical workflow examples
3. **Integrate with your development environment**: Use the IDE integration patterns
4. **Implement monitoring and validation**: Set up the debugging and health check utilities
5. **Scale to production**: Apply the performance optimization and error handling patterns

The ToDoWrite system ensures that every line of code in your agricultural robotics project traces back to strategic business goals while maintaining the safety standards critical for autonomous agricultural equipment operation.

---

## Quick Reference

### Essential CLI Commands

```bash
# System Overview
./bin/todowrite-commands              # All available commands
./bin/todo-status                     # Complete system status
./bin/strategic-status                # Strategic goals overview

# Layer Management (Examples)
./bin/goal-add "Project Title"        # Create strategic goal
./bin/phase-add "Phase Name" --goal-id goal-123
./bin/task-add "Task Name"            # Add to active step
./bin/command-add "Title" "shell_cmd" # Create executable command

# Execution and Validation
./bin/command-execute cmd-123         # Execute command
./bin/todowrite-debug validate        # Validate hierarchy
./bin/loadsession && ./bin/savesession # Session management
```

### Essential Python API

```python
# Core imports
from afs_fastapi.todos.manager import (
    add_goal, add_phase, add_task, add_command,
    get_goals, load_todos, complete_goal,
    validate_hierarchy_integrity
)

# Basic operations
goal, error = add_goal("Title", "Description")
todos = load_todos()
validation = validate_hierarchy_integrity()

# Advanced patterns
from todowrite_debug import safe_create_goal
goal, error = safe_create_goal("Safe Goal Creation", "With error handling")
```

### Layer Hierarchy Quick Reference

```
🎯 Strategic (1-4): Goal → Concept → Context → Constraints
📋 Specification (5-7): Requirements → Acceptance Criteria → Interface Contract
🚀 Implementation (8-11): Phase → Step → Task → SubTask
⚡ Execution (12): Command (ONLY executable layer)
```

**Remember**: Layers 1-11 are planning only. Layer 12 (Command) is the only executable layer.

### Next Steps

1.  **Start Small**: Create your first goal and phase
2.  **Practice Daily**: Use the morning/evening routines
3.  **Build Gradually**: Add complexity as you master the basics
4.  **Stay Agricultural**: Always consider field operations context
5.  **Maintain Traceability**: Keep parent-child links updated

The key insight: **Plan systematically (Layers 1-11), Execute carefully (Layer 12)**.

---

*For technical issues or questions about the ToDoWrite system, refer to the `ToDoWrite.md` specification or check the `bin/` directory for additional commands.*
