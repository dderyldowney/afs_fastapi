# Session Establishment & Verification Execution Order

> **Navigation**: [📚 DOCS Index](README.md) | [🏠 Project Root](../) | [📋 Monitoring](monitoring/) | [🔧 Implementation](implementation/)
>
> **Last Updated**: 2025-09-30
> **Platform Version**: v0.1.3
> **Maintenance**: CONTINUOUS - Update when session architecture changes

---

## Overview

This document defines the complete execution order for session establishment and verification in the AFS FastAPI agricultural robotics platform. Understanding this architecture is critical for maintaining the safety-critical multi-tractor coordination system.

**Total Files Involved**: 28+ files across 6 execution phases
**Primary Purpose**: Establish conceptual, contextual, and functional session state for ALL AI agents

---

## Executive Summary

**Session initialization uses a sophisticated multi-layered architecture**:

1. **Automatic Hook-Based**: Claude Code hooks detect new sessions and execute loadsession automatically
2. **Manual Fallback**: Users can explicitly run `bin/loadsession` for context restoration
3. **Conceptual Loading**: CLAUDE.md and SESSION_SUMMARY.md provide requirements and state
4. **Enforcement**: Validation hooks ensure compliance with TDD, investigation patterns, CHANGELOG
5. **Documentation**: MANDATORY specification files define universal AI agent requirements
6. **Testing**: Comprehensive test suites validate all initialization logic

**Why This Matters for Agricultural Robotics**: Safety-critical systems demand reliable context propagation across all development sessions, ensuring every AI agent (Claude, GPT, Gemini, Copilot, CodeWhisperer) has access to ISO 18497/11783 compliance requirements, Test-First Development methodology, and investigation pattern standards.

---

## Phase 1: Automatic Hook-Based Initialization

**Trigger**: First tool use OR SessionStart event
**Executor**: Claude Code hook system
**Purpose**: Detect new sessions and automatically load project context

### 1.1 Hook Registration

**File**: [.claude/settings.local.json](../.claude/settings.local.json)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/session_initialization.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/session_initialization.py"
          }
        ]
      }
    ]
  }
}
```

- **Classification**: Pure Configuration
- **Role**: Registers which hooks execute and when
- **Line Count**: ~93 lines
- **Key Settings**: Hook registration, permission model, output style
- **Continuous Update**: When adding new hooks or changing permissions

### 1.2 Session Detection Logic

**File**: [.claude/hooks/session_initialization.py](../.claude/hooks/session_initialization.py)

**Classification**: Pure Functional (Executable Python)
**Role**: Automatic session detection and loadsession execution
**Line Count**: ~200+ lines
**Test Coverage**: [tests/unit/hooks/test_session_initialization.py](../tests/unit/hooks/test_session_initialization.py) (10 tests)

**Detection Strategies**:
1. **Timestamp-based**: If `.session_initialized` is older than 5 minutes
2. **Agent registry**: Tracks all agent IDs and last activity times
3. **Global markers**: `.global_session_state` for cross-session persistence
4. **Universal access**: `.universal_access_enabled` for all agent types

**Key Functions**:
```python
def is_new_session(self) -> bool:
    """Determine if this is a new session requiring initialization."""
    # Strategy 1: Check session marker age
    if self._is_marker_stale(self.session_marker):
        return True

    # Strategy 2: Check agent registry staleness
    if self._is_agent_registry_stale():
        return True

    # Strategy 3: Check global session marker
    if self._is_marker_stale(self.global_session_marker):
        return True

    return False

def execute_loadsession(self) -> bool:
    """Execute bin/loadsession to restore project context."""
    result = subprocess.run([str(self.loadsession_script)])
    return result.returncode == 0
```

**Continuous Update**: When changing session detection logic or staleness thresholds

### 1.3 Session State Markers

**Runtime Files** (Gitignored):
- `.claude/.session_initialized` - Timestamp of last initialization
- `.claude/.agent_registry.json` - Agent activity tracking
- `.claude/.global_session_state` - Cross-session persistence marker
- `.claude/.universal_access_enabled` - Universal agent access indicator

**Classification**: Functional State
**Role**: Track session state across invocations
**Format**: Timestamp files or JSON registries

**Agent Registry Format**:
```json
{
  "agents": [
    {
      "agent_id": "agent_abc123_1727712345",
      "timestamp": 1727712345.67,
      "session_type": "main"
    },
    {
      "agent_id": "agent_def456_1727712389",
      "timestamp": 1727712389.12,
      "session_type": "subagent"
    }
  ],
  "last_update": 1727712389.12
}
```

**Continuous Update**: Automatically managed by session_initialization.py

---

## Phase 2: Manual Session Loading (Fallback/Explicit)

**Trigger**: User executes `bin/loadsession` or `loadsession` command
**Executor**: Bash script
**Purpose**: Provide manual fallback for context restoration

### 2.1 Session Loading Script

**File**: [bin/loadsession](../bin/loadsession)

**Classification**: Pure Functional (Executable Bash)
**Role**: Loads and displays SESSION_SUMMARY.md with visual formatting
**Line Count**: ~131 lines
**Test Coverage**: [bin/test_loadsession.sh](../bin/test_loadsession.sh)

**Key Operations**:
1. Locates SESSION_SUMMARY.md (root or docs/monitoring fallback)
2. Extracts platform status (version, test count, quality metrics)
3. Displays strategic priorities and documentation framework
4. Shows CRITICAL reminders (investigation pattern, TDD enforcement)
5. Displays current git status for context

**Output Format**:
```bash
🚀 AFS FastAPI Session Context Loader
=====================================

✅ SESSION_SUMMARY.md found
📋 Loading Project Context...

📊 Current Platform Status:
   • Version: v0.1.3 (Stable Release)
   • Testing: 148 comprehensive tests
   • Methodology: Test-First Development operational

🎯 Strategic Priority:
   • Focus: Synchronization infrastructure development
   • Foundation: Distributed systems (Vector Clock implemented)

🚨 CRITICAL: MANDATORY INVESTIGATION PATTERN ACTIVE
====================================================
ALL AI agent responses MUST follow structured investigation pattern:
   • Investigation Steps: Numbered methodology
   • Files Examined: File paths with rationale
   • Evidence Collected: Factual findings with indicators
   • Final Analysis: Root cause and solutions
Applies to: Claude, GPT, Gemini, Copilot, CodeWhisperer, all AI agents

🚨 CRITICAL: MANDATORY TDD ENFORCEMENT ACTIVE
================================================
ALL AI agents MUST follow Test-Driven Development methodology:
   • RED Phase: Write failing tests FIRST
   • GREEN Phase: Generate minimal code to pass tests
   • REFACTOR Phase: Enhance quality while maintaining coverage
Applies to: Claude, GPT, Gemini, Copilot, CodeWhisperer, all AI agents
```

**Continuous Update**: When changing reminder messages or adding new critical requirements

---

## Phase 3: Conceptual Context Loading

**Trigger**: Loaded by bin/loadsession OR read directly by AI agents
**Purpose**: Provide complete platform state and mandatory requirements

### 3.1 Primary Session State Document

**File**: [docs/monitoring/SESSION_SUMMARY.md](monitoring/SESSION_SUMMARY.md)

**Classification**: Documentation + Contextual
**Role**: PRIMARY source of truth for current platform state
**Line Count**: ~578 lines
**Referenced By**: bin/loadsession, CLAUDE.md, hooks, AI agents

**Key Sections**:
1. **Current Platform Status** (v0.1.3+)
   - Test count: 161 tests
   - Code quality: Zero warnings
   - Industry compliance: ISO 11783, ISO 18497
   - Distributed systems: Vector Clock operational

2. **CRITICAL: MANDATORY Structured Investigation Pattern**
   - Universal AI agent requirement
   - Four-section structure (Steps, Files, Evidence, Analysis)
   - Cross-session enforcement

3. **CRITICAL: ABSOLUTE Test-First Development**
   - RED-GREEN-REFACTOR protocol
   - Universal AI agent enforcement
   - Zero exceptions policy

4. **MANDATORY: CHANGELOG.md Maintenance**
   - Before-every-commit protocol
   - Cross-session enforcement

5. **Current Session State and Achievements**
   - Recent implementations
   - Strategic priorities
   - Development focus areas

**Update Frequency**: After every significant platform change, version bump, or requirement addition

**Continuous Update Triggers**:
- Test count changes (currently 148)
- Version changes (currently v0.1.3)
- New MANDATORY requirements added
- Strategic priority shifts
- Major feature implementations

### 3.2 Project-Specific AI Agent Instructions

**File**: [CLAUDE.md](../CLAUDE.md)

**Classification**: Configuration + Documentation
**Role**: Defines ALL mandatory requirements for AI agents
**Line Count**: ~347 lines
**Loaded By**: Claude Code automatically on session start

**Key Sections**:
1. **MANDATORY: Test-First Development for ALL Code Generation**
   - Universal test-first protocol
   - Zero exceptions policy
   - Enforcement mechanisms

2. **MANDATORY: Structured Investigation Pattern for ALL AI Agent Responses**
   - Universal investigation protocol
   - Enforcement and scope
   - Complete specification reference

3. **MANDATORY: Format-First Generation Standards**
   - Pre-formatted code templates
   - Error monitoring integration
   - CHANGELOG.md maintenance

4. **Code Documentation Requirements**
   - Educational code explanations
   - Architecture and implementation levels

5. **Project Context**
   - Fleet coordination
   - Industry compliance
   - Robotic interfaces

6. **Development Workflow**
   - Test-First Development
   - Branch strategy
   - Commit separation
   - Documentation standards

**Continuous Update**: When adding new MANDATORY requirements or changing enforcement policies

### 3.3 Agent Specification Document

**File**: [AGENTS.md](../AGENTS.md)

**Classification**: Configuration + Documentation
**Role**: Agent specification and usage guide
**Line Count**: ~136 lines (as of latest update)
**Version**: 1.1.0

**Key Sections**:
1. **Agent Description**
   - Hal — AFS FastAPI Assistant
   - Enforces ABSOLUTE Test-First Development
   - Mandatory structured investigation patterns
   - Universal AI agent support (Claude, GPT, Gemini, Copilot, CodeWhisperer)

2. **How to Use**
   - Session initialization: `./loadsession`
   - MANDATORY INVESTIGATION PATTERN requirement
   - ZERO EXCEPTIONS: ALL development starts with tests
   - Test validation: Ensure all 161 tests pass

3. **Configuration**
   - Python >=3.12,<3.13
   - Quality gates: Ruff, Black, MyPy, isort (161 tests maintained)
   - TDD enforcement hooks
   - Safety validation

4. **Recent Implementation**
   - INVESTIGATION_PATTERN_MANDATORY.md (374 lines)
   - TDD_FRAMEWORK_MANDATORY.md (319 lines)
   - CI/CD pipeline (161 tests validation)

**Continuous Update**: When agent version changes, requirements added, or test count updates

---

## Phase 4: Enforcement & Validation

**Trigger**: On tool use (PreToolUse hook) or user prompt submission
**Purpose**: Validate compliance with mandatory requirements

### 4.1 Pre-Tool Validation Wrapper

**File**: [.claude/hooks/pre_tool_validation_wrapper.py](../.claude/hooks/pre_tool_validation_wrapper.py)

**Classification**: Pure Functional
**Role**: Validates tool usage before execution
**Registered**: PreToolUse hook in settings.local.json
**Purpose**: Ensure tool calls comply with project standards

**Continuous Update**: When adding new tool validation rules

### 4.2 User Prompt TDD Wrapper

**File**: [.claude/hooks/user_prompt_tdd_wrapper.py](../.claude/hooks/user_prompt_tdd_wrapper.py)

**Classification**: Pure Functional
**Role**: Reminds about TDD requirements on prompt submit
**Registered**: UserPromptSubmit hook in settings.local.json
**Purpose**: Ensure test-first awareness before code generation

**Continuous Update**: When changing TDD reminder messaging

### 4.3 Investigation Pattern Validator

**File**: [.claude/hooks/investigation_pattern_validator.py](../.claude/hooks/investigation_pattern_validator.py)

**Classification**: Pure Functional
**Role**: Validates AI agent responses follow investigation pattern
**Line Count**: ~324 lines
**Purpose**: Universal agent response validation (Claude, GPT, Gemini, Copilot, etc.)

**Validation Checks**:
- Investigation Steps section present
- Files Examined section present
- Evidence Collected section present
- Final Analysis section present

**Continuous Update**: When changing investigation pattern requirements or adding new AI agents

---

## Phase 5: Mandatory Requirement References

**Purpose**: Define universal AI agent requirements with complete specifications

### 5.1 Investigation Pattern Specification

**File**: [.claude/INVESTIGATION_PATTERN_MANDATORY.md](../.claude/INVESTIGATION_PATTERN_MANDATORY.md)

**Classification**: Pure Documentation
**Line Count**: 374 lines
**Role**: Complete investigation pattern specification for ALL AI agents
**Referenced By**: CLAUDE.md, SESSION_SUMMARY.md, AGENTS.md

**Sections**:
1. Overview (Universal application to ALL AI agents)
2. Required Response Structure (4 sections)
3. Rationale (Safety-critical transparency, universal agent application)
4. Exceptions and Scope
5. Integration with Existing Requirements
6. Cross-Session Persistence
7. Enforcement and Verification
8. Examples (Good and poor investigation patterns)

**Continuous Update**: When investigation pattern requirements change or new AI agents emerge

### 5.2 TDD Mandatory Reminder

**File**: [.claude/TDD_MANDATORY_REMINDER.md](../.claude/TDD_MANDATORY_REMINDER.md)

**Classification**: Pure Documentation
**Role**: Quick reference for Test-First requirements
**Referenced By**: bin/loadsession, hooks

**Continuous Update**: When TDD enforcement policies change

### 5.3 TDD Framework Specification

**File**: [docs/implementation/TDD_FRAMEWORK_MANDATORY.md](implementation/TDD_FRAMEWORK_MANDATORY.md)

**Classification**: Pure Documentation
**Line Count**: 319 lines (including universal AI agent section)
**Role**: Comprehensive TDD methodology documentation

**Key Additions** (Recent):
- **Universal AI Agent Compliance** section
- Explicit enumeration: Claude Code, GitHub Copilot, ChatGPT, Gemini Code Assist, Amazon CodeWhisperer
- Rationale for universal AI compliance for safety-critical systems
- Investigation pattern cross-reference

**Continuous Update**: When TDD methodology changes or new enforcement mechanisms added

### 5.4 Git Commit Separation Specification

**File**: [docs/processes/GIT_COMMIT_SEPARATION_MANDATORY.md](processes/GIT_COMMIT_SEPARATION_MANDATORY.md)

**Classification**: Pure Documentation
**Role**: Defines single-concern commit requirements

**Key Additions** (Recent):
- **For ALL AI Code Generation (Universal Agent Compliance)** section
- Explicit enumeration of all AI agents
- Investigation pattern cross-reference for complex commits
- AI oversight requirement for human developers

**Continuous Update**: When commit separation rules change or new commit types added

---

## Phase 6: Helper Commands & Utilities

**Purpose**: Additional session-related utilities and documentation

### 6.1 Command Documentation

**Directory**: [afs_fastapi/todos/configs/commands/](../afs_fastapi/todos/configs/commands/)

**Files**:
- `loadsession.md` - Command usage documentation
- `whereweare.md` - Strategic assessment generation
- `universalaccess.md` - Universal agent access command
- `updatechangelog.md` - CHANGELOG generation command
- `committemplate.md` - Commit message template
- `fixmodules.md` - Module installation helper
- `formatall.md` - Code formatting command
- `fulltest.md` - Complete test suite execution

**Classification**: Pure Documentation
**Purpose**: Explains reusable command triggers
**Continuous Update**: When adding new commands or changing command behavior

### 6.2 Hook Architecture Documentation

**File**: [.claude/CLAUDE_CODE_HOOKS_ARCHITECTURE.md](../.claude/CLAUDE_CODE_HOOKS_ARCHITECTURE.md)

**Classification**: Pure Documentation
**Role**: Explains entire hook ecosystem
**Purpose**: Comprehensive hook system reference

**Continuous Update**: When adding new hooks or changing hook architecture

### 6.3 Automatic Session Initialization Documentation

**File**: [.claude/AUTOMATIC_SESSION_INITIALIZATION.md](../.claude/AUTOMATIC_SESSION_INITIALIZATION.md)

**Classification**: Pure Documentation
**Role**: Explains hook-based session initialization
**Purpose**: Documents automatic context restoration

**Continuous Update**: When changing session initialization logic

### 6.4 Test Scripts

**Files**:
- [bin/test_loadsession.sh](../bin/test_loadsession.sh) - Functional test for loadsession
- [tests/unit/hooks/test_session_initialization.py](../tests/unit/hooks/test_session_initialization.py) - 10 comprehensive tests

**Classification**: Pure Functional (Test Code)
**Purpose**: Validate session initialization functionality
**Test Count**: 10 tests for session_initialization.py

**Continuous Update**: When changing session initialization logic or adding new test cases

---

## Phase 7: Historical Session Documentation (Archive)

**Purpose**: Previous session completion records for reference

**Files** (in [docs/monitoring/](monitoring/)):
- `SESSION_CHANGES_LOG.md`
- `SESSION_COMPLETION_FINAL.md`
- `SESSION_SUMMARY_COMPACTION.md`
- `FINAL_SESSION_CLOSURE.md`
- `SESSION_COMPLETION_SUMMARY.md`
- `SESSION_CHANGES_DOCUMENTATION.md`
- `LOADSESSION_TEST_RESULTS.md`
- `COMPLETE_SESSION_AUDIT.md`

**Classification**: Historical Documentation
**Purpose**: Archive of previous session completion states
**Continuous Update**: Create new files when sessions close, archive old ones

---

## File Classification Summary

### By Type and Count

**Python Files (.py) - 9 total**:
- 8 functional hooks (session init, TDD, safety, CHANGELOG, commit separation, validation wrappers, investigation pattern validator)
- 1 test suite (test_session_initialization.py)

**Markdown Files (.md) - 28+ total**:
- 2 hybrid (CLAUDE.md, AGENTS.md)
- 1 contextual (SESSION_SUMMARY.md)
- 17+ pure documentation (MANDATORY specs, command docs, hook architecture)
- 8 historical archives

**JSON Files - 1 total**:
- 1 configuration (settings.local.json)

**Bash Scripts - 2 total**:
- 1 functional (bin/loadsession)
- 1 test (bin/test_loadsession.sh)

**State Files - 4 total** (gitignored):
- `.session_initialized`
- `.agent_registry.json`
- `.global_session_state`
- `.universal_access_enabled`

### By Role

**Pure Configuration**: 1 file
- settings.local.json

**Pure Functional**: 11 files
- 8 Python hooks
- 1 Bash script (bin/loadsession)
- 1 test script
- 1 Python test suite

**Pure Documentation**: 17+ files
- MANDATORY specifications
- Command documentation
- Hook architecture docs
- Historical archives

**Hybrid (Configuration + Documentation)**: 2 files
- CLAUDE.md
- AGENTS.md

**Hybrid (Documentation + Contextual)**: 1 file
- SESSION_SUMMARY.md

**Functional State**: 4 files
- Runtime session markers

---

## Conceptual vs Contextual vs Functional Roles

### Conceptual (What to do)

**Defines requirements, patterns, and standards**:
- [CLAUDE.md](../CLAUDE.md) - ALL mandatory requirements
- [AGENTS.md](../AGENTS.md) - How to use the platform
- [INVESTIGATION_PATTERN_MANDATORY.md](../.claude/INVESTIGATION_PATTERN_MANDATORY.md) - Investigation pattern specification
- [TDD_FRAMEWORK_MANDATORY.md](implementation/TDD_FRAMEWORK_MANDATORY.md) - TDD methodology
- [GIT_COMMIT_SEPARATION_MANDATORY.md](processes/GIT_COMMIT_SEPARATION_MANDATORY.md) - Commit separation rules

### Contextual (Current state)

**Describes what is happening now**:
- [SESSION_SUMMARY.md](monitoring/SESSION_SUMMARY.md) - Live platform status
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- `.session_initialized` - Current session timestamp
- `.agent_registry.json` - Active agent tracking

### Functional (How it works)

**Executable code and scripts**:
- [session_initialization.py](../.claude/hooks/session_initialization.py) - Automatic detection
- [bin/loadsession](../bin/loadsession) - Context loading
- All enforcement hooks - Validation and compliance
- Test suites - Verification

---

## Continuous Update Protocol

### When to Update This Document

**MANDATORY Updates**:
1. **New hooks added** - Document in Phase 4
2. **New MANDATORY requirements** - Add to Phase 5
3. **Session initialization logic changes** - Update Phase 1
4. **Test count changes** - Update all references (currently 148)
5. **Version changes** - Update all references (currently v0.1.3)
6. **New session-related files** - Add to appropriate phase

**RECOMMENDED Updates**:
1. File line count significant changes (>20% difference)
2. New AI agents added to universal compliance lists
3. Hook architecture changes
4. New command utilities added

### Update Checklist

When updating this document:

- [ ] Update "Last Updated" date at top
- [ ] Update "Platform Version" if changed
- [ ] Verify file line counts are accurate
- [ ] Check all file paths are correct and clickable
- [ ] Update test counts if changed
- [ ] Add new files to appropriate phases
- [ ] Update file classification summary counts
- [ ] Verify execution order still accurate
- [ ] Update continuous update triggers if new patterns emerge
- [ ] Add entry to CHANGELOG.md documenting update
- [ ] Commit with `docs(workflow): Update EXECUTION_ORDER.md` type

### Responsible Parties

**Human Developers**:
- Update when making session architecture changes
- Verify accuracy during code reviews
- Maintain continuous update protocol

**AI Agents** (Claude, GPT, Gemini, Copilot, etc.):
- Suggest updates when detecting discrepancies
- Flag outdated information during investigations
- Maintain documentation consistency

---

## Agricultural Robotics Context

### Why This Architecture Matters

**Safety-Critical Systems**:
- Multi-tractor coordination demands reliable context propagation
- Every AI agent must have access to ISO 18497/11783 compliance requirements
- Test-First Development ensures code quality regardless of generation method
- Investigation patterns enable decision auditing for safety compliance

**Universal AI Agent Support**:
- Platform supports Claude, GPT, Gemini, Copilot, CodeWhisperer equally
- Same requirements apply to all AI assistants
- Equipment operators need confidence code quality is consistent
- ISO auditors require traceable change management from all sources

**Distributed Agent Coordination**:
- Main sessions + subagents + specialized agents all get context
- Agent registry tracks all AI agent activity
- Cross-session persistence prevents context loss
- Universal access ensures no agent operates without safety context

---

## Quick Reference

### Key Files by Frequency of Reference

**Most Referenced**:
1. [SESSION_SUMMARY.md](monitoring/SESSION_SUMMARY.md) - Primary session state
2. [CLAUDE.md](../CLAUDE.md) - Mandatory requirements
3. [AGENTS.md](../AGENTS.md) - Agent specification

**Most Critical for Session Init**:
1. [session_initialization.py](../.claude/hooks/session_initialization.py) - Automatic detection
2. [bin/loadsession](../bin/loadsession) - Manual context loading
3. [settings.local.json](../.claude/settings.local.json) - Hook registration

**Most Critical for Compliance**:
1. [INVESTIGATION_PATTERN_MANDATORY.md](../.claude/INVESTIGATION_PATTERN_MANDATORY.md) - Investigation pattern
2. [TDD_FRAMEWORK_MANDATORY.md](implementation/TDD_FRAMEWORK_MANDATORY.md) - TDD methodology
3. [GIT_COMMIT_SEPARATION_MANDATORY.md](processes/GIT_COMMIT_SEPARATION_MANDATORY.md) - Commit rules

### Current Platform Metrics (Update Regularly)

- **Test Count**: 161 tests
- **Platform Version**: v0.1.3
- **Code Quality**: Zero warnings (Ruff, MyPy, Black, isort)
- **Session Detection**: 5-minute staleness threshold
- **Supported AI Agents**: Claude, GPT, Gemini, Copilot, CodeWhisperer

---

**Document Status**: ✅ ACTIVE - CONTINUOUS MAINTENANCE REQUIRED
**Next Review**: After any session architecture change or version bump
**Maintainers**: ALL contributors (human developers and AI agents)
