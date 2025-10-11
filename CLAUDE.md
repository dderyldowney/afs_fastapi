# Claude Code Configuration for AFS FastAPI

This file contains project-specific instructions for Claude Code sessions working on the **AFS FastAPI robotic agriculture platform**.

## Mandatory Universal Requirements

**Authoritative Source**: All universal agent requirements, including TDD workflows, commit standards, documentation practices, and environment setup, are defined in **`AGENTS.md`**. You must load and adhere to these rules. This file only contains overrides or instructions specific to Claude.

---

## Claude-Specific Instructions

### Format-First Generation Standards

**Requirement**: All generated content must emerge in final quality-controlled form.

**NO FORMATTING CYCLES**: Generate all code, tests, and documentation pre-formatted to quality standards.

1.  **Code Generation**: Apply Black, isort, Ruff compliance during creation
2.  **Type Safety**: Include proper type annotations from initial generation
3.  **Agricultural Context**: Embed domain-specific examples and scenarios
4.  **Quality Standards**: Meet enterprise-grade requirements immediately

### Pre-Formatted Generation Templates

**Python Code Template**:
'''python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

class AgriculturalComponent:
    """Agricultural robotics component for tractor coordination.

    Provides functionality for multi-tractor field operations with
    safety compliance and performance optimization.
    """

    def __init__(self, equipment_id: str) -> None:
        """Initialize agricultural equipment interface."""
        self.equipment_id = equipment_id
        self.operational_status = "ready"

    def coordinate_field_operation(self, operation_data: Dict[str, Any]) -> bool:
        """Execute coordinated field operation with fleet synchronization."""
        return True
'''

**Test Generation Template**:
'''python
import pytest
from afs_fastapi.equipment.farm_tractors import FarmTractor

class TestAgriculturalOperation:
    """Test agricultural equipment operations for field coordination."""

    def test_tractor_field_coordination(self) -> None:
        """Test multi-tractor coordination during field cultivation."""
        # RED: Describe desired agricultural behavior
        tractor = FarmTractor(equipment_id="FIELD_CULTIVATOR_01")

        # Test agricultural operation
        result = tractor.execute_cultivation_pattern()

        assert result is True
        assert tractor.field_status == "cultivation_complete"
'''

### Code Documentation Requirements

**Educational Code Explanations**: All code generated must be explained both **overall** and **individually**. Explanations should be concise with the dual purpose of teaching while building this real-world professional project.

### Claude Command Integration

The platform provides universal session management commands available to all AI agents, as defined in `AGENTS.md` and `SESSION_SUMMARY.md`.

**Claude Code Specific Integration**:
- Commands are executable via bash: `./bin/commandname`
- Select commands are available as slash commands: `/loadsession`, `/whereweare`, `/updatedocs`
- Command triggers are stored in `.claude/commands/` with complete specifications.

### Mandatory TodoWrite.md Task Management

**CRITICAL REQUIREMENT**: Claude Code MUST follow the "Mandatory TodoWrite.md Task Management System" defined in `AGENTS.md` with zero exceptions.

### Mandatory Pause Structure for Claude Code

**CRITICAL REQUIREMENT**: Claude Code MUST implement the mandatory pause structure defined in `PAUSE_STRUCTURE_SPECIFICATION.md` with zero exceptions.

**Claude-Specific Pause Enforcement**:

1. **Automatic Session Monitoring**: Claude MUST continuously monitor session duration and trigger pauses at appropriate points (session monitoring)
2. **Quality Gate Integration**: Before every pause, Claude MUST validate all quality gates (Black, Ruff, isort, MyPy, pre-commit hooks)
3. **Context Preservation**: Claude MUST create detailed resumption context using the standardized format
4. **Task Completion Tracking**: Claude MUST use TodoWrite tool to track progress and pause at natural task boundaries

**Claude Pause Commands** (mandatory usage):

```bash
# Task-level pause (every 2-3 completed tasks)
./bin/pause-here "Task: [TASK_NAME] - [STATUS]" "[NEXT_STEPS]"

# Phase-level pause (phase completion)
./bin/phase-end
./bin/pause-here "Phase: [PHASE_NAME] - Complete" "[NEXT_PHASE]"

# Strategic pause (strategic goal completion)
./bin/strategic-complete "[GOAL_DESCRIPTION]"
./bin/saveandpush "Strategic milestone: [DESCRIPTION]"
./bin/pause-here "Strategic: [GOAL_NAME] - Complete" "[NEXT_STRATEGIC_GOAL]"

# Emergency pause (session limit approaching)
./bin/pause-here "Emergency: Session limit approaching" "Resume with context preserved"
```

**Claude Session Limits** (strictly enforced):
- **Maximum session duration**: 3 hours
- **Warning trigger**: 2.5 hours - complete current task and pause
- **Hard stop**: 3 hours - immediate pause regardless of task state
- **Quality validation**: All work must pass quality gates before pause

**Claude Context Requirements**:
- **Before pause**: TodoWrite status, git status clean, quality gates passed
- **During pause**: Detailed resumption instructions with specific next steps
- **After resume**: Load session context, validate project state, verify git status

**Integration with Claude Code Workflow**:
1. Claude MUST check session duration before starting new tasks
2. Claude MUST pause at task completion boundaries within phases
3. Claude MUST enforce quality gates before every pause
4. Claude MUST use TodoWrite tool for progress tracking
5. Claude MUST create git commits for completed work before pausing
6. Claude MUST follow the commit-per-task workflow established in this project

**Claude Pause Context Template**:
```markdown
# Claude Code Pause Context: [PAUSE_ID]

**Session Type:** Claude Code Development Session
**Pause Reason:** [DETAILED_REASON]
**Timestamp:** [ISO_TIMESTAMP]
**Duration:** [SESSION_DURATION]
**Git Hash:** [COMMIT_HASH]

## Claude-Specific Context
**Current File(s):** [FILES_BEING_WORKED_ON]
**Active TODO Status:** [X/Y] todos completed
**Quality Gates:** [PASSED/FAILED] - [DETAILS]
**Test Status:** [PASSING/FAILING] - [COUNT]

## Task Progress (TodoWrite Status)
- [X] Completed Task 1
- [X] Completed Task 2
- [ ] Current Task: [TASK_NAME] - [STATUS]
- [ ] Next Task: [NEXT_TASK]

## Claude Resume Instructions
1. Execute: `./bin/loadsession`
2. Verify: `git status` (should be clean)
3. Check: `pytest --tb=short` (all tests passing)
4. Update: TodoWrite tool with current progress
5. Continue: [SPECIFIC_NEXT_ACTIONS]

## Agricultural Context
**Current System:** [AGRICULTURAL_SYSTEM_BEING_DEVELOPED]
**Safety Considerations:** [ANY_SAFETY_CRITICAL_ASPECTS]
**Performance Requirements:** [TIMING_OR_RELIABILITY_CONSTRAINTS]
```

**Enforcement Mechanism**:
Claude Code MUST refuse to continue development past 3-hour sessions without executing a proper pause. This is a hard requirement with zero exceptions to prevent context loss and ensure development quality in the agricultural robotics platform.

### Mandatory Git Commit Message Format

**CRITICAL REQUIREMENT**: Claude Code MUST follow the "Mandatory Git Commit Message Format" defined in `AGENTS.md` with zero exceptions.

### Mandatory Type Hinting and Annotation

**CRITICAL REQUIREMENT**: Claude Code MUST follow the "Mandatory Type Hinting and Annotation" defined in `AGENTS.md` with zero exceptions.
