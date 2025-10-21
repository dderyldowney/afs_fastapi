# ToDoWrite System: Complete User Guide

> **A practical guide to using the 12-layer hierarchical task management system for agricultural robotics development**

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Understanding the 12-Layer Hierarchy](#understanding-the-12-layer-hierarchy)
3. [Core Concepts & Data Structures](#core-concepts--data-structures)
4. [Detailed Layer Management (CRUD Operations)](#detailed-layer-management-crud-operations)
5. [ToDoWrite Node JSON Schema](#todowrite-node-json-schema)
6. [Workflow & Process Diagrams](#workflow--process-diagrams)
7. [Getting Started](#getting-started)
8. [Daily Development Workflow](#daily-development-workflow)
9. [Agricultural Robotics Examples](#agricultural-robotics-examples)
10. [Command Reference (CLI Tools)](#command-reference-cli-tools)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

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

## Command Reference (CLI Tools)

This section outlines the primary CLI tools available in the `./bin/` directory for interacting with the ToDoWrite system. These tools often wrap the underlying Python manager functions for convenient shell usage.

### Core System Status

| Command | Purpose | Example |
|---------|---------|---------|
| `./bin/todo-status` | Provides a complete overview of the ToDoWrite system status, including strategic objectives, active phases, and pending tasks. | `$./bin/todo-status` |
| `./bin/strategic-status` | Displays the progress and details of all strategic goals. | `$./bin/strategic-status` |

### Workflow Management (via Python Manager)

While specific CLI commands for every CRUD operation on every layer might not be directly exposed as `./bin/` scripts, the underlying `afs_fastapi.todos.manager` module provides the full programmatic interface. You can execute these functions directly via Python one-liners or scripts.

**Example: Listing all Goals (Python Manager via CLI)**
```bash
python -c 'from afs_fastapi.todos.manager import get_goals; import json; print(json.dumps(get_goals(), indent=2))'
```

**Example: Updating a Node's Status (Python Manager via CLI)**
```bash
# Assuming you have the node_id, its parents, children, and metadata
python -c 'from afs_fastapi.todos.manager import update_node; import json; node_id = "GOAL-YOUR-ID"; node_data = {"status": "done", "links": {"parents": [], "children": []}, "metadata": {"owner": "your-team", "labels": [], "severity": "med", "work_type": ""}}; updated_node, error = update_node(node_id, node_data); print(json.dumps({"result": updated_node.id if updated_node else None, "error": error}))'
```

---

## Best Practices

### 🛡️ Safety-First Development

1.  **Always Start with Safety Constraints:**
    ```bash
    # Before any implementation, define safety requirements
    # Example: Emergency stop response time < 500ms
    ```

2.  **Link Everything to Strategic Goals:**
    ```bash
    # Every task should trace back to a business goal
    # Use ./bin/strategic-status to verify alignment
    ```

3.  **Document Before Implementing:**
    ```bash
    # Layers 1-11 are planning - document thoroughly
    # Only Layer 12 executes - keep commands simple and testable
    ```

### 🔄 Workflow Optimization

1.  **Daily Rhythm:**
    ```bash
    # Morning: ./bin/todo-status (what needs doing?)
    # Midday: ./bin/todo-status (progress check)
    # Evening: ./bin/saveandpush (save progress)
    ```

2.  **Granular Progress Tracking:**
    ```bash
    # Mark completion immediately when finished
    # Example: python -c 'from afs_fastapi.todos.manager import update_node; ...'

    # Don't batch completions - update in real-time
    ```

3.  **Clear Naming Conventions:**
    ```bash
    # Use descriptive names
    # Good: "Configure CAN bus for ISO 11783 compliance"
    # Bad: "Fix CAN stuff"
    ```

### 🌾 Agricultural Context Integration

1.  **Equipment-Specific Planning:**
    ```bash
    # Consider specific tractor models, GPS systems, etc.
    # Example: "Configure for John Deere 8R series with StarFire 6000"
    ```

2.  **Field Condition Awareness:**
    ```bash
    # Factor in weather, terrain, crop conditions
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

### Common Issues

#### "No strategic goals found"

```bash
# Solution: Create a strategic goal first using the Python manager
python -c 'from afs_fastapi.todos.manager import add_goal; new_goal, err = add_goal(title="My First Goal", description="A test goal."); print(new_goal["id"] if new_goal else err)'
```

#### "Database errors"

```bash
# Solution: Reinitialize database (WARNING: This will clear all existing data!)
python -c "from afs_fastapi.todos.manager import init_database; print(init_database())"
```

#### "Commands not executing"

```bash
# Remember: Only Layer 12 (Commands) execute.
# Layers 1-11 are documentation only.
# Commands are stored in subtasks - retrieve and execute them manually as needed.
```

### Getting Help

1.  **Check System Status**
    ```bash
    ./bin/todo-status      # Overall health check
    ./bin/strategic-status # Strategic progress
    ```

2.  **Verify Database**
    ```bash
    ls -la todos.db        # Database file exists?
    ```

3.  **Review Recent Activity**
    ```bash
    git log --oneline -5   # Recent changes
    ```

---

## Conclusion

The ToDoWrite system provides a **systematic approach to agricultural robotics development** that ensures:

-   ✅ **Safety compliance** through structured requirements
-   ✅ **Strategic alignment** from goals to execution
-   ✅ **Full traceability** for agricultural standards
-   ✅ **Systematic progress** through clear workflows
-   ✅ **Quality assurance** with separation of planning and execution

### Next Steps

1.  **Start Small**: Create your first goal and phase
2.  **Practice Daily**: Use the morning/evening routines
3.  **Build Gradually**: Add complexity as you master the basics
4.  **Stay Agricultural**: Always consider field operations context
5.  **Maintain Traceability**: Keep parent-child links updated

The key insight: **Plan systematically (Layers 1-11), Execute carefully (Layer 12)**.

---

*For technical issues or questions about the ToDoWrite system, refer to the `ToDoWrite.md` specification or check the `bin/` directory for additional commands.*
