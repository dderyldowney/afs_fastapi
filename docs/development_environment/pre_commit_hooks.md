# Pre-commit Hooks

Pre-commit hooks are a powerful mechanism to ensure code quality and consistency within the AFS FastAPI Agricultural Robotics Platform. They allow you to run scripts automatically before each commit, catching issues early in the development cycle.

## 1. Purpose of Pre-commit Hooks

Pre-commit hooks serve several critical purposes:

*   **Code Quality Enforcement**: Automatically run linters (e.g., `ruff`), formatters (e.g., `black`), and type checkers (e.g., `pyright`) to ensure all committed code adheres to predefined style guides and quality standards.
*   **Early Bug Detection**: Catch common errors, syntax issues, and potential bugs before they are even committed to the repository, reducing the likelihood of introducing defects.
*   **Consistency**: Maintain a consistent code style and structure across the entire codebase, which is crucial for collaborative development and long-term maintainability.
*   **Reduced Review Overhead**: By automating basic code quality checks, code reviewers can focus on more complex logic and architectural concerns.
*   **TDD Enforcement**: Can be used to enforce Test-Driven Development (TDD) policies, ensuring tests are run and pass before code is committed.
*   **Safety and Compliance**: In safety-critical systems like agricultural robotics, pre-commit hooks can enforce checks related to safety standards and compliance, ensuring that critical code changes meet regulatory requirements.

## 2. How Pre-commit Hooks Work

When you attempt to make a Git commit, the pre-commit framework intercepts the commit operation. It then runs a series of configured hooks on the files that are staged for commit. If any of these hooks fail, the commit is aborted, and you are notified of the issues. The commit will only proceed if all configured hooks pass successfully.

## 3. Project's Pre-commit Configuration

The AFS FastAPI project uses the `pre-commit` framework, configured via the `.pre-commit-config.yaml` file in the project's root directory. This file defines the various hooks that are run.

Currently, the project includes hooks for:

*   **`ruff`**: A fast Python linter, used for checking code style and potential errors.
*   **`black`**: An uncompromising Python code formatter, ensuring consistent code style.
*   **`isort`**: A Python utility to sort imports alphabetically and automatically separate them into sections and by type.
*   **`pyright`**: A static type checker for Python, used to catch type-related errors.
*   **`tdd-enforcement`**: A custom hook to enforce Test-Driven Development policies.
*   **`safety-validation`**: A custom hook for validating adherence to safety standards (e.g., ISO 18497 alignment).

## 4. Installing Pre-commit Hooks

To install the pre-commit hooks for your local repository, ensure your Python virtual environment is active and run:

```bash
pre-commit install
```

This command sets up the Git hooks that will automatically run the checks defined in `.pre-commit-config.yaml` before each commit.

## 5. Bypassing Pre-commit Hooks

In rare cases, you might need to bypass the pre-commit hooks (e.g., for a quick fix that doesn't require full checks, or when dealing with a temporary broken state). You can do this by adding the `--no-verify` flag to your `git commit` command:

```bash
git commit --no-verify -m "Temporary commit bypassing hooks"
```

**Use this option sparingly and with caution**, as it bypasses important quality checks.
