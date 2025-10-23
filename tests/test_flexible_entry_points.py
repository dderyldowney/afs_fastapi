"""
Test ToDoWrite Flexible Entry Points and Mandatory Hierarchy Completion.

This test demonstrates two key ToDoWrite system capabilities:
1. FLEXIBLE ENTRY: You can start at any layer in the 12-layer hierarchy
2. MANDATORY COMPLETION: All layers below your starting point MUST be defined

The 12-layer hierarchy:
Goal → Concept → Context → Constraints → Requirements → Acceptance Criteria → 
Interface Contract → Phase → Step → Task → SubTask → Command
"""

from typing import Any

import pytest

from afs_fastapi.todos.manager import (
    add_command,
    add_step,
    add_subtask,
    add_task,
    create_database_engine,
    create_node,
    init_database,
    load_todos,
)


def create_standalone_node(layer: str, title: str, description: str) -> dict[str, Any]:
    """Create a node without requiring a parent - demonstrates flexible entry."""
    import uuid

    node_id = f"{layer.lower()}-{uuid.uuid4().hex[:12]}"
    node_data = {
        "id": node_id,
        "layer": layer,
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

    # Add command structure for Command layer
    if layer == "Command":
        node_data["command"] = {
            "ac_ref": f"AC-{uuid.uuid4().hex[:8].upper()}",
            "run": {"shell": "echo 'flexible entry test'"},
            "artifacts": [],
        }

    node = create_node(node_data)
    return {"id": node.id, "title": node.title, "status": node.status}


class TestFlexibleEntryPoints:
    """Test flexible entry points and mandatory hierarchy completion."""

    @pytest.fixture(autouse=True)
    def clean_database(self):
        """Clean database for each test."""
        from afs_fastapi.todos.db.models import Base

        engine = create_database_engine()
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        init_database()
        yield

    def test_flexible_entry_at_any_layer(self):
        """Demonstrate that you can start at ANY layer in the hierarchy."""

        # Entry Point 1: Start at Command (Layer 12) - Minimal hierarchy
        create_standalone_node("Command", "Emergency System Check", "Quick diagnostic command")

        # Entry Point 2: Start at Task (Layer 10) - Implementation level
        create_standalone_node("Task", "Fix GPS Module", "Repair GPS communication issue")

        # Entry Point 3: Start at Phase (Layer 8) - Project level
        create_standalone_node("Phase", "Hardware Integration", "Install and configure sensors")

        # Entry Point 4: Start at Goal (Layer 1) - Strategic level
        create_standalone_node(
            "Goal", "Autonomous Harvesting", "Develop autonomous harvesting system"
        )

        # Verify all entry points exist independently
        todos = load_todos()
        assert len(todos.get("Command", [])) == 1
        assert len(todos.get("Task", [])) == 1
        assert len(todos.get("Phase", [])) == 1
        assert len(todos.get("Goal", [])) == 1

        # Verify they are all root nodes (no parents)
        command_node = todos["Command"][0]
        task_node = todos["Task"][0]
        phase_node = todos["Phase"][0]
        goal_node = todos["Goal"][0]

        assert command_node.links.parents == []
        assert task_node.links.parents == []
        assert phase_node.links.parents == []
        assert goal_node.links.parents == []

        print("✅ FLEXIBLE ENTRY DEMONSTRATED: Started at 4 different layers independently")

    def test_mandatory_hierarchy_completion_from_task(self):
        """Demonstrate that starting at Task REQUIRES completing SubTask and Command layers."""

        # Start at Task (Layer 10)
        task = create_standalone_node(
            "Task", "Implement CAN Driver", "Develop CAN bus communication driver"
        )
        task_id = task["id"]

        # INCOMPLETE: Task exists but no SubTask or Command
        todos = load_todos()
        assert len(todos.get("Task", [])) == 1
        assert len(todos.get("SubTask", [])) == 0  # MISSING - violates completion requirement
        assert len(todos.get("Command", [])) == 0  # MISSING - violates completion requirement

        print("❌ INCOMPLETE HIERARCHY: Task exists without required SubTask and Command")

        # COMPLETE THE HIERARCHY: Add required layers below Task

        # Layer 11: SubTask (required below Task)
        subtask, error = add_subtask(
            task_id, "Write CAN Message Parser", "Parse incoming CAN messages"
        )
        assert error is None
        subtask_id = subtask["id"]

        # Layer 12: Command (required below SubTask)
        command, error = add_command(
            "Run CAN Tests",
            "Execute CAN driver test suite",
            "pytest tests/can_driver/ -v",
            subtask_id,
            "AC-CAN-DRIVER",
        )
        assert error is None

        # VERIFY COMPLETE HIERARCHY
        todos = load_todos()
        assert len(todos.get("Task", [])) == 1
        assert len(todos.get("SubTask", [])) == 1  # ✅ NOW PRESENT
        assert len(todos.get("Command", [])) == 1  # ✅ NOW PRESENT

        # Verify parent-child relationships
        task_node = todos["Task"][0]
        subtask_node = todos["SubTask"][0]
        command_node = todos["Command"][0]

        # Task is root (no parents)
        assert task_node.links.parents == []

        # SubTask has Task as parent
        assert task_id in subtask_node.links.parents

        # Command has SubTask as parent
        assert subtask_id in command_node.links.parents

        print("✅ MANDATORY COMPLETION DEMONSTRATED: Task → SubTask → Command hierarchy complete")

    def test_mandatory_hierarchy_completion_from_phase(self):
        """Demonstrate that starting at Phase REQUIRES completing Step, Task, SubTask, Command."""

        # Start at Phase (Layer 8)
        phase = create_standalone_node(
            "Phase", "GPS Integration Phase", "Install RTK-GPS modules on tractors"
        )
        phase_id = phase["id"]

        # INCOMPLETE: Only Phase exists
        todos = load_todos()
        assert len(todos.get("Phase", [])) == 1
        assert len(todos.get("Step", [])) == 0  # MISSING
        assert len(todos.get("Task", [])) == 0  # MISSING
        assert len(todos.get("SubTask", [])) == 0  # MISSING
        assert len(todos.get("Command", [])) == 0  # MISSING

        print("❌ INCOMPLETE HIERARCHY: Phase exists without required Step→Task→SubTask→Command")

        # COMPLETE THE MANDATORY HIERARCHY BELOW PHASE

        # Layer 9: Step (required below Phase)
        step, error = add_step(
            phase_id, "GPS Module Installation", "Mount and configure GPS hardware"
        )
        assert error is None
        step_id = step["id"]

        # Layer 10: Task (required below Step)
        task, error = add_task(step_id, "Mount GPS Antenna", "Physical installation of GPS antenna")
        assert error is None
        task_id = task["id"]

        # Layer 11: SubTask (required below Task)
        subtask, error = add_subtask(
            task_id, "Test GPS Signal Strength", "Validate GPS reception quality"
        )
        assert error is None
        subtask_id = subtask["id"]

        # Layer 12: Command (required below SubTask)
        command, error = add_command(
            "Test GPS Accuracy",
            "Validate GPS precision meets requirements",
            "python test_gps_accuracy.py --threshold 2cm",
            subtask_id,
            "AC-GPS-PRECISION",
        )
        assert error is None

        # VERIFY COMPLETE HIERARCHY FROM PHASE DOWN
        todos = load_todos()
        assert len(todos.get("Phase", [])) == 1
        assert len(todos.get("Step", [])) == 1  # ✅ NOW PRESENT
        assert len(todos.get("Task", [])) == 1  # ✅ NOW PRESENT
        assert len(todos.get("SubTask", [])) == 1  # ✅ NOW PRESENT
        assert len(todos.get("Command", [])) == 1  # ✅ NOW PRESENT

        # Verify complete parent-child chain
        phase_node = todos["Phase"][0]
        step_node = todos["Step"][0]
        task_node = todos["Task"][0]
        subtask_node = todos["SubTask"][0]
        command_node = todos["Command"][0]

        # Verify hierarchy chain: Phase → Step → Task → SubTask → Command
        assert phase_node.links.parents == []  # Phase is root
        assert phase_id in step_node.links.parents
        assert step_id in task_node.links.parents
        assert task_id in subtask_node.links.parents
        assert subtask_id in command_node.links.parents

        print("✅ MANDATORY COMPLETION DEMONSTRATED: Phase→Step→Task→SubTask→Command complete")

    def test_agricultural_emergency_scenario(self):
        """Real-world agricultural scenario: Emergency repair starting at Task level."""

        # SCENARIO: Tractor #3 CAN bus failure during harvest - no time for full planning
        # Start directly at Task level (emergency implementation)

        emergency_task = create_standalone_node(
            "Task", "Emergency CAN Bus Repair", "Restore communication to Tractor #3"
        )
        task_id = emergency_task["id"]

        # MUST complete hierarchy below Task for execution
        diagnostic_subtask, error = add_subtask(
            task_id, "Diagnose CAN Failure", "Identify root cause of communication loss"
        )
        assert error is None
        diag_subtask_id = diagnostic_subtask["id"]

        repair_subtask, error = add_subtask(
            task_id, "Replace CAN Transceiver", "Install new CAN hardware"
        )
        assert error is None
        repair_subtask_id = repair_subtask["id"]

        # Commands for execution (Layer 12 - only executable layer)
        diag_command, error = add_command(
            "CAN Bus Diagnostic",
            "Run diagnostic on CAN network",
            "candump can0 -n 100 | grep ERROR",
            diag_subtask_id,
            "AC-CAN-DIAG",
        )
        assert error is None

        repair_command, error = add_command(
            "Install New Transceiver",
            "Physical hardware replacement",
            "systemctl stop can-service && ./install_transceiver.sh",
            repair_subtask_id,
            "AC-CAN-REPAIR",
        )
        assert error is None

        # Verify emergency workflow hierarchy is complete
        todos = load_todos()
        assert len(todos.get("Task", [])) == 1  # Emergency task
        assert len(todos.get("SubTask", [])) == 2  # Diagnostic + Repair
        assert len(todos.get("Command", [])) == 2  # Executable commands

        # Verify no higher-level planning layers (emergency scenario)
        assert len(todos.get("Goal", [])) == 0  # No strategic planning
        assert len(todos.get("Phase", [])) == 0  # No project planning
        assert len(todos.get("Step", [])) == 0  # No step planning

        print(
            "✅ AGRICULTURAL EMERGENCY: Task→SubTask→Command hierarchy enables immediate execution"
        )
        print("✅ FLEXIBLE ENTRY: Started at Task level without requiring Goal/Phase/Step")
        print("✅ MANDATORY COMPLETION: All layers below Task (SubTask, Command) are present")
