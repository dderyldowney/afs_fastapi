# Code Quality: Formatting and Linting

Maintaining high code quality is essential for the AFS FastAPI Agricultural Robotics Platform, especially given its safety-critical nature and collaborative development environment. This section outlines the tools and procedures used for code formatting and linting.

## 1. Overview of Code Quality Tools

The project leverages a suite of Python-specific tools to automate code quality checks and ensure consistency:

*   **Black**: An uncompromising Python code formatter.
*   **Ruff**: An extremely fast Python linter, written in Rust.
*   **isort**: A utility to sort Python imports alphabetically and automatically separate them into sections and by type.
*   **MyPy**: A static type checker for Python, used to catch type-related errors.

These tools are integrated into the development workflow via pre-commit hooks and the `formatall` script.

## 2. Code Formatting with Black

**Black** is used to ensure consistent code formatting across the entire project. It automatically reformats code to adhere to the PEP 8 style guide, with some minor deviations.

### 2.1. Running Black

To format a specific file:

```bash
black your_module.py
```

To format the entire project (as part of `formatall`):

```bash
./bin/formatall
```

### 2.2. Checking Formatting

To check if files are correctly formatted without applying changes (used in pre-commit hooks):

```bash
black --check your_module.py
```

## 3. Linting with Ruff

**Ruff** is a high-performance Python linter that helps identify and report various code quality issues, potential bugs, and stylistic errors. It is configured via `pyproject.toml`.

### 3.1. Running Ruff

To lint a specific file:

```bash
ruff check your_module.py
```

To lint the entire project (as part of `formatall`):

```bash
./bin/formatall
```

### 3.2. Auto-fixing Issues

Ruff can automatically fix some issues:

```bash
ruff check --fix your_module.py
```

## 4. Import Sorting with isort

**isort** automatically sorts and formats import statements in Python files. This improves readability and helps prevent merge conflicts related to import order.

### 4.1. Running isort

To sort imports in a specific file:

```bash
isort your_module.py
```

To sort imports across the entire project (as part of `formatall`):

```bash
./bin/formatall
```

### 4.2. Checking Import Sorting

To check if imports are correctly sorted without applying changes (used in pre-commit hooks):

```bash
isort --check-only your_module.py
```

## 5. Type Checking with MyPy

**MyPy** is a static type checker that helps catch type-related errors in Python code. It uses type hints (annotations) to verify type consistency.

### 5.1. Running MyPy

To type-check a specific file:

```bash
pyright your_module.py
```

To type-check the entire project (as part of `formatall`):

```bash
./bin/formatall
```

### 5.2. Configuration

MyPy is configured via `pyright.ini` in the project's root directory, which specifies settings for strictness and module paths.

## 6. Integration with `formatall` and Pre-commit Hooks

All these tools are integrated into the `./bin/formatall` script, which provides a convenient way to run all checks. Furthermore, they are configured as pre-commit hooks, ensuring that no code violating these standards can be committed to the repository.

This automated approach to code quality is vital for the AFS FastAPI Agricultural Robotics Platform to maintain reliability, facilitate collaboration, and adhere to safety and compliance standards.
