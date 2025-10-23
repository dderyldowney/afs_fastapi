"""Pytest configuration for AFS FastAPI Agricultural Robotics Platform.

This configuration file provides pytest hooks and fixtures for the entire test suite.
It ensures proper test execution across all developers, AI agents, and CI/CD pipelines.

Agricultural Context: Test infrastructure for safety-critical agricultural robotics
systems requires reliable test isolation and proper handling of parallel execution
to ensure ISO compliance validation.
"""

import os
import shutil
import tempfile
from typing import Any

import pytest


def pytest_configure(config: Any) -> None:
    """Configure pytest with TodoWrite database isolation.

    Sets up a temporary directory with a fresh SQLite database for all TodoWrite
    tests to ensure complete test isolation. This prevents singleton database state
    pollution between tests by using a dedicated temporary database file.

    Agricultural Context: Ensures clean state for each agricultural robotics
    test scenario without persistent database artifacts between runs.
    """
    # Create a temporary directory for test databases
    temp_dir = tempfile.mkdtemp(prefix="todowrite_test_")
    test_db_path = os.path.join(temp_dir, "todos.db")

    # Set environment variable to use the temporary test database
    # Format: sqlite:///path/to/db/todos.db
    os.environ["TODOWRITE_DATABASE_URL"] = f"sqlite:///{test_db_path}"

    # Store temp directory path for cleanup
    config.todowrite_temp_dir = temp_dir


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Clean up TodoWrite test database after all tests complete.

    Removes the temporary directory created during pytest_configure.

    Agricultural Context: Ensures no leftover test artifacts on disk.
    """
    if hasattr(session.config, "todowrite_temp_dir"):
        temp_dir = session.config.todowrite_temp_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Modify test collection to handle serial marker for pytest-xdist.

    Tests marked with @pytest.mark.serial will be assigned to the same xdist group,
    ensuring they run sequentially rather than in parallel. This is critical for
    tests that use module-level singletons or shared resources that don't support
    parallel execution.

    Args:
        config: Pytest configuration object
        items: List of collected test items

    Agricultural Context: Sequential execution ensures proper test isolation for
    singleton patterns used in token usage tracking and other shared resources
    in agricultural robotics CI/CD pipelines.
    """
    for item in items:
        if "serial" in item.keywords:
            # Assign all serial tests to the same xdist group
            # This ensures they run sequentially on the same worker
            item.add_marker(pytest.mark.xdist_group("serial"))
