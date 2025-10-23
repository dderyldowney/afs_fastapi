"""Pytest configuration for AFS FastAPI Agricultural Robotics Platform.

This configuration file provides pytest hooks and fixtures for the entire test suite.
It ensures proper test execution across all developers, AI agents, and CI/CD pipelines.

Agricultural Context: Test infrastructure for safety-critical agricultural robotics
systems requires reliable test isolation and proper handling of parallel execution
to ensure ISO compliance validation.
"""

from typing import Any

import pytest


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
            item.add_marker(pytest.mark.xdist_group(name="serial"))

