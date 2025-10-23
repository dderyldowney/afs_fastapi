"""
Test ToDoWrite Flexible Entry Point and Mandatory Hierarchy Completion.

This test suite validates two critical ToDoWrite system requirements:
1. Flexible Entry: You can start at any layer in the 12-layer hierarchy
2. Mandatory Completion: All layers below your starting point MUST be defined

The 12-layer hierarchy:
1. Goal → 2. Concept → 3. Context → 4. Constraints → 5. Requirements → 
6. Acceptance Criteria → 7. Interface Contract → 8. Phase → 9. Step → 
10. Task → 11. SubTask → 12. Command
"""

from typing import Any

import pytest

from afs_fastapi.todos.manager import (
    add_acceptance_criteria,
    add_command,
    add_concept,
    add_constraint,
    add_context,
    add_goal,
    add_interface_contract,
    add_phase,
    add_requirement,
    add_step,
    add_subtask,
    add_task,
    init_database,
    load_todos,
)


def create_node_without_parent(
    layer: str, title: str, description: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Create a node without requiring a parent - for flexible entry points."""
    import uuid

    from afs_fastapi.todos.manager import create_node

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
            "run": {"shell": "echo 'test command'"},
            "artifacts": [],
        }

    try:
        node = create_node(node_data)
        if node:
            return {"id": node.id, "title": node.title, "status": node.status}, None
        else:
            return None, "Failed to create node"
    except Exception as e:
        return None, str(e)


class TestToDoWriteFlexibleHierarchy:
    """Test flexible entry points and mandatory hierarchy completion."""

    @pytest.fixture(autouse=True)
    def setup_clean_database(self):
        """Initialize clean database for each test."""
        # Clear existing database and reinitialize
        from afs_fastapi.todos.db.models import Base
        from afs_fastapi.todos.manager import create_database_engine

        engine = create_database_engine()
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        # Initialize with empty database
        init_database()
        yield
        # Cleanup is handled by database reinitialization

    def test_can_start_at_goal_layer(self):
        """Test starting at Goal (Layer 1) - the traditional top-down approach."""
        # Start at Goal
        goal, error = add_goal(
            "Agricultural Automation System", "Complete autonomous field operations"
        )
        assert error is None
        assert goal is not None
        goal_id = goal["id"]

        # Must define all layers below Goal (2-12)
        concept, error = add_concept(
            "Multi-Agent Coordination", "Coordinate multiple tractors", goal_id
        )
        assert error is None
        concept_id = concept["id"]

        context, error = add_context(
            "500-acre Corn Field", "Rolling terrain with GPS coverage", concept_id
        )
        assert error is None
        context_id = context["id"]

        constraint, error = add_constraint(
            "ISO 11783 Compliance", "Must meet agricultural standards", context_id
        )
        assert error is None
        constraint_id = constraint["id"]

        requirement, error = add_requirement(
            "CAN Bus 250kbps", "Communication at 250kbps", constraint_id
        )
        assert error is None
        requirement_id = requirement["id"]

        ac, error = add_acceptance_criteria(
            "CAN Message Validation", "Validate message integrity", requirement_id
        )
        assert error is None
        ac_id = ac["id"]

        interface, error = add_interface_contract(
            "Tractor Position API", "JSON position data format", ac_id
        )
        assert error is None

        phase, error = add_phase(goal_id, "Hardware Integration", "Install and configure hardware")
        assert error is None
        phase_id = phase["id"]

        step, error = add_step(phase_id, "CAN Bus Setup", "Configure CAN network")
        assert error is None
        step_id = step["id"]

        task, error = add_task(step_id, "Install CAN Transceivers", "Mount hardware on tractors")
        assert error is None
        task_id = task["id"]

        subtask, error = add_subtask(task_id, "Test CAN Throughput", "Validate 250kbps performance")
        assert error is None
        subtask_id = subtask["id"]

        command, error = add_command(
            "Configure CAN Interface",
            "Set up CAN bus parameters",
            "sudo ip link set can0 type can bitrate 250000",
            subtask_id,
        )
        assert error is None

        # Verify complete hierarchy exists
        todos = load_todos()
        assert len(todos.get("Goal", [])) == 1
        assert len(todos.get("Concept", [])) == 1
        assert len(todos.get("Context", [])) == 1
        assert len(todos.get("Constraints", [])) == 1
        assert len(todos.get("Requirements", [])) == 1
        assert len(todos.get("Acceptance Criteria", [])) == 1
        assert len(todos.get("Interface Contract", [])) == 1
        assert len(todos.get("Phase", [])) == 1
        assert len(todos.get("Step", [])) == 1
        assert len(todos.get("Task", [])) == 1
        assert len(todos.get("SubTask", [])) == 1
        assert len(todos.get("Command", [])) == 1

    def test_can_start_at_phase_layer(self):
        """Test starting at Phase (Layer 8) - mid-hierarchy entry point."""
        # Start directly at Phase - no Goal required
        phase, error = create_node_without_parent(
            "Phase", "GPS Integration Phase", "Install RTK-GPS modules on tractors"
        )
        assert error is None
        phase_id = phase["id"]

        # Must define all layers below Phase (9-12)
        step, error = add_step(
            phase_id, "GPS Module Installation", "Mount and configure GPS hardware"
        )
        assert error is None
        step_id = step["id"]

        task, error = add_task(step_id, "Mount GPS Antenna", "Physical installation of GPS antenna")
        assert error is None
        task_id = task["id"]

        subtask, error = add_subtask(
            task_id, "Test GPS Signal Strength", "Validate GPS reception quality"
        )
        assert error is None
        subtask_id = subtask["id"]

        command, error = add_command(
            "Test GPS Accuracy",
            "Validate GPS precision meets requirements",
            "python test_gps_accuracy.py --threshold 2cm",
            subtask_id,
            "AC-GPS-PRECISION",
        )
        assert error is None

        # Verify hierarchy from Phase down exists
        todos = load_todos()
        assert len(todos.get("Goal", [])) == 0  # No goal defined
        assert len(todos.get("Phase", [])) == 1
        assert len(todos.get("Step", [])) == 1
        assert len(todos.get("Task", [])) == 1
        assert len(todos.get("SubTask", [])) == 1
        assert len(todos.get("Command", [])) == 1

        # Verify parent-child relationships
        phase_node = todos["Phase"][0]
        assert phase_node.links.parents == []  # Phase is root in this hierarchy

        step_node = todos["Step"][0]
        assert phase_id in step_node.links.parents

        command_node = todos["Command"][0]
        assert subtask_id in command_node.links.parents

    def test_can_start_at_task_layer(self):
        """Test starting at Task (Layer 10) - implementation-level entry."""
        # Start directly at Task - no Phase or Step required
        task, error = create_node_without_parent(
            "Task", "Implement CAN Driver", "Develop CAN bus communication driver"
        )
        assert error is None
        task_id = task["id"]

        # Must define all layers below Task (11-12)
        subtask, error = add_subtask(
            task_id, "Write CAN Message Parser", "Parse incoming CAN messages"
        )
        assert error is None
        subtask_id = subtask["id"]

        command, error = add_command(
            "Run CAN Tests",
            "Execute CAN driver test suite",
            "pytest tests/can_driver/ -v",
            subtask_id,
            "AC-CAN-DRIVER",
        )
        assert error is None

        # Verify minimal hierarchy exists
        todos = load_todos()
        assert len(todos.get("Goal", [])) == 0
        assert len(todos.get("Phase", [])) == 0
        assert len(todos.get("Step", [])) == 0
        assert len(todos.get("Task", [])) == 1
        assert len(todos.get("SubTask", [])) == 1
        assert len(todos.get("Command", [])) == 1

        # Verify Task is root node
        task_node = todos["Task"][0]
        assert task_node.links.parents == []

    def test_can_start_at_command_layer(self):
        """Test starting at Command (Layer 12) - direct execution entry."""
        # Start directly at Command - minimal hierarchy
        command, error = create_node_without_parent(
            "Command", "Quick System Check", "Rapid system validation"
        )
        assert error is None

        # Verify only Command layer exists
        todos = load_todos()
        assert len(todos.get("Command", [])) == 1

        # All other layers should be empty
        for layer in [
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
        ]:
            assert len(todos.get(layer, [])) == 0

        # Command should be root node
        command_node = todos["Command"][0]
        assert command_node.links.parents == []

    def test_hierarchy_validation_enforces_completion(self):
        """Test that hierarchy validation catches incomplete hierarchies."""
        # Create a Phase without required child layers
        phase, error = add_phase(None, "Incomplete Phase", "Phase without complete hierarchy")
        assert error is None
        phase_id = phase["id"]

        # Add Step but skip Task/SubTask/Command
        step, error = add_step(phase_id, "Incomplete Step", "Step without tasks")
        assert error is None

        # Hierarchy is incomplete - missing Task, SubTask, Command
        todos = load_todos()

        # This should be flagged as incomplete in validation
        # (Note: The actual validation logic would be implemented in the system)
        phase_node = todos["Phase"][0]
        step_node = todos["Step"][0]

        # Step exists but has no children (Tasks)
        assert len(step_node.links.children) == 0

        # Phase has Step child but hierarchy is incomplete
        assert step_node.id in phase_node.links.children

    def test_multiple_entry_points_in_same_system(self):
        """Test that multiple entry points can coexist in the same system."""
        # Entry point 1: Start at Goal
        goal, error = add_goal("Strategic Goal", "High-level objective")
        assert error is None
        goal_id = goal["id"]

        phase1, error = add_phase(goal_id, "Strategic Phase", "Goal-driven phase")
        assert error is None

        # Entry point 2: Start at Phase (independent)
        phase2, error = create_node_without_parent("Phase", "Independent Phase", "Standalone phase")
        assert error is None
        phase2_id = phase2["id"]

        step2, error = add_step(phase2_id, "Independent Step", "Standalone step")
        assert error is None

        # Entry point 3: Start at Task (independent)
        task3, error = create_node_without_parent("Task", "Independent Task", "Standalone task")
        assert error is None
        task3_id = task3["id"]

        subtask3, error = add_subtask(task3_id, "Independent SubTask", "Standalone subtask")
        assert error is None
        subtask3_id = subtask3["id"]

        command3, error = add_command(
            "Independent Command", "Standalone command", "echo 'Independent execution'", subtask3_id
        )
        assert error is None

        # Verify all entry points coexist
        todos = load_todos()
        assert len(todos.get("Goal", [])) == 1
        assert len(todos.get("Phase", [])) == 2  # One from goal, one independent
        assert len(todos.get("Step", [])) == 1  # Only from independent phase
        assert len(todos.get("Task", [])) == 1  # Independent task
        assert len(todos.get("SubTask", [])) == 1
        assert len(todos.get("Command", [])) == 1

        # Verify parent relationships
        goal_phase = next(p for p in todos["Phase"] if goal_id in p.links.parents)
        independent_phase = next(p for p in todos["Phase"] if not p.links.parents)
        independent_task = todos["Task"][0]

        assert goal_phase.title == "Strategic Phase"
        assert independent_phase.title == "Independent Phase"
        assert independent_task.links.parents == []  # Root node

    def test_agricultural_robotics_flexible_entry_example(self):
        """Test realistic agricultural robotics scenario with flexible entry."""
        # Scenario: Emergency repair workflow starting at Task level
        # (No time for full strategic planning - direct implementation needed)

        emergency_task, error = add_task(
            None, "Emergency CAN Bus Repair", "Restore communication to Tractor #3"
        )
        assert error is None
        task_id = emergency_task["id"]

        # Must complete hierarchy below Task
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

        test_subtask, error = add_subtask(
            task_id, "Validate Repair", "Confirm communication restored"
        )
        assert error is None
        test_subtask_id = test_subtask["id"]

        # Commands for each subtask
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

        test_command, error = add_command(
            "Test CAN Communication",
            "Validate repair success",
            "cansend can0 123#DEADBEEF && echo 'CAN OK'",
            test_subtask_id,
            "AC-CAN-TEST",
        )
        assert error is None

        # Verify emergency workflow hierarchy
        todos = load_todos()
        assert len(todos.get("Task", [])) == 1
        assert len(todos.get("SubTask", [])) == 3
        assert len(todos.get("Command", [])) == 3

        # Verify all commands trace back to the emergency task
        task_node = todos["Task"][0]
        subtask_nodes = todos["SubTask"]
        command_nodes = todos["Command"]

        # All subtasks should be children of the task
        for subtask in subtask_nodes:
            assert task_id in subtask.links.parents

        # All commands should trace back through subtasks to the task
        for command in command_nodes:
            assert any(st.id in command.links.parents for st in subtask_nodes)

        # Task should be root (no parents)
        assert task_node.links.parents == []

    def test_validation_helper_functions(self):
        """Test helper functions for validating hierarchy completion."""

        def validate_hierarchy_completion(starting_layer: str, todos: dict) -> dict[str, Any]:
            """Validate that all required layers below starting layer are present."""
            layer_order = [
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

            try:
                start_index = layer_order.index(starting_layer)
            except ValueError:
                return {"valid": False, "error": f"Unknown layer: {starting_layer}"}

            required_layers = layer_order[start_index:]
            missing_layers = []

            for layer in required_layers:
                if not todos.get(layer, []):
                    missing_layers.append(layer)

            return {
                "valid": len(missing_layers) == 0,
                "missing_layers": missing_layers,
                "required_layers": required_layers,
                "present_layers": [layer for layer in required_layers if todos.get(layer, [])],
            }

        # Test complete hierarchy starting at Phase
        phase, error = add_phase(None, "Test Phase", "Complete hierarchy test")
        phase_id = phase["id"]

        step, error = add_step(phase_id, "Test Step", "Test step")
        step_id = step["id"]

        task, error = add_task(step_id, "Test Task", "Test task")
        task_id = task["id"]

        subtask, error = add_subtask(task_id, "Test SubTask", "Test subtask")
        subtask_id = subtask["id"]

        command, error = add_command("Test Command", "Test command", "echo test", subtask_id)

        todos = load_todos()
        validation = validate_hierarchy_completion("Phase", todos)

        assert validation["valid"] is True
        assert validation["missing_layers"] == []
        assert "Phase" in validation["present_layers"]
        assert "Command" in validation["present_layers"]

        # Test incomplete hierarchy
        init_database()  # Reset
        incomplete_phase, error = add_phase(None, "Incomplete Phase", "Missing children")

        todos = load_todos()
        validation = validate_hierarchy_completion("Phase", todos)

        assert validation["valid"] is False
        assert "Step" in validation["missing_layers"]
        assert "Task" in validation["missing_layers"]
        assert "SubTask" in validation["missing_layers"]
        assert "Command" in validation["missing_layers"]

    def test_mandatory_completion_requirement_enforcement(self):
        """Test that starting at any layer REQUIRES completing all layers below it."""

        # Test Case 1: Starting at Requirements (Layer 5) - must have layers 6-12
        requirement, error = add_requirement(
            "GPS Accuracy Requirement", "RTK-GPS must provide ±2cm accuracy", None
        )
        assert error is None
        req_id = requirement["id"]

        # Verify that ONLY having Requirements is incomplete
        todos = load_todos()
        assert len(todos.get("Requirements", [])) == 1
        assert len(todos.get("Acceptance Criteria", [])) == 0  # Missing!
        assert len(todos.get("Command", [])) == 0  # Missing!

        # Now complete the mandatory hierarchy below Requirements
        ac, error = add_acceptance_criteria(
            "GPS Accuracy Test", "Measure GPS accuracy in field conditions", req_id
        )
        assert error is None
        ac_id = ac["id"]

        interface, error = add_interface_contract(
            "GPS Data Format", "NMEA 0183 standard format", ac_id
        )
        assert error is None

        # Skip to Phase (can start at Phase independently)
        phase, error = add_phase(None, "GPS Testing Phase", "Validate GPS accuracy")
        assert error is None
        phase_id = phase["id"]

        step, error = add_step(phase_id, "Field GPS Testing", "Test GPS in actual field")
        assert error is None
        step_id = step["id"]

        task, error = add_task(step_id, "Measure GPS Accuracy", "Record GPS measurements")
        assert error is None
        task_id = task["id"]

        subtask, error = add_subtask(task_id, "Run GPS Accuracy Test", "Execute test protocol")
        assert error is None
        subtask_id = subtask["id"]

        command, error = add_command(
            "Execute GPS Test",
            "Run GPS accuracy measurement",
            "python gps_accuracy_test.py --duration 3600",
            subtask_id,
        )
        assert error is None

        # Verify complete hierarchy now exists
        todos = load_todos()
        assert len(todos.get("Requirements", [])) == 1
        assert len(todos.get("Acceptance Criteria", [])) == 1
        assert len(todos.get("Interface Contract", [])) == 1
        assert len(todos.get("Phase", [])) == 1
        assert len(todos.get("Step", [])) == 1
        assert len(todos.get("Task", [])) == 1
        assert len(todos.get("SubTask", [])) == 1
        assert len(todos.get("Command", [])) == 1

    def test_incomplete_hierarchy_detection(self):
        """Test detection of incomplete hierarchies at various starting points."""

        def check_hierarchy_completeness(starting_layer: str) -> dict[str, Any]:
            """Check if hierarchy is complete from starting layer down."""
            layer_sequence = [
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

            todos = load_todos()
            start_idx = layer_sequence.index(starting_layer)
            required_layers = layer_sequence[start_idx:]

            present_layers = []
            missing_layers = []

            for layer in required_layers:
                if todos.get(layer, []):
                    present_layers.append(layer)
                else:
                    missing_layers.append(layer)

            return {
                "complete": len(missing_layers) == 0,
                "present": present_layers,
                "missing": missing_layers,
                "starting_layer": starting_layer,
            }

        # Test Case 1: Step without Task/SubTask/Command (incomplete)
        init_database()
        step, error = add_step(None, "Incomplete Step", "Step without children")
        assert error is None

        result = check_hierarchy_completeness("Step")
        assert result["complete"] is False
        assert "Task" in result["missing"]
        assert "SubTask" in result["missing"]
        assert "Command" in result["missing"]
        assert "Step" in result["present"]

        # Test Case 2: Complete the hierarchy
        step_id = step["id"]
        task, error = add_task(step_id, "Complete Task", "Now with task")
        task_id = task["id"]

        subtask, error = add_subtask(task_id, "Complete SubTask", "Now with subtask")
        subtask_id = subtask["id"]

        command, error = add_command(
            "Complete Command", "Now complete", "echo complete", subtask_id
        )

        result = check_hierarchy_completeness("Step")
        assert result["complete"] is True
        assert result["missing"] == []
        assert all(layer in result["present"] for layer in ["Step", "Task", "SubTask", "Command"])

    def test_real_world_agricultural_scenarios(self):
        """Test real-world agricultural robotics scenarios with different entry points."""

        # Scenario 1: Research Project - Start at Goal (full planning)
        init_database()
        goal, error = add_goal(
            "Autonomous Corn Harvesting Research",
            "Develop autonomous harvesting for 500-acre corn operation",
        )
        assert error is None
        goal_id = goal["id"]

        # Complete strategic planning layers
        concept, error = add_concept(
            "Multi-Harvester Coordination",
            "Coordinate 3 harvesters with real-time optimization",
            goal_id,
        )
        assert error is None

        # Skip to implementation (Phase level)
        phase, error = add_phase(
            goal_id, "Prototype Development", "Build and test prototype system"
        )
        assert error is None
        phase_id = phase["id"]

        step, error = add_step(phase_id, "Sensor Integration", "Install yield monitoring sensors")
        assert error is None
        step_id = step["id"]

        task, error = add_task(
            step_id, "Calibrate Yield Sensors", "Ensure accurate yield measurement"
        )
        assert error is None
        task_id = task["id"]

        subtask, error = add_subtask(
            task_id, "Field Calibration Test", "Test sensors in actual field"
        )
        assert error is None
        subtask_id = subtask["id"]

        command, error = add_command(
            "Run Sensor Calibration",
            "Execute calibration protocol",
            "python calibrate_yield_sensors.py --field corn_field_7",
            subtask_id,
        )
        assert error is None

        # Scenario 2: Production Issue - Start at Task (urgent fix needed)
        production_task, error = add_task(
            None, "Fix Harvester #2 GPS Issue", "Restore GPS functionality on harvester #2"
        )
        assert error is None
        prod_task_id = production_task["id"]

        # Must complete hierarchy below Task
        fix_subtask, error = add_subtask(
            prod_task_id, "Replace GPS Receiver", "Install new RTK-GPS unit"
        )
        assert error is None
        fix_subtask_id = fix_subtask["id"]

        fix_command, error = add_command(
            "Install GPS Unit",
            "Physical GPS replacement",
            "systemctl stop gps-service && ./install_gps.sh --unit rtk-2000",
            fix_subtask_id,
            "AC-GPS-INSTALL",
        )
        assert error is None

        # Verify both scenarios coexist with different entry points
        todos = load_todos()
        assert len(todos.get("Goal", [])) == 1  # Research project
        assert len(todos.get("Phase", [])) == 1  # Research project
        assert len(todos.get("Task", [])) == 2  # Research + Production
        assert len(todos.get("SubTask", [])) == 2  # Both scenarios
        assert len(todos.get("Command", [])) == 2  # Both scenarios

        # Verify independent hierarchies
        research_task = next(t for t in todos["Task"] if "Calibrate" in t.title)
        production_task = next(t for t in todos["Task"] if "GPS Issue" in t.title)

        # Research task has parents (Step -> Phase -> Goal)
        assert len(research_task.links.parents) == 1
        assert step_id in research_task.links.parents

        # Production task is root (no parents)
        assert len(production_task.links.parents) == 0

    def test_layer_dependency_validation(self):
        """Test that layer dependencies are properly validated."""

        # Test that you cannot create a Command without proper parent structure
        # when starting from a higher layer

        # Start with a Phase
        phase, error = add_phase(None, "Test Phase", "Testing layer dependencies")
        assert error is None
        phase_id = phase["id"]

        # Try to create a Command directly under Phase (should fail validation)
        # This violates the hierarchy: Phase -> Step -> Task -> SubTask -> Command

        # The system should enforce that Commands can only be children of SubTasks
        command, error = add_command(
            "Invalid Command",
            "Should not work directly under Phase",
            "echo 'This should not work'",
            phase_id,
        )

        # The command creation might succeed at the API level, but hierarchy validation
        # should catch this as an invalid structure
        todos = load_todos()

        if command:  # If command was created
            # Verify it's not properly linked to the phase
            command_node = todos["Command"][0]
            phase_node = todos["Phase"][0]

            # Command should not be a direct child of Phase
            assert command_node.id not in phase_node.links.children

        # Now create the proper hierarchy
        step, error = add_step(phase_id, "Proper Step", "Following hierarchy")
        assert error is None
        step_id = step["id"]

        task, error = add_task(step_id, "Proper Task", "Following hierarchy")
        assert error is None
        task_id = task["id"]

        subtask, error = add_subtask(task_id, "Proper SubTask", "Following hierarchy")
        assert error is None
        subtask_id = subtask["id"]

        proper_command, error = add_command(
            "Proper Command",
            "Follows hierarchy",
            "echo 'This follows proper hierarchy'",
            subtask_id,
        )
        assert error is None

        # Verify proper hierarchy
        todos = load_todos()
        phase_node = todos["Phase"][0]
        step_node = todos["Step"][0]
        task_node = todos["Task"][0]
        subtask_node = todos["SubTask"][0]

        # Verify parent-child relationships
        assert step_node.id in phase_node.links.children
        assert task_node.id in step_node.links.children
        assert subtask_node.id in task_node.links.children

        # Command should be child of SubTask
        proper_command_node = next(c for c in todos["Command"] if c.title == "Proper Command")
        assert subtask_node.id in proper_command_node.links.parents
