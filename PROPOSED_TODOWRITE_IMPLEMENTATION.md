# ToDoWrite — Agent-Loadable Instruction Spec
> **Usage:** Load this file with `load and apply ToDoWrite.md` (Claude Code).  
> **Intent:** Provide a complete, enforceable system that decomposes high-level goals into **executable Commands** while guaranteeing **Separation of Concerns** (SoC). Only **Command** executes; all other layers are declarative.

---

## 1) Overview
- **Spec Version:** 2.2
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

## 3) Repo Layout (create if missing)
```
. 
├─ ToDoWrite/configs/plans/                         # Declarative nodes (layers 1–11) as YAML
│  ├─ goals/
│  ├─ concepts/
│  ├─ contexts/
│  ├─ constraints/                # contains preserved constraints files
│  ├─ requirements/
│  ├─ acceptance_criteria/
│  ├─ interface_contracts/
│  ├─ phases/
│  ├─ steps/
│  ├─ tasks/
│  └─ subtasks/
├─ ToDoWrite/configs/commands/                      # Layer 12 only; runnable scripts/runbooks
│  ├─ CMD-CAN-AC001.sh
│  └─ CMD-<ID>.sh
├─ ToDoWrite/configs/schemas/
│  └─ todowrite.schema.json       # JSON Schema for all nodes
├─ afs_fastapi/todos/tools/                         # Build-time validation ecosystem
│  ├─ tw_lint_soc.py              # SoC linter (layers 1–11 non-executable)
│  ├─ tw_validate.py              # JSON Schema validator
│  ├─ tw_trace.py                 # Build trace matrix & graph
│  ├─ tw_stub_command.py          # Generate command stubs for ACs
│  └─ commitlint.config.cjs       # Conventional Commit lint config
├─ trace/
│  ├─ trace.csv                   # Forward/backward mapping
│  └─ graph.json                  # Node/edge graph
├─ results/                       # Command artifacts
├─ .git/hooks/                    # Local hooks (installed by `make hooks`)
├─ .commitlintrc.yml              # Optional commitlint
└─ Makefile```

## 4) Work-Type Tagging & Commit Policy (Mandatory)
This project uses **work-type tags** and **Conventional Commits** for every change.

### 4.1 Work-Type Tags (attach in node `metadata.labels` and PR labels)
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

### 4.2 Conventional Commits (enforced)
- **Format:** `<type>(<scope>): <short summary>`
- **Common types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- **Scopes (suggested):** `goal`, `concept`, `context`, `constraints`, `req`, `ac`, `iface`, `phase`, `step`, `task`, `subtask`, `cmd`, `schema`, `lint`, `trace`, `docs`
- **Examples:**
  - `feat(req): add R-CAN-001 for 250kbps J1939 bus with ≤50ms jitter`
  - `test(ac): add AC-CAN-001 Given/When/Then`
  - `build(schema): generate todowrite.schema.json`
  - `ci(lint): enforce SoC for non-exec layers`
  - `docs(spec): clarify Interface Contract units and endianness`
- **Footers (when applicable):** `BREAKING CHANGE: <description>` or issue refs `Refs: #123`

## 5) Data Model (JSON Schema)
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

## 6) SoC Enforcement
- **Layers 1–11:** no `command` key, no shell/CLI/API calls, no side effects.
- **Layer 12 (Command):** must reference `command.ac_ref` and emit artifacts under `results/<CMD-ID>/` (machine-readable JSON/NDJSON).

## 7) Makefile Targets (agent may run these)
```make
.PHONY: all init schema lint validate trace prove hooks commitcheck

all: schema lint validate trace

init:
	mkdir -p ToDoWrite/configs/plans/{goals,concepts,contexts,constraints,requirements,acceptance_criteria,interface_contracts,phases,steps,tasks,subtasks} ToDoWrite/configs/commands ToDoWrite/configs/schemas tools trace results
	@echo "Initialized ToDoWrite layout."

schema:
	@python3 afs_fastapi/todos/tools/tw_validate.py --write-schema ToDoWrite/configs/schemas/todowrite.schema.json

lint:
	@python3 afs_fastapi/todos/tools/tw_lint_soc.py --plans ToDoWrite/configs/plans --report trace/lint_report.json

validate:
	@python3 afs_fastapi/todos/tools/tw_validate.py --plans ToDoWrite/configs/plans --schema ToDoWrite/configs/schemas/todowrite.schema.json

trace:
	@python3 afs_fastapi/todos/tools/tw_trace.py --plans ToDoWrite/configs/plans --out-csv trace/trace.csv --out-graph trace/graph.json

prove:
	@python3 afs_fastapi/todos/tools/tw_stub_command.py --acs ToDoWrite/configs/plans/acceptance_criteria --out ToDoWrite/configs/commands

hooks:
	@chmod +x afs_fastapi/todos/tools/git-commit-msg-hook.sh || true
	@ln -sf ../../afs_fastapi/todos/tools/git-commit-msg-hook.sh .git/hooks/commit-msg
	@echo "Local commit-msg hook installed."

commitcheck:
	@afs_fastapi/todos/tools/git-commit-msg-hook.sh --check
```

## 8) Git Commit Message Policy (Conventional + Semantic)
**Every commit MUST follow Conventional Commits and be semantically meaningful.**

- **Type**: `feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`
- **Scope**: one of `goal|concept|context|constraints|req|ac|iface|phase|step|task|subtask|cmd|schema|lint|trace|docs`
- **Summary**: concise, imperative
- **Body**: rationale/context
- **Footer**: `BREAKING CHANGE:` and/or `Refs: #id`

**Examples**
- `feat(req): add R-CAN-001 for 250kbps J1939 bus`
- `test(ac): add AC-CAN-001 Given/When/Then`
- `ci(lint): block non-exec content in layers 1–11`
- `build(schema): generate todowrite.schema.json`
- `docs(cmd): document CMD-CAN-AC001 artifacts`

### Commit Hook (afs_fastapi/todos/tools/git-commit-msg-hook.sh)
```bash
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--check" ]]; then
  msg_file=".git/COMMIT_EDITMSG"
else
  msg_file="${1:-.git/COMMIT_EDITMSG}"
fi
msg="$(cat "$msg_file" || true)"
regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)\((goal|concept|context|constraints|req|ac|iface|phase|step|task|subtask|cmd|schema|lint|trace|docs)\):\s.+'
if ! echo "$msg" | head -n1 | grep -Eq "$regex"; then
  echo "✖ Commit message must match Conventional Commits with an allowed scope."
  echo "  Example: feat(req): add R-CAN-001 for 250kbps J1939 bus"
  exit 1
fi
echo "✔ Conventional Commit format OK"
```

## 9) Agent Runbook (Claude Code MUST perform)
1. Initialize layout → `make init`
2. Generate/refresh schema → `make schema`
3. Lint SoC → `make lint`
4. Validate plans → `make validate`
5. Build traceability → `make trace`
6. Stub commands for pending ACs → `make prove`
7. Install commit hook → `make hooks`
8. Enforce commit policy on each commit

## 10) Node Templates (YAML)

### Requirement
```yaml
id: R-CAN-001
layer: Requirements
title: Tractor exchanges ISO 11783 messages on a 250 kbps J1939 bus
description: >
  The ECU shall communicate using ISO 11783 PGNs over a 250 kbps J1939 CAN bus with ≤ 50 ms jitter.
metadata:
  owner: controls-team
  labels: [work:spec, can, j1939, isobus]
  severity: med
  work_type: spec
links:
  parents: [CTX-OPER-ENV, CON-ARCH-ECU]
  children: [AC-CAN-001]
```

### Acceptance Criteria
```yaml
id: AC-CAN-001
layer: AcceptanceCriteria
title: Address Claim ≤ 2 s; PGN 65280 at ≥ 10 Hz; jitter ≤ 50 ms (95th pct)
description: |
  Given a live 250 kbps bus, when ECU boots, then Address Claim completes ≤ 2 s.
  PGN 65280 is observed at ≥ 10 Hz with jitter ≤ 50 ms (95th percentile).
metadata:
  owner: test-team
  labels: [work:validation, can, j1939]
  work_type: validation
links:
  parents: [R-CAN-001]
  children: [CMD-CAN-AC001]
```

### Interface Contract
```yaml
id: IF-CAN
layer: InterfaceContract
title: CAN bus parameters and PGN encodings
description: >
  Bitrate 250000; termination 120 Ω ends; PGNs; byte layouts; units; endianness.
metadata:
  owner: interface-team
  labels: [work:interface, isobus, j1939]
  work_type: interface
links:
  parents: [R-CAN-001]
  children: []
```

### Command (only executable)
```yaml
id: CMD-CAN-AC001
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
    - results/CMD-CAN-AC001/jitter.json
```

## 11) Example Developer Flow
```bash
make init
make schema
make lint validate trace
git add -A
git commit -F - <<EOF
feat(req): add R-CAN-001 for 250kbps bus with <=50ms jitter

This commit adds the initial requirement for CAN bus communication
with specific bitrate and jitter constraints, aligning with ISO 11783.
EOF
make prove
git add -A
git commit -F - <<EOF
feat(cmd): implement CMD-CAN-AC001 to prove AC-CAN-001

This commit implements the command to prove the acceptance criteria
for CAN bus communication, including instrumentation for jitter measurement.
EOF
```

## 12) Old → New Mapping
- Goal → Goal *(unchanged)*
- Phase → Phase *(unchanged)*
- Step → Step *(unchanged)*
- Task → Task *(unchanged)*
- SubTask → SubTask *(unchanged)*
- **Added:** Concept, Context, Constraints, Requirements, Acceptance Criteria, Interface Contract, **Command** (executable).

## 13) Constraints (Preserved Verbatim)
_No original constraints section detected; add constraints as layer 4 content here to bind the system._

## 14) Guardrails Recap
- Only **Command** executes.
- One concern per node.
- Enforce traceability.
- Enforce commit policy with type+scope tags.
