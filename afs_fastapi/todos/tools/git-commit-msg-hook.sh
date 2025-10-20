#!/usr/bin/env bash
# TodoWrite Git Commit Message Hook
# Enforces Conventional Commits format with TodoWrite-specific scopes

set -euo pipefail

# Configuration
HOOK_NAME="git-commit-msg-hook"
VERSION="1.0.0"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine commit message file
if [[ "${1:-}" == "--check" ]]; then
    msg_file=".git/COMMIT_EDITMSG"
else
    msg_file="${1:-.git/COMMIT_EDITMSG}"
fi

# Read commit message
if [[ -f "$msg_file" ]]; then
    msg="$(cat "$msg_file" || true)"
else
    echo -e "${RED}✖ Commit message file not found: $msg_file${NC}"
    exit 1
fi

# Skip if commit message is empty
if [[ -z "$msg" ]]; then
    echo -e "${YELLOW}⚠ Empty commit message${NC}"
    exit 0
fi

# Skip merge commits
if echo "$msg" | head -n1 | grep -q "^Merge "; then
    echo -e "${GREEN}✔ Merge commit - skipping validation${NC}"
    exit 0
fi

# Conventional Commits regex with TodoWrite scopes
# Format: <type>(<scope>): <description>
# Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
# Scopes: goal, concept, context, constraints, req, ac, iface, phase, step, task, subtask, cmd, schema, lint, trace, docs
conventional_regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)\((goal|concept|context|constraints|req|ac|iface|phase|step|task|subtask|cmd|schema|lint|trace|docs)\):\s.+'

# Extract first line (summary)
summary=$(echo "$msg" | head -n1)

# Check if summary matches Conventional Commits format
if ! echo "$summary" | grep -Eq "$conventional_regex"; then
    echo -e "${RED}✖ Commit message must follow Conventional Commits format with TodoWrite scopes${NC}"
    echo ""
    echo -e "${YELLOW}Required format:${NC}"
    echo "  <type>(<scope>): <description>"
    echo ""
    echo -e "${YELLOW}Valid types:${NC}"
    echo "  feat     - New feature"
    echo "  fix      - Bug fix"
    echo "  docs     - Documentation changes"
    echo "  style    - Code style changes (formatting, etc.)"
    echo "  refactor - Code refactoring"
    echo "  perf     - Performance improvements"
    echo "  test     - Adding or updating tests"
    echo "  build    - Build system changes"
    echo "  ci       - CI/CD changes"
    echo "  chore    - Maintenance tasks"
    echo "  revert   - Reverting previous changes"
    echo ""
    echo -e "${YELLOW}Valid TodoWrite scopes:${NC}"
    echo "  goal        - Strategic Goals"
    echo "  concept     - Big-picture concepts"
    echo "  context     - Environmental context"
    echo "  constraints - System constraints"
    echo "  req         - Requirements"
    echo "  ac          - Acceptance Criteria"
    echo "  iface       - Interface Contracts"
    echo "  phase       - Project phases"
    echo "  step        - Implementation steps"
    echo "  task        - Development tasks"
    echo "  subtask     - Sub-tasks"
    echo "  cmd         - Executable commands"
    echo "  schema      - Schema definitions"
    echo "  lint        - Linting and validation"
    echo "  trace       - Traceability"
    echo "  docs        - Documentation"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  feat(req): add R-CAN-001 for 250kbps J1939 bus with ≤50ms jitter"
    echo "  test(ac): add AC-CAN-001 Given/When/Then validation"
    echo "  build(schema): generate todowrite.schema.json"
    echo "  ci(lint): enforce SoC for non-executable layers"
    echo "  docs(cmd): document CMD-CAN-AC001 artifacts"
    echo ""
    echo -e "${RED}Your commit message:${NC}"
    echo "  $summary"
    echo ""
    exit 1
fi

# Additional validations

# Check summary length (recommended max 72 characters)
if [[ ${#summary} -gt 72 ]]; then
    echo -e "${YELLOW}⚠ Warning: Summary line is longer than 72 characters (${#summary})${NC}"
    echo "  Consider shortening: $summary"
fi

# Check for imperative mood (should start with verb)
description=$(echo "$summary" | sed 's/^[^:]*: *//')
if [[ "$description" =~ ^(added|fixed|updated|changed|removed|implemented) ]]; then
    echo -e "${YELLOW}⚠ Warning: Use imperative mood ('add' not 'added')${NC}"
    echo "  Current: $description"
fi

# Check for capitalization of description
if [[ "$description" =~ ^[A-Z] ]]; then
    echo -e "${YELLOW}⚠ Warning: Description should start with lowercase letter${NC}"
    echo "  Current: $description"
fi

# Check for trailing period
if [[ "$description" =~ \.$ ]]; then
    echo -e "${YELLOW}⚠ Warning: Description should not end with a period${NC}"
    echo "  Current: $description"
fi

# Parse commit message parts
if [[ "$summary" =~ ^([^(]+)\(([^)]+)\):\s*(.+)$ ]]; then
    type="${BASH_REMATCH[1]}"
    scope="${BASH_REMATCH[2]}"
    desc="${BASH_REMATCH[3]}"

    echo -e "${GREEN}✔ Conventional Commit format validated${NC}"
    echo -e "  ${BLUE}Type:${NC} $type"
    echo -e "  ${BLUE}Scope:${NC} $scope"
    echo -e "  ${BLUE}Description:${NC} $desc"

    # Additional scope-specific validations
    case "$scope" in
        "cmd")
            if [[ ! "$desc" =~ (CMD-|implement|execute|prove) ]]; then
                echo -e "${YELLOW}⚠ Command scope should mention CMD- IDs or execution${NC}"
            fi
            ;;
        "ac")
            if [[ ! "$desc" =~ (AC-|acceptance|criteria|validation) ]]; then
                echo -e "${YELLOW}⚠ AC scope should mention AC- IDs or validation${NC}"
            fi
            ;;
        "req")
            if [[ ! "$desc" =~ (R-|requirement|shall|must) ]]; then
                echo -e "${YELLOW}⚠ Requirements scope should mention R- IDs or requirements language${NC}"
            fi
            ;;
    esac
fi

# Check for breaking changes
if echo "$msg" | grep -q "BREAKING CHANGE:"; then
    echo -e "${YELLOW}🚨 Breaking change detected${NC}"
fi

# Check for issue references
if echo "$msg" | grep -q "Refs: #[0-9]"; then
    echo -e "${BLUE}🔗 Issue reference found${NC}"
fi

echo -e "${GREEN}✔ Commit message validation passed${NC}"
exit 0