# Keep It Simple (KIS) Directive

## AGENT INSTRUCTIONS (NON-NEGOTIABLE)

ALL agents, including AI assistants, must adhere to these principles at ALL times.

### 1. KIS (Keep It Simple) Principle
**Simplicity over complexity** - Always choose the simplest solution that works
**Clarity over cleverness** - Code should be easy to understand
**Essential over extra** - Only add what's truly necessary
**Readability over optimization** - Clear code is more valuable than micro-optimizations
**Maintainability over features** - Easy to maintain is better than more features

### 2. PEP Compliance (MANDATORY)
**Follow ALL relevant PEPs** - Strict adherence to Python Enhancement Proposals:
- PEP 8: Style Guide for Python Code
- PEP 484: Type Hints
- PEP 695: Type Parameter Syntax
- PEP 570: Python 3.8 Positional-Only Parameters
- PEP 572: Assignment Expressions (Walrus Operator)
- PEP 585: Built-in Generic Types
- PEP 604: Union Types
- PEP 613: TypeAlias
- PEP 616: String methods to remove prefixes and suffixes

**NO EXCEPTIONS** - All code must pass linting tools (black, isort, ruff, pyright)

### 3. CLI Tool Usage (MANDATORY)
**USE COMMAND LINE TOOLS FIRST** - Before reading files:
- **grep/rg** for text searches
- **find** for file searches
- **sed** for simple replacements
- **awk** for text processing
- **ls/dir** for directory listings
- **head/tail** for file previews

**LOWER TOKEN USAGE** - CLI tools reduce context bloat:
- Use `grep -n` for line numbers
- Use `find -name` patterns for file discovery
- Use `sed` for bulk text operations
- Only Read tool when absolutely necessary

### 4. Constant Vigilance for Simplification (MANDATORY)
**ALWAYS LOOK FOR SIMPLIFICATION OPPORTUNITIES**:
- Remove redundant code and data
- Eliminate unnecessary variables
- Simplify complex logic
- Reduce function parameters
- Combine related operations
- Remove unused imports
- Consolidate duplicate tests

**VIGILANCE CHECKLIST** - Before completing any task:
- [ ] Can this be simpler?
- [ ] Is there redundant code?
- [ ] Are there unused variables/imports?
- [ ] Can CLI tools replace reading files?
- [ ] Does this follow PEP standards?
- [ ] Is this over-engineered?

### 5. TDD - Red-Green-Refactor (ABSOLUTELY MANDATORY)
**TEST-DRIVEN DEVELOPMENT METHODOLOGY - NOT OPTIONAL**:
1. **RED**: Write failing test FIRST - ALWAYS
2. **GREEN**: Make MINIMAL changes to pass test ONLY
3. **REFACTOR**: Simplify while keeping test GREEN ONLY
4. **REPEAT**: Cycle continues for EACH feature - NO EXCEPTIONS

**TDD ABSOLUTE REQUIREMENTS**:
- ALWAYS write tests BEFORE code (RED phase) - NEVER skipped
- NEVER write production code WITHOUT failing test - ZERO TOLERANCE
- TDD IS MANDATORY - NOT "nice to have" or "available"
- Red-Green-Refactor cycle MUST be followed FOR ALL CHANGES
- Keep test-to-code ratio high (minimum 80% coverage) - ENFORCED
- Refactor ONLY after GREEN phase confirmed - NO SHORTCUTS
- Simplicity during REFACTOR phase (KIS principle) - REQUIRED

**VIOLATION CONSEQUENCES**: Any code written without following TDD Red-Green-Refactor IS NOT ACCEPTABLE

### 6. Test Cleanup (MANDATORY)
**ZERO ARTIFACTS REQUIREMENT**:
- Tests MUST clean up ALL artifacts after execution
- Leave ZERO files, databases, temporary data
- Use setUp/tearDown methods properly
- Clean up database connections
- Remove temporary directories
- Reset environment variables
- Verify cleanup with assertions

**CLEANUP ENFORCEMENT**:
- NO test files left in project directory
- NO database files after test completion
- NO temporary directories after test completion
- NO environment pollution
- NO resource leaks

### 7. Test Simplification (MANDATORY)
**KIS TESTING PRINCIPLES**:
- One assertion per test when possible
- Test one behavior per test
- Use simple, descriptive test names
- Avoid complex test setup/teardown
- Don't test implementation details
- Use simple test data
- Eliminate redundant test cases
- Apply TDD Red-Green-Refactor methodology (MANDATORY)
- Follow Red-Green-Refactor cycle for ALL changes (NO EXCEPTIONS)
- Ensure complete cleanup (ZERO artifacts) (MANDATORY)

### Enforcement and Violations

**ABSOLUTE REQUIREMENTS** - NO EXCEPTIONS:
- PEP compliance (verified by linting tools)
- CLI tool usage for file operations
- Constant simplification vigilance
- KIS principles in all code
- TDD Red-Green-Refactor methodology
- Test cleanup (ZERO artifacts)
- Test simplification

**VIOLATIONS OF THESE DIRECTIVES ARE NOT ACCEPTABLE**

**MONITORING**: All interactions will be evaluated for compliance with these non-negotiable requirements.

**Last updated: 2025-11-03**
**Status: ACTIVE - NON-NEGOTIABLE - PERMANENT**
