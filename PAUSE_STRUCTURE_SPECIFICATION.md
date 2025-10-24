# AFS FastAPI Pause Structure Specification

## Purpose

This document defines the mandatory **Recommended Pause Structure for Session Optimization** that must be followed by ALL agents and humans working on the AFS FastAPI agricultural robotics platform.

## Mandatory Compliance

**CRITICAL**: This pause structure is MANDATORY for all contributors:
- ✅ **All AI agents** (Claude, GPT, etc.)
- ✅ **All human developers**
- ✅ **All session types** (development, debugging, documentation)
- ✅ **All work contexts** (features, bug fixes, refactoring)

## Pause Structure Framework

### 1. Task-Level Pauses (Micro-Pauses)

**TRIGGER CONDITIONS:**
- After completing TDD RED-GREEN-REFACTOR cycle
- After all quality gates pass (Black, Ruff, isort, MyPy, pre-commit hooks)
- After successful git commit with quality validation
- Before starting context-heavy integration work
- Every 2-3 completed tasks within a phase

**IMPLEMENTATION:**
```bash
# Execute after each completed task
./bin/pause-here "Task: [TASK_NAME] - [BRIEF_STATUS]" "[NEXT_STEP_DESCRIPTION]"
```

**EXAMPLE:**
```bash
./bin/pause-here "Task: Advanced Message Prioritization - Completed with full TDD coverage" "Ready to implement network congestion detection system"
```

### 2. Phase-Level Pauses (Major Pauses)

**TRIGGER CONDITIONS:**
- End of each development phase (6-task completion)
- After completing functional unit with full test coverage
- At architectural review points
- Before switching development focus areas

**IMPLEMENTATION:**
```bash
# Execute at phase completion
./bin/todo status # Check current phase progress
./bin/pause-here "Phase: [PHASE_NAME] - Complete" "Ready for next phase: [NEXT_PHASE_NAME]"
```

**EXAMPLE:**
```bash
./bin/todo status
./bin/pause-here "Phase: CAN Network Traffic Management - Complete with full test coverage" "Ready for next phase: Physical CAN Interface Integration"
```

### 3. Strategic Milestone Pauses (Critical Pauses)

**TRIGGER CONDITIONS:**
- After completing strategic goals from strategic-list
- Major platform capability completion
- Production readiness validation points
- Before major architectural changes

**IMPLEMENTATION:**
```bash
# Execute at strategic completion
./bin/strategic-complete "Strategic Goal Description"
./bin/saveandpush "Strategic milestone: [DESCRIPTION]"
./bin/pause-here "Strategic: [GOAL_NAME] - Complete" "Ready for next strategic objective: [NEXT_GOAL]"
```

## Session Limit Management

### Mandatory Triggers

**TIME-BASED TRIGGERS:**
- **Target**: Maximum 3-hour development sessions
- **Warning**: At 2.5-hour mark, complete current task and pause
- **Hard Stop**: At 3-hour mark, immediate pause regardless of task state

**CONTEXT-BASED TRIGGERS:**
- Session context approaching complexity limits
- Before starting multi-file complex integrations
- When switching between different architectural concerns
- Before major refactoring efforts

**QUALITY-BASED TRIGGERS:**
- After any test failures that require extensive debugging
- Before implementing features requiring research/analysis
- After completing any infrastructure changes

### Implementation Commands

**EMERGENCY PAUSE** (immediate session preservation):
```bash
./bin/pause-here "Emergency: Session limit approaching" "Resume with current context preserved"
```

**PLANNED PAUSE** (optimal development breakpoint):
```bash
./bin/saveandpush "Completed work before strategic pause"
./bin/pause-here "Planned: [REASON]" "[NEXT_STEPS]"
```

## Quality Gate Integration

### Pre-Pause Quality Requirements

**MANDATORY CHECKS** (must pass before any pause):
1. ✅ All tests passing: `pytest --tb=short`
2. ✅ Code formatting: `black --check`
3. ✅ Linting: `ruff check`
4. ✅ Type checking: `mypy`
5. ✅ Import sorting: `isort --check`
6. ✅ Git status clean: `git status`

**IMPLEMENTATION:**
```bash
# Automated quality check before pause
./bin/quality-check-and-pause "[PAUSE_REASON]" "[NEXT_STEPS]"
```

### Post-Pause Quality Assurance

**MANDATORY VERIFICATION** (after resuming):
1. ✅ Load session context: `./bin/loadsession`
2. ✅ Verify test suite: `pytest --tb=short`
3. ✅ Check git status: `git status`
4. ✅ Validate project state: `./bin/todo status`, `./bin/strategic-status`

## Context Preservation Requirements

### Pause Context Documentation

**MANDATORY FIELDS** for all pause points:
- **Timestamp**: Exact pause time with timezone
- **Git Hash**: Current commit hash for resumption
- **Task Status**: Current progress within active task
- **Step Status**: Progress within current development step
- **Strategic Status**: Progress toward strategic goals
- **Next Steps**: Clear, actionable resumption instructions
- **Dependencies**: Any external dependencies or blockers
- **Quality State**: Last quality gate passage confirmation

### Context File Format

```markdown
# Pause Point Context: [PAUSE_ID]

**Reason:** [DETAILED_PAUSE_REASON]
**Timestamp:** [ISO_TIMESTAMP_WITH_TIMEZONE]
**Git Hash:** [FULL_COMMIT_HASH]
**Current Step:** [STEP_NAME]

## Task Progress
- [X] Completed Task 1
- [X] Completed Task 2
- [ ] Current Task: [TASK_NAME] - [STATUS]
- [ ] Next Task: [NEXT_TASK_NAME]

## Quality Status
- [X] All tests passing
- [X] Code formatted (Black)
- [X] Linting clean (Ruff)
- [X] Types valid (MyPy)
- [X] Imports sorted (isort)
- [X] Git status clean

## Strategic Context
**Current Strategic Goal:** [GOAL_NAME]
**Progress:** [X/Y] strategic goals completed
**Step Progress:** [X/Y] step tasks completed

## Resume Instructions
1. **Load Context:** `./bin/resume-from [PAUSE_ID]`
2. **Verify Quality:** `pytest --tb=short`
3. **Check Status:** `./bin/todo status`, `./bin/strategic-status`
4. **Continue Work:** [SPECIFIC_NEXT_STEPS]

## Dependencies and Blockers
- [LIST_ANY_DEPENDENCIES]
- [LIST_ANY_BLOCKERS]
- [LIST_ANY_RESEARCH_NEEDED]
```

## Enforcement Mechanisms

### Agent Enforcement

**AI AGENTS MUST:**
1. Check session duration before starting new tasks
2. Execute pause structure automatically at trigger points
3. Refuse to continue work past 3-hour sessions without pause
4. Validate quality gates before every pause
5. Create detailed context documentation for every pause

### Human Enforcement

**HUMAN DEVELOPERS MUST:**
1. Follow identical pause structure as AI agents
2. Use provided pause commands and tools
3. Document context thoroughly before pauses
4. Validate quality gates before commits
5. Resume using formal resumption procedures

### Automated Enforcement

**SYSTEM ENFORCEMENT:**
```bash
# Pre-commit hook integration
# File: .git/hooks/pre-commit-pause-validation
if [[ session_duration > 3_hours ]]; then
    echo "ERROR: Session exceeds 3 hours. Execute pause before committing."
    exit 1
fi
```

**CONTINUOUS ENFORCEMENT:**
- Session monitoring with automatic warnings
- Git hook integration for pause validation
- Quality gate enforcement at pause points
- Automated context preservation validation

## Tools and Commands

### Core Pause Commands

**PRIMARY PAUSE COMMAND:**
```bash
./bin/pause-here "[REASON]" "[NEXT_STEPS]"
```

**QUALITY-INTEGRATED PAUSE:**
```bash
./bin/quality-check-and-pause "[REASON]" "[NEXT_STEPS]"
```

**STRATEGIC PAUSE:**
```bash
./bin/strategic-pause "[STRATEGIC_GOAL]" "[COMPLETION_STATUS]"
```

**EMERGENCY PAUSE:**
```bash
./bin/emergency-pause
```

### Resume Commands

**STANDARD RESUME:**
```bash
./bin/resume-from [PAUSE_ID]
```

**QUALITY-VALIDATED RESUME:**
```bash
./bin/resume-with-validation [PAUSE_ID]
```

### Status and Monitoring

**SESSION MONITORING:**
```bash
./bin/session-status           # Current session metrics
./bin/session-time-remaining   # Time until mandatory pause
./bin/session-quality-check    # Quality gates status
```

## Integration with Existing Tools

### Session Management Integration

**LOADESSION INTEGRATION:**
- `./bin/loadsession` automatically checks for active pause points
- Validates resumption context and quality state
- Restores TODO state and strategic progress

**SAVEANDPUSH INTEGRATION:**
- `./bin/saveandpush` automatically triggers pause evaluation
- Enforces quality gates before saving
- Creates resumption context automatically



### Strategic Management Integration

**STRATEGIC COMMAND INTEGRATION:**
- `./bin/strategic-complete` triggers strategic milestone pause
- Strategic goal completion requires context preservation
- Strategic pauses include comprehensive status documentation

## Compliance Validation

### Pre-Session Validation

**MANDATORY CHECKS** before starting any work session:
1. ✅ Previous session properly paused and documented
2. ✅ All quality gates passed in previous session
3. ✅ Git status clean with latest work committed
4. ✅ Strategic and task/step status validated

### During-Session Monitoring

**CONTINUOUS MONITORING:**
- Session duration tracking with warnings
- Quality gate status monitoring
- Task completion tracking
- Context complexity assessment

### Post-Session Validation

**MANDATORY VALIDATION** after any pause:
1. ✅ Pause context properly documented
2. ✅ Quality gates validated
3. ✅ Work committed and saved
4. ✅ Resumption instructions clear and actionable

## Benefits and Rationale

### Prevents Session Context Loss
- No work lost due to session limits
- Complete development context preserved
- Quality state maintained across sessions

### Ensures Development Quality
- Quality gates enforced at natural breakpoints
- Test coverage validated before pauses
- Code quality maintained consistently

### Optimizes Development Flow
- Natural pause points maintain momentum
- Context switching optimized for resumption
- Strategic progress tracked and preserved

### Enables Team Collaboration
- Consistent pause structure across all contributors
- Clear resumption instructions for handoffs
- Standardized context documentation

## Version Control and Updates

**DOCUMENT VERSION:** 1.0.0
**EFFECTIVE DATE:** 2025-10-10
**MANDATORY COMPLIANCE DATE:** Immediate (all sessions)

**UPDATE REQUIREMENTS:**
- Changes to this specification require project maintainer approval
- Updates must be tested with existing session management tools
- All agents and humans must be notified of specification changes
- Backward compatibility must be maintained for existing pause contexts

---

**FINAL REQUIREMENT**: This specification is MANDATORY for all AFS FastAPI agricultural robotics platform development. No exceptions are permitted. All agents and humans MUST implement and follow this pause structure to ensure project quality, continuity, and success.