# `formatall` Command Documentation

## Purpose

The `formatall` command is a convenience script designed to apply a suite of code quality tools (linters and formatters) across the entire AFS FastAPI project. Its primary purpose is to ensure consistent code style, identify potential issues, and maintain high code quality standards, which are critical for collaborative development and safety-critical agricultural robotics applications.

## Usage

To apply linters and formatters across the entire project, execute the `formatall` command from your project's root directory:

```bash
./bin/formatall
```

## Key Features

*   **Comprehensive Code Formatting**: Utilizes `black` to automatically reformat Python code to adhere to a consistent style.
*   **Linting**: Employs `ruff` to identify and report various code quality issues, potential bugs, and stylistic errors.
*   **Import Sorting**: Uses `isort` to automatically sort and format import statements, improving readability and consistency.
*   **Type Checking**: Integrates `pyright` for static type checking, helping to catch type-related errors early in the development cycle.
*   **Pre-commit Integration**: Designed to be run manually or integrated into pre-commit hooks to enforce code quality before commits are made.

## Agricultural Context

In the context of the AFS FastAPI Agricultural Robotics Platform, `formatall` is essential for:

*   **Code Reliability**: Ensuring that the codebase for safety-critical agricultural systems is free from common errors and adheres to best practices, reducing the risk of malfunctions.
*   **Team Collaboration**: Facilitating smooth collaboration among a diverse team of agricultural engineers, robotics engineers, and AI specialists by enforcing a unified code style.
*   **Maintainability**: Improving the long-term maintainability of the platform by keeping the codebase clean, readable, and consistent.
*   **Compliance**: Supporting compliance efforts with agricultural standards (ISO 18497, ISO 11783) by promoting high-quality, auditable code.

## Example Output

```
Success: no issues found in 97 source files
```

This output indicates that all source files were checked and found to be compliant with the configured linters and formatters.
