.PHONY: help run test lint format type check clean precommit-install precommit-run precommit-autoupdate install-dev \
         tw-all tw-init tw-schema tw-lint tw-validate tw-trace tw-prove tw-hooks tw-commitcheck tw-clean tw-check tw-dev tw-prod tw-deps tw-examples tw-test tw-help

help:
	@echo "Targets:"
	@echo "  run     - Start API with reload"
	@echo "  test    - Run pytest (-q)"
	@echo "  lint    - Ruff lint"
	@echo "  format  - Black + isort"
	@echo "  type    - mypy type-check"
	@echo "  check   - lint + type + test"
	@echo "  precommit-install - install and enable pre-commit hooks"
	@echo "  precommit-run     - run pre-commit on all files"
	@echo "  precommit-autoupdate - update hook revisions"
	@echo "  install-dev - Install project in editable mode with dev dependencies"

run:
	AFS_API_RELOAD=1 python -m afs_fastapi

test:
	pytest -q

lint:
	ruff check .

format:
	black . && isort .

type:
	mypy .

check: install-dev lint type test

clean:
	rm -rf .pytest_cache .mypy_cache **/__pycache__

precommit-install:
	python -m pip install pre-commit && pre-commit install

precommit-run:
	pre-commit run --all-files

precommit-autoupdate:
	pre-commit autoupdate

install-dev:
	python -m pip install -e .[dev]

# ============================================================================
# TodoWrite System Targets (12-layer declarative planning framework)
# ============================================================================

# Default TodoWrite workflow
tw-all: tw-schema tw-lint tw-validate tw-trace

# Initialize TodoWrite directory structure
tw-init:
	@echo "🏗️  Initializing TodoWrite directory structure..."
	@mkdir -p plans/{goals,concepts,contexts,constraints,requirements,acceptance_criteria,interface_contracts,phases,steps,tasks,subtasks}
	@mkdir -p commands schemas tools trace results
	@echo "✅ TodoWrite layout initialized"

# Generate/refresh JSON Schema
tw-schema:
	@echo "📋 Generating TodoWrite JSON Schema..."
	@python3 tools/tw_validate.py --write-schema schemas/todowrite.schema.json
	@echo "✅ Schema generated at schemas/todowrite.schema.json"

# Lint for Separation of Concerns violations
tw-lint:
	@echo "🔍 Linting for SoC violations..."
	@python3 tools/tw_lint_soc.py --plans plans --report trace/lint_report.json
	@echo "✅ SoC linting completed"

# Validate all plan files against schema
tw-validate:
	@echo "✅ Validating YAML files against schema..."
	@python3 tools/tw_validate.py --plans plans --schema schemas/todowrite.schema.json
	@echo "✅ Schema validation completed"

# Build traceability matrix and dependency graph
tw-trace:
	@echo "🔗 Building traceability matrix..."
	@python3 tools/tw_trace.py --plans plans --out-csv trace/trace.csv --out-graph trace/graph.json --validate
	@echo "✅ Traceability analysis completed"

# Generate command stubs for pending Acceptance Criteria
tw-prove:
	@echo "⚡ Generating command stubs for Acceptance Criteria..."
	@python3 tools/tw_stub_command.py --acs plans/acceptance_criteria --out commands
	@echo "✅ Command stubs generated"

# Install git commit hooks
tw-hooks:
	@echo "🪝 Installing git commit hooks..."
	@chmod +x tools/git-commit-msg-hook.sh || true
	@ln -sf ../../tools/git-commit-msg-hook.sh .git/hooks/commit-msg || true
	@echo "✅ Git commit-msg hook installed"

# Check commit message format (used by git hook)
tw-commitcheck:
	@echo "📝 Checking commit message format..."
	@tools/git-commit-msg-hook.sh --check
	@echo "✅ Commit format valid"

# Clean TodoWrite generated files
tw-clean:
	@echo "🧹 Cleaning TodoWrite generated files..."
	@rm -rf trace/*.json trace/*.csv
	@rm -rf results/*
	@rm -f schemas/todowrite.schema.json
	@echo "✅ TodoWrite clean completed"

# Full TodoWrite validation pipeline (strict mode)
tw-check: tw-schema tw-lint tw-validate tw-trace
	@echo "🔍 Running full TodoWrite validation pipeline..."
	@python3 tools/tw_lint_soc.py --plans plans --strict
	@python3 tools/tw_trace.py --plans plans --validate
	@echo "✅ All TodoWrite checks passed!"

# Development workflow: lint, validate, and generate commands
tw-dev: tw-lint tw-validate tw-prove
	@echo "💻 TodoWrite development workflow completed"

# Production workflow: full validation with traceability
tw-prod: tw-all tw-prove
	@echo "🚀 TodoWrite production workflow completed"

# Install Python dependencies for TodoWrite tools
tw-deps:
	@echo "📦 Installing TodoWrite Python dependencies..."
	@pip install pyyaml jsonschema
	@echo "✅ TodoWrite dependencies installed"

# Generate example TodoWrite files for testing
tw-examples:
	@echo "📝 Creating example TodoWrite files..."
	@mkdir -p plans/goals plans/requirements plans/acceptance_criteria
	@echo 'id: GOAL-AGRICULTURAL-AUTOMATION\nlayer: Goal\ntitle: Implement autonomous agricultural equipment coordination\ndescription: >\n  Enable multiple tractors and implements to coordinate field operations\n  autonomously while maintaining safety and efficiency standards.\nmetadata:\n  owner: product-team\n  labels: [work:architecture, agricultural, autonomous]\n  severity: high\n  work_type: architecture\nlinks:\n  parents: []\n  children: [CON-MULTI-TRACTOR]' > plans/goals/GOAL-AGRICULTURAL-AUTOMATION.yaml
	@echo 'id: R-CAN-001\nlayer: Requirements\ntitle: Tractor exchanges ISO 11783 messages on 250 kbps J1939 bus\ndescription: >\n  The ECU shall communicate using ISO 11783 PGNs over a 250 kbps J1939 CAN bus with ≤ 50 ms jitter.\nmetadata:\n  owner: controls-team\n  labels: [work:spec, can, j1939, isobus]\n  severity: med\n  work_type: spec\nlinks:\n  parents: [GOAL-AGRICULTURAL-AUTOMATION]\n  children: [AC-CAN-001]' > plans/requirements/R-CAN-001.yaml
	@echo 'id: AC-CAN-001\nlayer: AcceptanceCriteria\ntitle: Address Claim ≤ 2 s; PGN 65280 at ≥ 10 Hz; jitter ≤ 50 ms\ndescription: |\n  Given a live 250 kbps bus, when ECU boots, then Address Claim completes ≤ 2 s.\n  PGN 65280 is observed at ≥ 10 Hz with jitter ≤ 50 ms (95th percentile).\nmetadata:\n  owner: test-team\n  labels: [work:validation, can, j1939]\n  work_type: validation\nlinks:\n  parents: [R-CAN-001]\n  children: []' > plans/acceptance_criteria/AC-CAN-001.yaml
	@echo "✅ Example TodoWrite files created"

# Test the complete TodoWrite system with examples
tw-test: tw-examples tw-all tw-prove
	@echo "🧪 Testing complete TodoWrite system..."
	@echo "📊 Testing Results:"
	@echo "   - Schema validation: $(shell python3 tools/tw_validate.py --plans plans >/dev/null 2>&1 && echo 'PASS' || echo 'FAIL')"
	@echo "   - SoC linting: $(shell python3 tools/tw_lint_soc.py --plans plans >/dev/null 2>&1 && echo 'PASS' || echo 'FAIL')"
	@echo "   - Traceability: $(shell python3 tools/tw_trace.py --plans plans --validate >/dev/null 2>&1 && echo 'PASS' || echo 'FAIL')"
	@echo "   - Command generation: $(shell test -f commands/CMD-CANAC001.yaml && echo 'PASS' || echo 'FAIL')"
	@echo "✅ TodoWrite system test completed"

# Display TodoWrite help information
tw-help:
	@echo "TodoWrite System Targets"
	@echo "======================="
	@echo ""
	@echo "Core Workflow:"
	@echo "  tw-all       - Run schema, lint, validate, trace (default)"
	@echo "  tw-init      - Initialize directory structure"
	@echo "  tw-schema    - Generate JSON schema"
	@echo "  tw-lint      - Check Separation of Concerns"
	@echo "  tw-validate  - Validate YAML against schema"
	@echo "  tw-trace     - Build traceability matrix"
	@echo "  tw-prove     - Generate command stubs"
	@echo ""
	@echo "Quality & Integration:"
	@echo "  tw-hooks     - Install git commit hooks"
	@echo "  tw-commitcheck - Check commit message format"
	@echo "  tw-clean     - Remove generated files"
	@echo "  tw-check     - Full validation (strict mode)"
	@echo ""
	@echo "Workflows:"
	@echo "  tw-dev       - Development workflow"
	@echo "  tw-prod      - Production workflow"
	@echo "  tw-deps      - Install Python dependencies"
	@echo "  tw-examples  - Create example files"
	@echo "  tw-test      - Test complete system"
	@echo "  tw-help      - Show this help"
	@echo ""
	@echo "Examples:"
	@echo "  make tw-init tw-schema  - Initialize and create schema"
	@echo "  make tw-dev            - Run development workflow"
	@echo "  make tw-check          - Run full validation"
	@echo "  make tw-test           - Test complete system"
