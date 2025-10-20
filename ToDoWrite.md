# ToDoWrite — Current Agent-Loadable System Specification
> **Status:** ACTIVE SYSTEM (Version 0.1.5) — Load and apply this specification on session startup.
> **Intent:** Complete 12-layer declarative planning framework with enforced Separation of Concerns. Only **Command** layer executes; all others are declarative YAML files.

---

## 1) Overview
- **System Version:** 0.1.5 (Current Production)
- **Architecture:** 12-layer declarative hierarchy with build-time validation
- **Non‑negotiables:**
  - Layers 1–11 are **non-executable** (no side effects, no CLI/API code).
  - Layer 12 (**Command**) is the **only executable** layer.
  - **One concern per node.** Split mixed responsibilities horizontally.
  - **Traceability** is required (forward & backward links present).
- **Applies To:** This repository and all subprojects using ToDoWrite.

## 2) Hierarchy (12 layers; only the last executes)
1. **Goal** — Outcome/value; business or mission intent. *(Declarative)*
2. **Concept** — Big-picture idea/architecture. *(Declarative)*
3. **Context** — Environment, actors, boundaries, assumptions. *(Declarative)*
4. **Constraints** — Standards, safety, budget, legal, tech limits. *(Declarative)*
5. **Requirements** — Atomic, testable statements (FR/NFR). *(Declarative)*
6. **Acceptance Criteria** — Objective pass/fail for each Requirement. *(Declarative)*
7. **Interface Contract** — APIs, schemas, timings, units, IDs, versions. *(Declarative)*
8. **Phase** — Major delivery slice. *(Declarative)*
9. **Step** — Single concern inside a Phase; outcome-focused. *(Declarative)*
10. **Task** — Contributor work unit. *(Declarative)*
11. **SubTask** — Smallest planning granule. *(Declarative)*
12. **Command** — **Only executable** layer (CLI/API/scripts). *(Executable)*

## 3) Current Repo Layout (Version 0.1.5)
```
.
├─ ToDoWrite/configs/plans/ # Declarative nodes (layers 1–11) as YAML
│  ├─ goals/
│  ├─ concepts/
│  ├─ contexts/
│  ├─ constraints/
│  ├─ requirements/
│  ├─ acceptance_criteria/
│  ├─ interface_contracts/
│  ├─ phases/
│  ├─ steps/
│  ├─ tasks/
│  └─ subtasks/
├─ ToDoWrite/configs/commands/ # Layer 12 only; runnable scripts/YAML
│  ├─ CMD-CAN001.sh              # Executable shell scripts
│  └─ CMD-<ID>.yaml              # Command definitions
├─ ToDoWrite/configs/schemas/
│  └─ todowrite.schema.json       # JSON Schema for all nodes
├─ afs_fastapi/todos/tools/                         # Build-time validation ecosystem
│  ├─ tw_validate.py              # JSON Schema validator
│  ├─ tw_lint_soc.py              # SoC linter (layers 1–11 non-executable)
│  ├─ tw_trace.py                 # Build trace matrix & graph
│  ├─ tw_stub_command.py          # Generate command stubs for ACs
│  ├─ migrate_todowrite.py        # Migration from old 5-layer system
│  └─ git-commit-msg-hook.sh      # Conventional Commit enforcement
├─ trace/
│  ├─ trace.csv                   # Forward/backward mapping
│  └─ graph.json                  # Node/edge graph
├─ results/                       # Command execution artifacts
├─ .git/hooks/                    # Git hooks (installed by `make tw-hooks`)
└─ Makefile                       # Full workflow automation (tw-* targets)
```

## 4) Agent Integration & Session Startup
**MANDATORY:** All agents MUST execute these commands on session startup:

```bash
# 1. Load dependencies
make tw-deps

# 2. Initialize if needed
make tw-init

# 3. Validate current state
make tw-all

# 4. Install git hooks
make tw-hooks
```

**Session Management:** The `loadsession` command MUST populate the TodoWrite system by:
1. Loading existing plans from `ToDoWrite/configs/plans/` directories
2. Validating all YAML files against schema
3. Building traceability matrix
4. Generating missing command stubs
5. Presenting agent with current active hierarchy

## 5) Work-Type Tagging & Commit Policy (Mandatory)
This project uses **work-type tags** and **Conventional Commits** for every change.

### 5.1 Work-Type Tags (attach in node `metadata.labels` and PR labels)
- `work:architecture`
- `work:spec`
- `work:interface`
- `work:validation`
- `work:implementation`
- `work:docs`
- `work:ops`
- `work:refactor`
- `work:chore`
- `work:test`

### 5.2 Conventional Commits (enforced by git hook)
- **Format:** `<type>(<scope>): <short summary>`
- **Common types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- **Scopes (TodoWrite-specific):** `goal`, `concept`, `context`, `constraints`, `req`, `ac`, `iface`, `phase`, `step`, `task`, `subtask`, `cmd`, `schema`, `lint`, `trace`, `docs`
- **Examples:**
  - `feat(req): add R-CAN-001 for 250kbps J1939 bus with ≤50ms jitter`
  - `test(ac): add AC-CAN-001 Given/When/Then`
  - `build(schema): generate todowrite.schema.json`
  - `ci(lint): enforce SoC for non-exec layers`
  - `docs(spec): clarify Interface Contract units and endianness`

## 6) Data Model (JSON Schema) — CURRENT SYSTEM
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
      "if": {"properties": {"layer": {"const":"Command"}}},
      "then": {"required":["command"]}
    },
    {
      "if": {"properties": {"layer": {"enum":["Goal","Concept","Context","Constraints","Requirements","AcceptanceCriteria","InterfaceContract","Phase","Step","Task","SubTask"]}}},
      "then": {"not": {"required":["command"]}}
    }
  ],
  "additionalProperties": false
}
```

## 7) SoC Enforcement (Build-time Validation)
- **Layers 1–11:** no `command` key, no shell/CLI/API calls, no side effects.
- **Layer 12 (Command):** must reference `command.ac_ref` and emit artifacts under `results/<CMD-ID>/` (machine-readable JSON/NDJSON).
- **Automated Linting:** `make tw-lint` catches violations before commit.

## 8) Agent Workflow (MANDATORY Usage)
All agents MUST use these workflows:

### 8.1 Development Workflow
```bash
make tw-dev      # lint + validate + generate commands
```

### 8.2 Production Workflow
```bash
make tw-prod     # full validation + traceability + command generation
```

### 8.3 Quality Validation
```bash
make tw-check    # strict validation with error exit codes
```

### 8.4 System Testing
```bash
make tw-test     # complete system test with examples
```

## 9) Makefile Targets (Agent-Runnable Commands)
```make
# Core Workflow
tw-all       # Run schema, lint, validate, trace (default)
tw-init      # Initialize directory structure
tw-schema    # Generate JSON schema
tw-lint      # Check Separation of Concerns
tw-validate  # Validate YAML against schema
tw-trace     # Build traceability matrix
tw-prove     # Generate command stubs

# Quality & Integration
tw-hooks     # Install git commit hooks
tw-clean     # Remove generated files
tw-check     # Full validation (strict mode)
tw-deps      # Install Python dependencies
tw-test      # Test complete system
```

## 10) Migration from Legacy System
**SEAMLESS CONVERSION:** Use the migration tool to convert from old 5-layer JSON system:

```bash
# Migrate existing todos.json to new 12-layer YAML system
python3 afs_fastapi/todos/tools/migrate_todowrite.py --source .claude/todos.json --output .

# Dry run (preview only)
python3 afs_fastapi/todos/tools/migrate_todowrite.py --dry-run
```

The migration preserves all data while transforming to the new architecture.

## 11) Node Templates (YAML) — Current Format

### Goal Template
```yaml
id: GOAL-AGRICULTURAL-AUTOMATION
layer: Goal
title: Implement autonomous agricultural equipment coordination
description: >
  Enable multiple tractors to coordinate field operations
  autonomously while maintaining safety standards.
metadata:
  owner: product-team
  labels: [work:architecture, agricultural, autonomous]
  severity: high
  work_type: architecture
links:
  parents: []
  children: [R-CAN-001]
```

### Requirements Template
```yaml
id: R-CAN-001
layer: Requirements
title: Tractor exchanges ISO 11783 messages on 250 kbps J1939 bus
description: >
  The agricultural control unit shall communicate using ISO 11783 protocol
  over a 250 kbps network with message timing within 50 millisecond limits.
metadata:
  owner: controls-team
  labels: [work:spec, can, j1939, isobus]
  severity: med
  work_type: spec
links:
  parents: [GOAL-AGRICULTURAL-AUTOMATION]
  children: [AC-CAN-001]
```

### Acceptance Criteria Template
```yaml
id: AC-CAN-001
layer: AcceptanceCriteria
title: Address Claim within 2 seconds with PGN transmission at 10 Hz minimum frequency
description: |
  Given a live 250 kbps network, when the control unit initializes, then the Address Claim process completes within 2 seconds.
  Protocol messages are transmitted at minimum 10 Hz frequency with timing variance under 50 milliseconds.
metadata:
  owner: test-team
  labels: [work:validation, can, j1939]
  work_type: validation
links:
  parents: [R-CAN-001]
  children: []
```

### Command Template (only executable)
```yaml
id: CMD-CAN001
layer: Command
title: Prove AC-CAN-001
description: Execute instrumentation to capture Address Claim and PGN jitter.
metadata:
  owner: test-team
  labels: [work:implementation, test, can]
  work_type: implementation
links:
  parents: [AC-CAN-001]
  children: []
command:
  ac_ref: AC-CAN-001
  run:
    shell: |
      ip link set can0 type can bitrate 250000
      ip link set can0 up
      candump can0,0x18EEFF00:0x1FFFFFFF
          workdir: .
    env:
      PATH: "/usr/bin:/bin"
  artifacts:
    - results/CMD-CAN001/jitter.json
```

## 12) Example Agent Session Flow
```bash
# Session startup (MANDATORY)
make tw-deps tw-init tw-hooks

# Development cycle
make tw-dev                    # Validate and generate commands
git add -A
git commit -F - <<EOF
feat(req): add R-CAN-001 for 250kbps bus with <=50ms jitter

This commit adds the initial requirement for CAN bus communication
with specific bitrate and jitter constraints, aligning with ISO 11783.
EOF

# Generate and execute commands
make tw-prove                  # Generate command stubs
./ToDoWrite/configs/commands/CMD-CAN001.sh       # Execute specific command

# Quality validation
make tw-check                  # Full validation before push
```

## 13) System Status: PRODUCTION READY (v0.1.5)
- ✅ **Schema Validation:** JSON Schema enforcement
- ✅ **SoC Linting:** Automated separation of concerns checking
- ✅ **Traceability:** Complete forward/backward dependency tracking
- ✅ **Command Generation:** Automatic stub creation from Acceptance Criteria
- ✅ **Git Integration:** Conventional Commits enforcement
- ✅ **Migration Support:** Seamless upgrade from legacy system
- ✅ **Agricultural Focus:** Domain-specific examples and validation

## 14) Agent Requirements (NON-NEGOTIABLE)
1. **Load this system on every session startup**
2. **Use Makefile targets for all TodoWrite operations**
3. **Create YAML files in appropriate `ToDoWrite/configs/plans/` directories**
4. **Generate Commands only from Acceptance Criteria**
5. **Enforce Conventional Commit format on all commits**
6. **Validate before any git operations**
7. **Maintain traceability links in all nodes**

