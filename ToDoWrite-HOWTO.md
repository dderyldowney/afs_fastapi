# ToDoWrite System: Complete User Guide

> **A practical guide to using the 12-layer hierarchical task management system for agricultural robotics development**

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Understanding the 12-Layer Hierarchy](#understanding-the-12-layer-hierarchy)
3. [Getting Started](#getting-started)
4. [Daily Development Workflow](#daily-development-workflow)
5. [Agricultural Robotics Examples](#agricultural-robotics-examples)
6. [Command Reference](#command-reference)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

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

---

## Getting Started

### 1. Check System Status

```bash
# View overall system status
./bin/todo-status

# Check strategic progress
./bin/strategic-status

# View current development phase
./bin/phase-status
```

### 2. Your First Project Setup

#### Option A: Through Command Interface (Recommended for beginners)

```bash
# 1. Check what's currently active
./bin/todo-status

# 2. Start a new development phase
./bin/phase-start "CAN Communication Setup" GOAL-MULTI-TRACTOR

# 3. Add implementation steps
./bin/step-add "Hardware Configuration"
./bin/step-add "Software Integration"
./bin/step-add "Testing & Validation"

# 4. Add specific tasks
./bin/task-add "Install CAN hardware interfaces"
./bin/task-add "Configure network topology"

# 5. Add executable subtasks (Layer 12 only)
./bin/subtask-add "Setup CAN interface" "sudo modprobe can && sudo modprobe can-raw" bash
```

#### Option B: Through Python Interface (For strategic planning)

```python
# Create strategic goals through Python
python3 -c "
from afs_fastapi.todos.manager import create_node

goal_data = {
    'id': 'GOAL-AUTONOMOUS-TRACTORS',
    'layer': 'Goal',
    'title': 'Implement Autonomous Multi-Tractor Coordination',
    'description': 'Enable 3+ tractors to coordinate field operations autonomously while maintaining ISO 11783 safety compliance',
    'status': 'planned',
    'owner': 'agricultural-team',
    'severity': 'high',
    'work_type': 'architecture',
    'labels': ['agricultural', 'autonomous', 'safety-critical'],
    'parent_ids': [],
    'child_ids': []
}

create_node(goal_data)
print('Strategic goal created successfully!')
"
```

### 3. Verify Your Setup

```bash
# Check that everything is working
./bin/strategic-status  # Should show your goal
./bin/phase-status      # Should show active phase
./bin/step-status       # Should show current step
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

echo -e "\n📋 Today's Phase:"
./bin/phase-status

echo -e "\n⚡ Ready for Execution:"
./bin/step-status
```

### 🔨 Active Development Session

#### Starting Work on a Specific Task

```bash
# 1. Activate the work hierarchy
./bin/phase-activate PHASE-ID     # Set active phase
./bin/step-activate STEP-ID       # Set active step
./bin/task-activate TASK-ID       # Set active task

# 2. Check what needs to be done
./bin/todo-status                 # Overview
./bin/step-status                 # Current step details

# 3. Work on implementation
# (Write code, run tests, execute commands)

# 4. Execute specific commands (Layer 12 only)
# Commands are in your subtasks - execute them as needed
```

#### Example Development Session: CAN Bus Implementation

```bash
# Scenario: Working on CAN bus configuration for tractor coordination

# 1. Check current status
./bin/phase-status  # Should show "CAN Communication Setup" active

# 2. Work on current step
./bin/step-status   # Shows "Hardware Configuration" step

# 3. Add today's tasks
./bin/task-add "Configure CAN0 interface on Tractor-001"
./bin/task-add "Test message throughput between tractors"

# 4. Add executable commands
./bin/subtask-add "Enable CAN module" "sudo modprobe can && sudo modprobe can-raw" bash
./bin/subtask-add "Set CAN bitrate" "sudo ip link set can0 type can bitrate 250000" bash
./bin/subtask-add "Bring CAN interface up" "sudo ip link set can0 up" bash
./bin/subtask-add "Test CAN communication" "candump can0 | head -20" bash

# 5. Execute the commands (one by one as needed)
# Note: Commands are executed manually - they're documented in subtasks

# 6. Mark completion as you finish
./bin/task-complete TASK-ID
```

### 🔄 Progress Tracking During the Day

```bash
# Quick status check (run anytime)
./bin/todo-status

# Update progress on current work
./bin/task-complete TASK-ID        # Mark task complete
./bin/step-complete STEP-ID        # Mark step complete

# Move to next phase when ready
./bin/phase-complete PHASE-ID
./bin/phase-start "Next Phase Name" GOAL-ID
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

```bash
# 1. Create strategic goal (Python)
python3 -c "
from afs_fastapi.todos.manager import create_node

create_node({
    'id': 'GOAL-FIELD-COORDINATION',
    'layer': 'Goal',
    'title': 'Multi-Tractor Field Coordination System',
    'description': 'Coordinate 5 John Deere tractors for autonomous corn harvesting with real-time position sharing and collision avoidance',
    'owner': 'field-operations-team',
    'labels': ['multi-tractor', 'coordination', 'safety-critical', 'harvest']
})
"

# 2. Set up development phases
./bin/phase-add "System Architecture Design"
./bin/phase-add "Communication Infrastructure"
./bin/phase-add "Coordination Algorithm Development"
./bin/phase-add "Safety System Integration"
./bin/phase-add "Field Testing & Validation"
./bin/phase-add "Production Deployment"
```

#### Implementation Breakdown

```bash
# Phase 1: Communication Infrastructure
./bin/phase-start "Communication Infrastructure" GOAL-FIELD-COORDINATION

# Steps for communication
./bin/step-add "CAN Bus Network Setup"
./bin/step-add "GPS Data Integration"
./bin/step-add "Wireless Mesh Network"
./bin/step-add "Message Protocol Definition"

# Tasks for CAN Bus setup
./bin/step-activate STEP-CAN-BUS
./bin/task-add "Install CAN transceivers on all tractors"
./bin/task-add "Configure CAN network topology"
./bin/task-add "Implement ISO 11783 message handling"
./bin/task-add "Test message throughput and latency"

# Executable commands (Layer 12)
./bin/subtask-add "Setup CAN interface" "sudo ip link set can0 type can bitrate 250000 && sudo ip link set can0 up" bash
./bin/subtask-add "Monitor CAN traffic" "candump can0 -L" bash
./bin/subtask-add "Send test message" "cansend can0 123#DEADBEEF" bash
```

### Example 2: Safety Compliance Project

#### ISO 11783 Compliance Tracking

```bash
# Strategic goal for compliance
python3 -c "
from afs_fastapi.todos.manager import create_node

create_node({
    'id': 'GOAL-ISO11783-COMPLIANCE',
    'layer': 'Goal',
    'title': 'Achieve ISO 11783 Agricultural Communication Compliance',
    'description': 'Ensure all tractor communication systems meet ISO 11783 standards for agricultural equipment interoperability'
})
"

# Compliance phases
./bin/phase-add "Standards Analysis"
./bin/phase-add "Implementation"
./bin/phase-add "Testing & Validation"
./bin/phase-add "Certification"

# Safety-specific tasks
./bin/step-add "Emergency Stop System Implementation"
./bin/task-add "Install emergency stop buttons on all tractors"
./bin/task-add "Implement stop signal propagation via CAN"
./bin/task-add "Test emergency stop response times"

# Safety validation commands
./bin/subtask-add "Test emergency stop response" "python test_emergency_stop.py --max-response-time 500ms" python
./bin/subtask-add "Validate ISO message format" "python validate_iso11783_messages.py --input can0" python
```

### Example 3: Daily Agricultural Operations

#### Typical Day: Corn Harvesting Coordination

```bash
# Morning: Check system status
./bin/todo-status                    # Overall progress
./bin/phase-status                   # Current development phase

# Active work: GPS coordination feature
./bin/task-add "Implement GPS position sharing between tractors"
./bin/subtask-add "Read GPS from John Deere API" "python read_gps_data.py --tractor JD001" python
./bin/subtask-add "Broadcast position via CAN" "python broadcast_position.py --interval 100ms" python

# Testing: Field validation
./bin/task-add "Test 3-tractor coordination in south field"
./bin/subtask-add "Deploy coordination software" "ansible-playbook deploy-coordination.yml" bash
./bin/subtask-add "Monitor field operation" "python monitor_field_ops.py --duration 60min" python

# End of day: Save progress
./bin/saveandpush "GPS coordination feature complete, field testing successful"
```

---

## Command Reference

### Strategic Management

| Command | Purpose | Example |
|---------|---------|---------|
| `./bin/strategic-status` | View strategic progress overview | Shows completion percentages |
| `./bin/strategic-add` | Add new strategic objective | Creates new goal |
| `./bin/strategic-complete` | Mark strategic goal complete | Updates goal status |
| `./bin/strategic-list` | List all strategic objectives | Shows all goals |

### Phase Management

| Command | Purpose | Example |
|---------|---------|---------|
| `./bin/phase-status` | Current phase status | Shows active phase details |
| `./bin/phase-start <name> <goal>` | Start new phase | `./bin/phase-start "Hardware Setup" GOAL-001` |
| `./bin/phase-add <name>` | Add phase to project | `./bin/phase-add "Testing Phase"` |
| `./bin/phase-activate <id>` | Activate specific phase | `./bin/phase-activate PHASE-123` |
| `./bin/phase-complete <id>` | Mark phase complete | `./bin/phase-complete PHASE-123` |
| `./bin/phase-list-all` | List all phases | Shows all project phases |

### Step Management

| Command | Purpose | Example |
|---------|---------|---------|
| `./bin/step-status` | Current step status | Shows active step details |
| `./bin/step-add <name>` | Add step to active phase | `./bin/step-add "CAN Configuration"` |
| `./bin/step-activate <id>` | Activate specific step | `./bin/step-activate STEP-456` |
| `./bin/step-complete <id>` | Mark step complete | `./bin/step-complete STEP-456` |

### Task Management

| Command | Purpose | Example |
|---------|---------|---------|
| `./bin/task-add <title>` | Add task to active step | `./bin/task-add "Install CAN hardware"` |
| `./bin/task-activate <id>` | Activate specific task | `./bin/task-activate TASK-789` |
| `./bin/task-complete <id>` | Mark task complete | `./bin/task-complete TASK-789` |
| `./bin/subtask-add <title> <cmd> <type>` | Add executable subtask | `./bin/subtask-add "Setup CAN" "modprobe can" bash` |

### System Management

| Command | Purpose | Example |
|---------|---------|---------|
| `./bin/todo-status` | Overall system status | Shows complete overview |
| `./bin/todo-sync` | Sync todo state | Synchronizes database |
| `./bin/saveandpush <message>` | Save and push changes | `./bin/saveandpush "Feature complete"` |

---

## Best Practices

### 🛡️ Safety-First Development

1. **Always Start with Safety Constraints**
   ```bash
   # Before any implementation, define safety requirements
   # Example: Emergency stop response time < 500ms
   ```

2. **Link Everything to Strategic Goals**
   ```bash
   # Every task should trace back to a business goal
   # Use ./bin/strategic-status to verify alignment
   ```

3. **Document Before Implementing**
   ```bash
   # Layers 1-11 are planning - document thoroughly
   # Only Layer 12 executes - keep commands simple and testable
   ```

### 🔄 Workflow Optimization

1. **Daily Rhythm**
   ```bash
   # Morning: ./bin/todo-status (what needs doing?)
   # Midday: ./bin/phase-status (progress check)
   # Evening: ./bin/saveandpush (save progress)
   ```

2. **Granular Progress Tracking**
   ```bash
   # Mark completion immediately when finished
   ./bin/task-complete TASK-ID

   # Don't batch completions - update in real-time
   ```

3. **Clear Naming Conventions**
   ```bash
   # Use descriptive names
   # Good: "Configure CAN bus for ISO 11783 compliance"
   # Bad: "Fix CAN stuff"
   ```

### 🌾 Agricultural Context Integration

1. **Equipment-Specific Planning**
   ```bash
   # Consider specific tractor models, GPS systems, etc.
   # Example: "Configure for John Deere 8R series with StarFire 6000"
   ```

2. **Field Condition Awareness**
   ```bash
   # Factor in weather, terrain, crop conditions
   # Example: "Test coordination in muddy field conditions"
   ```

3. **Compliance Documentation**
   ```bash
   # Always link to relevant agricultural standards
   # Example: ISO 11783, ISO 25119, ASABE standards
   ```

### 🔗 Traceability Maintenance

1. **Parent-Child Relationships**
   ```bash
   # Every item should have clear parents and children
   # Goals → Phases → Steps → Tasks → SubTasks → Commands
   ```

2. **Acceptance Criteria Links**
   ```bash
   # Commands must link to acceptance criteria
   # Ensures every execution has a purpose and test
   ```

3. **Strategic Alignment**
   ```bash
   # Regular alignment checks
   ./bin/strategic-status  # Are we achieving goals?
   ```

---

## Troubleshooting

### Common Issues

#### "No strategic goals found"
```bash
# Solution: Create a strategic goal first
python3 -c "
from afs_fastapi.todos.manager import create_node
create_node({
    'id': 'GOAL-TEST',
    'layer': 'Goal',
    'title': 'Test Goal',
    'description': 'Test goal for learning the system'
})
"
```

#### "No active phase"
```bash
# Solution: Start or activate a phase
./bin/phase-start "Learning Phase" GOAL-TEST
# OR
./bin/phase-activate EXISTING-PHASE-ID
```

#### "Database errors"
```bash
# Solution: Reinitialize database
python3 -c "from afs_fastapi.todos.manager import init_database; init_database()"
```

#### "Commands not executing"
```bash
# Remember: Only Layer 12 (Commands) execute
# Layers 1-11 are documentation only
# Commands are stored in subtasks - execute them manually as needed
```

### Getting Help

1. **Check System Status**
   ```bash
   ./bin/todo-status      # Overall health check
   ./bin/strategic-status # Strategic progress
   ```

2. **Verify Database**
   ```bash
   ls -la todos.db        # Database file exists?
   ```

3. **Review Recent Activity**
   ```bash
   git log --oneline -5   # Recent changes
   ```

---

## Conclusion

The ToDoWrite system provides a **systematic approach to agricultural robotics development** that ensures:

- ✅ **Safety compliance** through structured requirements
- ✅ **Strategic alignment** from goals to execution
- ✅ **Full traceability** for agricultural standards
- ✅ **Systematic progress** through clear workflows
- ✅ **Quality assurance** with separation of planning and execution

### Next Steps

1. **Start Small**: Create your first goal and phase
2. **Practice Daily**: Use the morning/evening routines
3. **Build Gradually**: Add complexity as you master the basics
4. **Stay Agricultural**: Always consider field operations context
5. **Maintain Traceability**: Keep parent-child links updated

The key insight: **Plan systematically (Layers 1-11), Execute carefully (Layer 12)**.

---

*For technical issues or questions about the ToDoWrite system, refer to the `ToDoWrite.md` specification or check the `bin/` directory for additional commands.*