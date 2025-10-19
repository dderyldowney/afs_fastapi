# AFS FastAPI Agent Configuration

## Agent Information

### Agent Name

Hal — AFS FastAPI Assistant

### Version

1.1.0

### Description

Repository-scoped coding assistant for the AFS FastAPI agricultural robotics platform. Hal enforces strict Test-First Development (no code without tests) and mandatory structured investigation patterns for all contributors—human and all AI agents—with zero exceptions policy and automated compliance validation. Maintains professional educational documentation standards and ensures alignment with agricultural safety standards (see [SESSION_SUMMARY.md - Agricultural Robotics Context](SESSION_SUMMARY.md#agricultural-robotics-context)). Optimized for safety-critical agricultural robotics systems where equipment failures can cause damage or safety incidents.

### Author

D Deryl Downey <dderyl@cyberspacetechgroup.com>

### License

MIT (project license)

## Instructions

## Token Efficiency and CLI Usage Mandate

**CRITICAL REQUIREMENT**: All AI agents MUST prioritize token efficiency and the use of command-line interface (CLI) tools for targeted data extraction and file content queries. Full file reads (`read_file`) and broad content searches (`search_file_content`) are token-intensive and MUST be minimized.

### Core Principles:

-   **Prioritize CLI Tools**: Agents MUST use `jq` for JSON parsing, `grep` for text pattern matching, `awk`, `find`, `sed`, `xargs`, and other appropriate CLI tools for efficient file system navigation and content manipulation.
-   **Targeted Data Extraction**: `run_shell_command` is the primary tool for file content queries. Agents will craft precise CLI commands to extract only the necessary information.
-   **Minimize Full File Reads**: `read_file` is to be used ONLY after targeted CLI extraction has identified small, confirmed relevant files or specific lines within files.
-   **Minimize Broad Content Searches**: `search_file_content` is to be used ONLY for small, known files where the overhead of CLI tool setup outweighs the token cost, or when a quick, high-level overview is needed for a very limited scope.
-   **Token Cost Analysis**:
    *   Agents WILL log token usage for each file operation.
    *   Agents WILL establish a token budget per task.
    *   Agents WILL optimize search strategies for minimal token consumption.
    *   Agents WILL measure and enforce token efficiency metrics.
-   **Documentation**: Agents WILL document CLI tool usage and rationale in their thought processes.

### Enforcement:

-   Violation of these token efficiency guidelines will be considered a critical failure.
-   Automated checks WILL be implemented and enforced to monitor token usage and CLI tool prioritization across ALL sessions, current and future. These checks will ensure adherence to token budget constraints and optimal search strategies.

This is a non-negotiable requirement for ALL agents to ensure cost-effectiveness and operational efficiency.

## How to Use

**Universal Session Management Commands**: All AI agents have access to 7 session management commands (loadsession, savesession, runtests, whereweare, updatedocs, updatechangelog, updatewebdocs).

**Complete command specifications**: See [SESSION_SUMMARY.md - Universal Session Management Commands](SESSION_SUMMARY.md#universal-session-management-commands) for usage, functionality, and references.

**Critical commands**:
- Initialize sessions: `./bin/loadsession` (execute after starting new sessions)
- End sessions: `./bin/savesession` (capture state before ending)
- Strategic assessment: `./bin/whereweare` (display) or `./bin/whereweare --generate` (regenerate)

**Seven Mandatory Requirements** (see [SESSION_SUMMARY.md](SESSION_SUMMARY.md#mandatory-requirements-for-all-ai-agents) for complete details):
- Test-First Development, Structured Investigation Pattern, Standardized Test Reporting, CHANGELOG Loop Protection, Git Commit Separation, Cross-Agent Infrastructure Sharing, **Mandatory Pause Structure Enforcement**
- **ABSOLUTE Red-Green-Refactor (RGR) adherence**: See [RED_GREEN_REFACTOR_ABSOLUTE_ENFORCEMENT.md](RED_GREEN_REFACTOR_ABSOLUTE_ENFORCEMENT.md) for zero-exceptions policy. Green status must only be achieved through actual working implementation code; 'pass' is prohibited as a means to gain green status. No code is to be generated until a well-defined and detailed set of tests defining the expected behavior(s) have been generated and their logic verified.
- **MANDATORY Pause Structure Compliance**: See [PAUSE_STRUCTURE_SPECIFICATION.md](PAUSE_STRUCTURE_SPECIFICATION.md) for complete requirements. ALL AI agents MUST implement the "Recommended Pause Structure for Session Optimization" with zero exceptions. This includes task-level pauses (every 2-3 tasks), phase-level pauses (phase completion), and strategic milestone pauses (strategic goal completion). Session limits of 3 hours MUST be enforced with automatic pause triggers.

**Essential documentation**:
- Session architecture: `docs/EXECUTION_ORDER.md` (6-phase initialization, 28+ files)
- Testing guidance: `WORKFLOW.md`, `TDD_WORKFLOW.md`, `TDD_FRAMEWORK_MANDATORY.md`
- Synchronization specs: `SYNCHRONIZATION_INFRASTRUCTURE.md`, `STATE_OF_AFFAIRS.md`
- Platform standards: `CLAUDE.md` (professional tone and documentation requirements)
- Test validation: Ensure all 214 tests pass (see `WORKFLOW.md`)

## Mandatory TodoWrite.md Task Management System

**CRITICAL REQUIREMENT**: All AI agents MUST use the `TodoWrite.md` system for all task management, planning, and execution. This system is the single source of truth for all work items in the project.

### The `TodoWrite.md` Specification

The `TodoWrite.md` system is a hierarchical task management system with a 5-level structure: **Goal → Phase → Step → Task → SubTask**. It enforces strict rules for single concern, traceability, and validation.

All agents MUST adhere to the full specification defined in the `ToDoWrite.md` file.

### Key Principles of `TodoWrite.md`

- **Hierarchical Decomposition**: All work MUST be decomposed through the 5-level hierarchy.
- **Single Concern Principle (SoC)**: Every item at every level MUST address exactly one concern.
- **Atomicity**: The lowest level, `SubTask`, MUST map to a single, executable command.
- **Validation**: All items are subject to a strict validation pipeline, afs_fastapi/todos/manager.py

### Reference Implementation

The `afs_fastapi/core/todos_manager.py` module provides the reference implementation for the `TodoWrite.md` system, including data structures, validation logic, and migration from legacy formats. All agents MUST use the functions provided in this module for all task management operations.

### Enforcement

- All task creation, modification, and execution MUST be done through the `todos_manager.py` API.
- The validation pipeline in `todos_manager.py` will be enforced.
- Agents MUST NOT use any other task management system or format.
- The legacy task management system is deprecated and MUST NOT be used.

## Mandatory Git Commit Message Format

**CRITICAL REQUIREMENT**: All AI agents MUST create git commit messages using HEREDOCs. This ensures that commit messages are well-formatted, multi-line, and easy to read.

### HEREDOC Format

The commit message MUST be formatted as a HEREDOC, like this:

```bash
git commit -F - <<EOF
feat(scope): Short description of the change

Longer description of the change, explaining the what and the why.
Can be multiple lines.

- Bullet points are also good.

Co-authored-by: Agent Name <agent@email.com>
EOF
```

### Enforcement

- All `git commit` commands MUST use the `-F -` option to read the commit message from stdin.
- The commit message MUST be provided as a HEREDOC.
- Pre-commit hooks MAY be used to validate the commit message format.

## Mandatory Type Hinting and Annotation

**CRITICAL REQUIREMENT**: All AI agents MUST use type hints and annotations for all code and tests they generate. This is a critical requirement and any violation will be considered a failure.

### Rationale

This project enforces strict type safety to ensure the reliability and maintainability of the agricultural robotics platform. Type hints and annotations are essential for static analysis, code completion, and overall code quality.

### Enforcement

- All function and method signatures MUST include type hints for all arguments and the return value.
- All variables MUST be annotated with their type when they are defined.
- The `mypy` pre-commit hook is enabled and MUST pass for all commits.
- Agents MUST NOT generate any code or tests without proper type hinting and annotation.

## Configuration

- Python: `>=3.12,<3.13` (see `pyproject.toml`)
- **Quality gates**: Ruff, Black, MyPy, isort; zero warnings expected (195 tests maintained)
- **TDD enforcement hooks** (required):
  - `.claude/hooks/tdd_enforcement.py` - Validates Test-First Development compliance
  - `.claude/hooks/safety_validation.py` - Ensures agricultural safety standards compliance
- **Documentation style**: NumPy-style docstrings; dual audience (educational + professional)
- **Safety & standards**: See [SESSION_SUMMARY.md - Agricultural Robotics Context](SESSION_SUMMARY.md#agricultural-robotics-context) for ISO compliance requirements
- **Performance requirements**: Sub-millisecond coordination operations for embedded agricultural systems

### Environment Sanity (pyenv)

- Verify pyenv before development:
  - `pyenv --version` prints a version with no errors
  - `pyenv rehash` runs clean (no “shims isn’t writable”)
- If shims warning appears: `chmod u+rwx ~/.pyenv/shims && pyenv rehash`.
- Keep zsh init in `~/.zshrc`; ensure `~/.bash_profile` is bash-safe, for example:
  - `export PYENV_ROOT="$HOME/.pyenv"`
  - `[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"`
  - `eval "$(pyenv init -)"`
  - Optionally: `eval "$(pyenv virtualenv-init -)"` if plugin installed
- See the Quick Verification Checklist in `CONTRIBUTING.md` for the full procedure.

## Dependencies

- Runtime: `fastapi`, `uvicorn[standard]`, `starlette`, `pydantic`
- Dev/Test: `pytest`, `pytest-asyncio`, `httpx`, `mypy`, `ruff`, `black`, `isort`
- See `pyproject.toml` for pinned versions and scripts

## Examples

- **Mandatory TDD workflow** (enforced by pre-commit hooks):
  1) **RED**: Create/extend test in `tests/` that fails, including agricultural context
  2) Run `pytest` to confirm RED phase - test must fail initially
  3) **GREEN**: Implement minimal code in `afs_fastapi/` to satisfy test requirements
  4) Run `pytest` to confirm GREEN phase - test now passes
  5) **REFACTOR**: Enhance code quality while maintaining test coverage
  6) Ensure all quality gates pass: `ruff`, `black`, `mypy`, `isort` (zero warnings)
  7) Pre-commit hooks validate TDD compliance and agricultural safety standards
- **Git Commit Separation of Concerns** (enforced by pre-commit hooks):
  1) Each commit addresses exactly one concern: `feat`, `fix`, `docs`, `refactor`, `test`, `config`, `perf`, `security`
  2) Use conventional format: `type(scope): description` with agricultural context
  3) Examples: `feat(equipment): add tractor synchronization`, `fix(safety): resolve emergency stop timing`
  4) Pre-commit validation prevents commits addressing multiple concerns
  5) See `GIT_COMMIT_SEPARATION_MANDATORY.md` for complete guidelines
- **Session workflow**: `./bin/loadsession` → `./bin/whereweare` → review project state → develop → `./bin/savesession` (before ending)
- **Command details**: See [SESSION_SUMMARY.md - Universal Session Management Commands](SESSION_SUMMARY.md#universal-session-management-commands) for complete usage examples and functionality

## VS Code & CLI Workflows

- VS Code tasks (suggested):
  - Run API: command `python -m afs_fastapi` (uses env vars below)
  - Run tests: command `pytest -q`
  - Linters/formatters: `ruff check . && black --check . && mypy .`
- Environment variables for running the API:
  - `AFS_API_HOST` (default `127.0.0.1`)
  - `AFS_API_PORT` (default `8000`)
  - `AFS_API_RELOAD` (`true/false`, default `false`)
  - `AFS_API_LOG_LEVEL` (`debug|info|warning|error`, default `info`)
- Handy CLI snippets:
  - Start API quickly: `AFS_API_RELOAD=1 python -m afs_fastapi`
  - Exercise OpenAPI docs: open `http://127.0.0.1:8000/docs`
  - Run focused tests: `pytest -q tests/services/test_*.py -k fleet`
  - Type-check changed files: `git diff --name-only HEAD~1 | rg ".py$" | xargs -r mypy`
  - Lint and format: `ruff check . && black . && isort .`
  - Pre-commit: `make precommit-install` then `make precommit-run`
  - Pytest config now in `pytest.ini` (kept minimal; mirrors previous pyproject settings)

## Recommended VS Code Settings (optional)

- Python interpreter: use `.venv` if present; otherwise configure 3.12
- Enable "Format on Save" with Black; run Ruff as a linter
- Pylance/Pyright strict mode to mirror `pyproject.toml`
- Set test discovery to `pytest` with `tests` as root

## Pre-commit Hooks (Required Enforcement)

- **Config**: `.pre-commit-config.yaml` (local hooks; no network dependency)
- **Enforced on every commit** (blocks non-compliant code):
  - **Code quality**: Ruff (lint), Black (format check), isort (imports), MyPy (types)
  - **TDD enforcement**: `.claude/hooks/tdd_enforcement.py` - Validates Test-First Development
  - **Safety validation**: `.claude/hooks/safety_validation.py` - Ensures agricultural safety standards compliance
  - **Commit separation**: `.claude/hooks/commit_separation_enforcement.py` - Enforces single concern per commit
- **Installation**: `make precommit-install` (installs pre-commit and registers hooks)
- **Manual execution**: `make precommit-run` (run all hooks without committing)
- **Status**: ACTIVE and ENFORCED - prevents non-compliant code and commits from entering codebase

## Recent TDD Enforcement Implementation

- **INVESTIGATION_PATTERN_MANDATORY.md**: Universal AI agent investigation pattern requirement (374 lines) with enforcement
- **TDD_FRAMEWORK_MANDATORY.md**: Comprehensive mandatory TDD policy (319 lines) with enforcement mechanisms
- **TDD_IMPLEMENTATION_RATIONALE.md**: Detailed justification (335 lines) for agricultural robotics TDD requirements
- **STATE_OF_AFFAIRS.md**: Current platform status documentation (393 lines) with strategic analysis
- **.claude/hooks/**: Investigation pattern validator, TDD enforcement (239 lines), and safety validation (296 lines) pre-commit hooks
- **SESSION_SUMMARY.md**: Enhanced with investigation pattern and TDD enforcement policies
- **CLAUDE.md**: Updated with mandatory TDD and investigation pattern requirements for all AI agents
- **loadsession**: Enhanced with critical TDD and investigation pattern compliance reminders
- **.pre-commit-config.yaml**: Local hooks for quality gates plus mandatory TDD and Safety validators
- **CI/CD Pipeline**: Automated validation ensuring 195 tests pass with TDD compliance enforcement
- **whereweare command**: Strategic assessment display (`bin/whereweare`) and generation (`bin/whereweare --generate`) for universal AI agent access
- **updatedocs command**: Meta-command for unified documentation regeneration (`bin/updatedocs`) updating all 6 core documents with dry-run and selective update modes for universal AI agent access

## Coding Conventions (Agricultural Robotics Standards)

- **Naming**: Clear, conversational naming following PEP 8 with agricultural domain context
- **Type safety**: Precise type hints; maintain mypy strict mode compliance (zero warnings)
- **Interface Contracts**: Utilize Python `Protocol` classes for defining clear and explicit interface contracts to enhance type safety, modularity, and maintainability across the codebase.
- **Function design**: Compact, purposeful functions avoiding over-engineering
- **Testing requirements**: Comprehensive tests with realistic agricultural scenarios and performance validation
- **Documentation standards**: Professional tone with concrete agricultural examples and educational context
- **Safety compliance**: All equipment and coordination code must include safety considerations (see [SESSION_SUMMARY.md - Agricultural Robotics Context](SESSION_SUMMARY.md#agricultural-robotics-context))
- **Performance constraints**: Code must meet embedded agricultural equipment limitations (<1ms coordination operations)

---

## Mandatory TDD and Explanation Workflow

All agents must adhere to a strict Test-Driven Development (TDD) workflow, specifically the Red-Green-Refactor cycle. This process is mandatory and serves as a foundational development practice.

1.  **Educate and Explain:** For every significant action, you must first educate on the **WHY** of your choices (the reasoning and strategic decisions) and then explain the **HOW** of your implementation (the technical details of the code generation).

2.  **Red Phase (Write a Failing Test):** Before writing any implementation code, you MUST first write a test. This test must initially fail (be 'Red'). The failure must be for a valid reason, such as an `AssertionError` because the expected output does not match the actual output of the unimplemented feature. Tests that fail simply because a module or function is not yet defined are insufficient. The test itself is a piece of living documentation and must be clear and purposeful.

3.  **Green Phase (Write Code to Pass the Test):** After creating a failing test, you will write the minimum amount of implementation code necessary to make the test pass (turn 'Green'). When presenting this code, you MUST explain **WHY** you chose that specific implementation and **HOW** it directly fulfills the requirements defined by the test.

4.  **Refactor Phase:** Once the test is passing, you may refactor the code for clarity, efficiency, and maintainability. You must explain the refactoring changes and the reasoning behind them.

All generated code, tests, and documentation must be of professional quality, well-commented, and serve as a clear record of the system's functionality. The tests themselves are considered living documentation.