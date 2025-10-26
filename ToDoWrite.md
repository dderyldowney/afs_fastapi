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

## 2.1) Complete Layer Architecture & Storage Mapping

### 📋 Layers 1-11: Declarative (Non-Executable)
*Stored in `ToDoWrite/configs/plans/`*

| Layer | Name | Purpose | Storage Directory |
|-------|------|---------|------------------|
| 1 | **Goal** | Business/mission intent | `goals/` |
| 2 | **Concept** | Architectural approaches | `concepts/` |
| 3 | **Context** | Environment & assumptions | `contexts/` |
| 4 | **Constraints** | Standards & legal limits | `constraints/` |
| 5 | **Requirements** | Atomic specifications | `requirements/` |
| 6 | **Acceptance Criteria** | Pass/fail conditions | `acceptance_criteria/` |
| 7 | **Interface Contract** | APIs & protocols | `interface_contracts/` |
| 8 | **Phase** | Major delivery slices | `phases/` |
| 9 | **Step** | Single-concern work units | `steps/` |
| 10 | **Task** | Contributor work assignments | `tasks/` |
| 11 | **SubTask** | Smallest planning units | `subtasks/` |

### ⚡ Layer 12: Executable
*Stored in `ToDoWrite/configs/commands/`*

| Layer | Name | Purpose | Storage Directory |
|-------|------|---------|------------------|
| 12 | **Command** | **ONLY** executable layer | `commands/` |

## 2.2) Functional Groupings of the 12-Layer Hierarchy

To facilitate understanding and interaction for AI agents, the 12-layer hierarchy is grouped by functional role, ensuring clarity in purpose, agent interaction, and expected outputs for effective task decomposition and execution.

### I. Strategic & High-Level Planning (Layers 1-4)
These layers define the overarching vision, architectural concepts, environmental context, and limiting factors for the project. They are purely declarative and guide all subsequent layers.

*   **1. Goal**
    *   **Purpose:** Defines the ultimate outcome, value, or business/mission intent. It answers "Why are we doing this?"
    *   **Agent Interaction:** Agents should read Goals to understand the high-level objective. When proposing new work, agents must link it to an existing Goal. New Goals are created at the project's inception or when a significant new strategic direction is adopted.
    *   **Expected Outputs:** A clear, concise YAML definition of the Goal, linked to higher-level visions (if applicable) and lower-level Concepts or Requirements. Verifiable by its alignment with project vision and stakeholder needs.

*   **2. Concept**
    *   **Purpose:** Outlines big-picture ideas, architectural approaches, or fundamental principles that support a Goal. It answers "What is the high-level approach?"
    *   **Agent Interaction:** Agents refer to Concepts to understand the chosen architectural patterns or major design decisions. New Concepts are typically derived from Goals and inform Contexts and Constraints.
    *   **Expected Outputs:** A declarative YAML file describing the architectural concept, linked to its parent Goal and child Contexts/Constraints. Verifiable by its logical coherence and alignment with the Goal.

*   **3. Context**
    *   **Purpose:** Describes the environment, involved actors, system boundaries, and underlying assumptions. It answers "What is the operational environment and who/what is involved?"
    *   **Agent Interaction:** Agents use Contexts to understand the operational landscape, external dependencies, and implicit assumptions. This layer is critical for identifying potential risks and informing Constraints.
    *   **Expected Outputs:** A declarative YAML file detailing environmental factors, actors, system scope, and assumptions, linked to parent Concepts and child Constraints. Verifiable by its completeness and accuracy in describing the operational reality.

*   **4. Constraints**
    *   **Purpose:** Specifies standards, safety regulations, budget limitations, legal requirements, and technological boundaries. It answers "What are the non-negotiable limitations and rules?"
    *   **Agent Interaction:** Agents *must* adhere to all defined Constraints. This layer acts as a critical filter for all subsequent design and implementation decisions. Agents should reference Constraints when evaluating solutions or identifying risks.
    *   **Expected Outputs:** A declarative YAML file listing all applicable constraints, linked to parent Contexts and informing Requirements. Verifiable by its adherence to external regulations and internal policies.

### II. Specification & Definition (Layers 5-7)
These layers translate high-level planning into concrete, testable specifications that define what needs to be built and how its success will be measured.

*   **5. Requirements**
    *   **Purpose:** Defines atomic, testable statements of what the system must do (Functional Requirements) or how well it must perform (Non-Functional Requirements). It answers "What exactly must the system achieve?"
    *   **Agent Interaction:** Agents create Requirements based on Goals, Concepts, Contexts, and Constraints. All implementation work (Tasks, SubTasks) must trace back to one or more Requirements. Agents use Requirements to guide the creation of Acceptance Criteria.
    *   **Expected Outputs:** Declarative YAML files, each containing a single, unambiguous, and testable requirement, linked to parent Constraints/Goals and child Acceptance Criteria. Verifiable by its clarity, testability, and traceability.

*   **6. Acceptance Criteria**
    *   **Purpose:** Provides objective, measurable pass/fail conditions for each Requirement. It answers "How will we know if the Requirement is met?"
    *   **Agent Interaction:** Agents develop Acceptance Criteria for each Requirement. These criteria directly inform the creation of executable Commands (Layer 12) and serve as the basis for testing and validation.
    *   **Expected Outputs:** Declarative YAML files, each defining clear, measurable conditions for a specific Requirement, linked to its parent Requirement and child Commands. Verifiable by its objectivity and direct correlation to the Requirement.

*   **7. Interface Contract**
    *   **Purpose:** Specifies APIs, communication protocols, data schemas, timing requirements, units of measurement, unique identifiers, and versioning for system interfaces. It answers "How do system components interact?"
    *   **Agent Interaction:** Agents refer to Interface Contracts when designing or implementing interactions between system components. This layer ensures interoperability and consistency.
    *   **Expected Outputs:** Declarative YAML files detailing interface specifications, linked to relevant Requirements and informing implementation details in lower layers. Verifiable by its completeness, consistency, and adherence to established protocols.

### III. Work Breakdown & Granular Units (Layers 8-11)
These layers break down the specified work into manageable units for planning, assignment, and tracking, leading towards concrete implementation.

*   **8. Phase**
    *   **Purpose:** Represents a major delivery slice or significant milestone within the project. It answers "What are the major stages of development?"
    *   **Agent Interaction:** Agents use Phases to organize large bodies of work. Progress through Phases is typically managed through the overall todo system, with Steps and Tasks being created within the context of an active Phase.
    *   **Expected Outputs:** A declarative YAML file defining a major stage of work, linked to parent Interface Contracts/Requirements and child Steps. Verifiable by the completion of all its constituent Steps.

*   **9. Step**
    *   **Purpose:** A single-concern unit of work within a Phase, focused on achieving a specific outcome. It answers "What is a distinct, outcome-focused part of this Phase?"
    *   **Agent Interaction:** Agents create Steps within an active Phase. Steps are activated to define the current focus of work. Tasks are then created under an active Step.
    *   **Expected Outputs:** A declarative YAML file defining a single, outcome-oriented work unit, linked to its parent Phase and child Tasks. Verifiable by the completion of all its constituent Tasks.

*   **10. Task**
    *   **Purpose:** Represents a contributor's work unit, typically assigned to an individual or a small team. It answers "What specific work needs to be done by a contributor?"
    *   **Agent Interaction:** Agents create Tasks under an active Step. Tasks are the primary unit of work assignment and progress tracking for individual contributors. SubTasks are created to break down complex Tasks.
    *   **Expected Outputs:** A declarative YAML file defining a specific work item, linked to its parent Step and child SubTasks. Verifiable by the completion of all its constituent SubTasks.

*   **11. SubTask**
    *   **Purpose:** The smallest planning granule, breaking down a Task into highly granular, actionable items. It answers "What are the smallest actionable pieces of work?"
    *   **Agent Interaction:** Agents create SubTasks under an active Task. SubTasks are often directly associated with specific code changes, documentation updates, or the execution of Commands.
    *   **Expected Outputs:** A declarative YAML file defining a highly granular work item, linked to its parent Task and potentially to a Command. Verifiable by its direct completion or the successful execution of an associated Command.

### IV. Execution (Layer 12)
This is the only executable layer, responsible for performing actions and generating verifiable artifacts.

*   **12. Command**
    *   **Purpose:** The *only executable* layer. It defines specific CLI commands, API calls, or scripts that perform actions and generate verifiable outputs. It answers "How is the work actually performed and verified?"
    *   **Agent Interaction:** Agents generate Commands from Acceptance Criteria or SubTasks. Agents *execute* Commands. The output of a Command is critical for verifying the completion of higher-level layers.
    *   **Expected Outputs:** An executable script or command definition (e.g., `.sh`, `.py`, `.yaml` with `run` block), linked to its parent Acceptance Criteria or SubTask. The execution of a Command should produce verifiable artifacts (e.g., test reports, log files, data outputs) that confirm the successful completion of the intended action. Verifiable by the successful execution and the integrity of its generated artifacts.

### 📋 **Functional Groupings Summary**

#### **I. Strategic & High-Level Planning (Layers 1-4)**
- **Purpose**: Define vision, architecture, environment, and constraints
- **Interaction**: Guide all subsequent layers but never execute

#### **II. Specification & Definition (Layers 5-7)**
- **Purpose**: Translate strategy into concrete, testable specifications
- **Interaction**: Bridge between strategic vision and work breakdown

#### **III. Work Breakdown & Granular Units (Layers 8-11)**
- **Purpose**: Break specifications into manageable work units
- **Interaction**: Organize and track development progress

#### **IV. Execution (Layer 12)**
- **Purpose**: **Only layer that executes** - generates verifiable artifacts
- **Interaction**: Transforms all planning into actionable results

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

## 13) Architectural Insights & Design Principles

### 🏗️ **Separation of Concerns Architecture**
- **11+1 Structure**: The 11 declarative + 1 executable design enforces pure separation - planning layers cannot execute code, ensuring clean architectural boundaries
- **Filesystem Safety**: Physical separation (`plans/` vs `commands/`) prevents accidental execution of declarative content, a critical safety feature for agricultural robotics
- **Traceability Chain**: Each layer links to parents/children, creating an unbroken chain from business goal (Layer 1) to executable command (Layer 12)

### 🚜 **Agricultural Robotics Focus**
- **Safety-Critical Systems**: The structured approach ensures every agricultural feature traces from strategic business goal down to verified executable implementation
- **Multi-Tractor Coordination**: Framework supports complex fleet operations with safety compliance and performance optimization
- **Standards Compliance**: Built-in support for ISO 11783, J1939 CAN bus protocols, and agricultural safety standards

### 📊 **Quality Assurance**
- **Build-Time Validation**: Automated schema validation and SoC linting prevent violations before commit
- **Conventional Commits**: Enforced commit message format with ToDoWrite-specific scopes
- **End-to-End Traceability**: Complete forward/backward dependency tracking from goals to commands

## 14) System Status: PRODUCTION READY (v0.1.5)

### ✅ **Core Functionality**
- **Schema Validation:** JSON Schema enforcement with agricultural domain examples
- **SoC Linting:** Automated separation of concerns checking
- **Traceability:** Complete forward/backward dependency tracking
- **Command Generation:** Automatic stub creation from Acceptance Criteria
- **Git Integration:** Conventional Commits enforcement with ToDoWrite scopes

### ✅ **Current Implementation State**
- **11 Declarative Directories**: All planning layers initialized in `ToDoWrite/configs/plans/`
- **1 Executable Directory**: Commands layer ready in `ToDoWrite/configs/commands/`
- **Example Content**: Agricultural CAN bus workflow populated (GOAL-AGRICULTURAL-AUTOMATION → R-CAN-001 → AC-CAN-001)
- **Makefile Integration**: All `tw-*` targets functional for development workflow

### ✅ **Agricultural Examples Ready**
- **CAN Bus Communication**: ISO 11783 over 250 kbps J1939 with ≤50ms jitter
- **Address Claim Protocol**: ≤2s initialization with performance validation
- **Multi-Tractor Coordination**: Fleet operations with safety standards
- **Migration Support:** Seamless upgrade from legacy system

## 15) Agent Requirements (NON-NEGOTIABLE)
1. **Load this system on every session startup**
2. **Use Makefile targets for all TodoWrite operations**
3. **Create YAML files in appropriate `ToDoWrite/configs/plans/` directories**
4. **Generate Commands only from Acceptance Criteria**
5. **Enforce Conventional Commit format on all commits**
6. **Validate before any git operations**
7. **Maintain traceability links in all nodes**

