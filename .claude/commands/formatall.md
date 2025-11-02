# Format All Files Command

## Command Name
formatall

## Purpose
Applies comprehensive code formatting and quality standards to all files in the AFS FastAPI agricultural robotics platform, ensuring consistency and preventing pre-commit hook failures.

## Description
This command runs all quality control tools (Black, isort, Ruff, MyPy) to bring files into compliance with enterprise development standards required for safety-critical agricultural systems.

## Implementation
```bash
# Apply Black formatting
black . --quiet

# Sort imports with isort
isort . --quiet

# Fix linting issues with Ruff
ruff check . --fix --quiet

# Validate types with MyPy
pyright . --ignore-missing-imports --no-strict-optional
```

## When to Use
- Before creating git commits
- After generating new code files
- When pre-commit hooks report formatting violations
- At start of development sessions for clean baseline
- Before pushing to remote repository

## Expected Output
```
Success: no issues found in X source files (MyPy)
(Silent execution for other tools when successful)
```

## Format-First Generation
This command embodies our format-first approach:
- Apply formatting during code generation, not after
- Ensure all generated content emerges in final quality form
- Prevent formatting cycles through immediate compliance

## Agricultural Context
Code formatting consistency is crucial for safety-critical agricultural robotics where multiple developers work on tractor coordination systems. Consistent formatting reduces errors during code reviews and ensures ISO compliance documentation maintains professional standards.

## Quality Standards Applied
- **Black**: Python code formatting (line length, indentation, spacing)
- **isort**: Import organization and grouping
- **Ruff**: Linting and code quality enforcement
- **MyPy**: Type checking for safety-critical operations

## Integration with Workflow
- Part of pre-commit hook validation
- Used before test execution
- Applied to all generated content immediately
- Essential for maintaining zero technical debt

## Error Prevention
This command prevents common formatting errors:
- Inconsistent code style across modules
- Import organization violations
- Type annotation missing or incorrect
- Linting rule violations that could mask bugs

## Related Commands
- `fixmodules`: Module installation before quality checks
- `fulltest`: Comprehensive testing after formatting
- Pre-commit hooks: Automated formatting validation

---

**Status**: Essential for maintaining code quality standards
**Frequency**: High (before every commit and after code generation)
**Integration**: Required component of development workflow