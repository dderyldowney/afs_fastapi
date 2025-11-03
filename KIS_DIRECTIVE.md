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

**BEFORE EVERY OPERATION**:
1. Can this be simpler?
2. Is there redundant code?
3. Are there unused variables/imports?
4. Can CLI tools replace reading files?
5. Does this follow PEP standards?
6. Is this over-engineered?
7. Will tests cleanup all artifacts?

### 5. TDD - Red-Green-Refactor (ABSOLUTELY MANDATORY)
**NOT OPTIONAL - REQUIRED FOR ALL CHANGES**

**RED**: Write a failing test that demonstrates the requirement
**GREEN**: Write the simplest code to make the test pass
**REFACTOR**: Improve code quality while keeping tests green
**REPEAT**: Continue cycle for all functionality

**NO EXCEPTIONS** - All code changes must follow TDD methodology:
- Test cases must be written first
- All tests must pass before refactoring
- No production code without failing tests
- Refactoring only after tests pass

### 6. Pre-Commit Compliance (ABSOLUTELY MANDATORY)
**NEVER BYPASS PRE-COMMIT HOOKS**

**FORBIDDEN ACTIONS**:
- **NEVER** use `--no-verify` to bypass pre-commit hooks
- **NEVER** use `git commit --no-verify` under any circumstances
- **NEVER** disable pre-commit hooks temporarily
- **NEVER** commit code that fails pre-commit checks

**REQUIRED PROCESS**:
1. **FIX ALL ISSUES** identified by pre-commit hooks
2. **RESOLVE ALL ERRORS** before committing
3. **ASK FOR PERMISSION** only in exceptional circumstances
4. **DOCUMENT EXCEPTIONS** if any bypass is absolutely necessary

**EXCEPTIONAL CIRCUMSTANCES** (Must be explicitly requested):
- Critical production hotfixes with team approval
- Infrastructure issues preventing hook execution
- Verified false positives from tools with documented evidence

**MANDATORY VERIFICATION**:
- All code must pass all pre-commit hooks
- No linting errors or warnings
- All tests must pass
- Code quality standards must be met

### 7. Test Cleanup Requirements (MANDATORY)
**ZERO ARTIFACTS AFTER TEST COMPLETION**

**REQUIRED CLEANUP ACTIONS**:
- Remove temporary directories
- Delete database files
- Reset environment variables
- Clean up cache files
- Remove generated content
- Verify cleanup with assertions

**MANDATORY VERIFICATION**:
- Tests must leave the system in original state
- No side effects after test completion
- All temporary resources properly disposed
- File system returned to pre-test condition

## VIOLATION CONSEQUENCES

**ANY VIOLATION OF THESE DIRECTIVES IS UNACCEPTABLE**

- **Pre-commit bypass**: IMMEDIATE REJECTION - Never bypass pre-commit hooks
- **KIS violations**: Immediate refactoring required
- **PEP violations**: Code will not be accepted
- **CLI tool neglect**: Context will be rejected
- **TDD bypass**: Changes will be rejected
- **Cleanup violations**: Tests will be failed

**SEVERITY LEVELS**:
- **CRITICAL (Pre-commit bypass)**: Immediate rollback required
- **HIGH (TDD, PEP)**: Code rejected until fixed
- **MEDIUM (KIS, CLI)**: Refactoring required before acceptance
- **LOW (Cleanup)**: Test fixes required

## ENFORCEMENT

These directives are **ENFORCED AUTOMATICALLY** through:
- Site-wide Python configuration
- Import hooks and monitoring
- Test framework integration
- Code review requirements
- **Pre-commit hook enforcement** (Mandatory for all commits)

**PRE-COMMIT ENFORCEMENT**:
- **MANDATORY HOOKS**: All pre-commit hooks must pass
- **NO BYPASS ALLOWED**: `--no-verify` is forbidden
- **AUTOMATIC REJECTION**: Commits with failing hooks are rejected
- **QUALITY GATE**: Code quality must meet standards

**NO AGENT CAN BYPASS THESE REQUIREMENTS**

---

## APPROVED AGENT PATTERNS

### Simplicity Examples
```python
# ✅ GOOD: Simple and clear
def calculate_total(items):
    return sum(item.price for item in items)

# ❌ BAD: Over-engineered
def calculate_total(items: List[ProductType], currency: CurrencyType,
                   tax_calculator: TaxCalculatorInterface,
                   discount_applier: DiscountApplierClass) -> MonetaryAmount:
    # Complex implementation that could be simple
```

### CLI Tool Examples
```bash
# ✅ GOOD: Use grep first
grep -r "import.*requests" src/

# ✅ GOOD: Use find for files
find . -name "*.py" -exec grep -l "TODO" {} \;

# ❌ BAD: Read entire files when not needed
# Don't read entire file when you just need to check for imports
```

### TDD Examples
```python
# ✅ GOOD: Test first, then implementation
def test_add_numbers():
    assert add(2, 3) == 5

def add(a, b):
    return a + b

# ❌ BAD: Implementation without tests
def complex_business_logic():
    # Code written without failing test
```

### Pre-Commit Examples
```bash
# ✅ GOOD: Fix issues identified by pre-commit
git add .
git commit -m "Fix style issues"

# ✅ GOOD: Address all pre-commit feedback
# Fix linting errors first, then commit
black src/
isort src/
git add .
git commit -m "Code improvements"

# ❌ FORBIDDEN: Never bypass pre-commit hooks
git commit --no-verify -m "Quick fix"  # NEVER DO THIS

# ❌ FORBIDDEN: Don't use --no-verify under any circumstances
git add .
git commit --no-verify -m "Bypassing hooks"  # IMMEDIATE REJECTION
```

### Correct Process for Pre-Commit Issues
```bash
# 1. Run pre-commit manually to check issues
pre-commit run --all-files

# 2. Fix identified issues
black .
isort .
ruff check --fix .

# 3. Fix remaining issues manually
# Address any remaining errors

# 4. Commit normally (hooks will pass)
git add .
git commit -m "Proper code fixes"
```

**REMEMBER**:
- **Simplicity** is not just a preference - it is a requirement
- **Pre-commit compliance** is absolutely mandatory - no exceptions
- **Quality gates** protect code integrity for all team members
