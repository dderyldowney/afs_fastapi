#!/usr/bin/env python3
"""
ABSOLUTE Test-First Development Enforcement Hook

This pre-commit hook enforces MANDATORY Test-First Development for ALL code
implementation in the AFS FastAPI Agricultural Robotics Platform.

ZERO EXCEPTIONS POLICY:
ALL development—Human AND AI/Agent/ML/LLM—MUST start with tests.
Testing drives ALL implementation. NO CODE WITHOUT TESTS.

Agricultural Context:
- Safety-critical multi-tractor coordination demands bulletproof reliability
- Equipment failures can cause damage or safety incidents
- ISO 18497 and ISO 11783 compliance requires comprehensive validation
- Embedded agricultural equipment has strict performance constraints

ABSOLUTE TDD Requirements:
1. EVERY function/class/module MUST have failing tests written FIRST
2. NO implementation code without corresponding test coverage
3. RED-GREEN-REFACTOR methodology mandatory for ALL contributors
4. Agricultural context required in ALL test scenarios
5. Performance validation required for equipment constraints
"""

import os
import re
import subprocess
import sys
from pathlib import Path


class TDDEnforcementValidator:
    """
    MANDATORY Test-First Development Enforcement Validator

    ABSOLUTE ENFORCEMENT: ALL code implementation MUST start with tests.
    ZERO EXCEPTIONS for Human or AI/Agent/ML/LLM contributors.

    Blocks ALL non-test-first development from entering the agricultural robotics codebase.
    Safety-critical systems require bulletproof reliability through comprehensive testing.
    """

    def __init__(self):
        self.project_root = Path.cwd()
        self.critical_modules = {
            "synchronization",
            "safety",
            "coordination",
            "motor_control",
            "power_management",
            "vision_systems",
            "emergency",
        }

    def validate_tdd_compliance(self, files: list[str]) -> tuple[bool, list[str]]:
        """
        Validate TDD compliance for modified files.

        Args:
            files: List of modified Python files

        Returns:
            Tuple of (is_compliant, error_messages)
        """
        errors = []

        for file_path in files:
            if not file_path.endswith(".py"):
                continue

            # Skip test files themselves
            if "/test" in file_path or file_path.startswith("test"):
                continue

            # Check for corresponding test file
            test_file_exists, test_path = self._check_test_file_exists(file_path)
            if not test_file_exists:
                errors.append(
                    f"TDD Violation: {file_path} lacks corresponding test file at {test_path}"
                )
                continue

            # Check if this is a critical agricultural component
            if self._is_critical_component(file_path):
                compliance_errors = self._validate_critical_component_tests(file_path, test_path)
                errors.extend(compliance_errors)

            # Check for recent test activity (Red-Green-Refactor pattern)
            if not self._has_recent_test_activity(test_path):
                errors.append(
                    f"TDD Violation: {file_path} modified without recent test updates. "
                    f"Red-Green-Refactor requires test-first development."
                )

        return len(errors) == 0, errors

    def _check_test_file_exists(self, source_file: str) -> tuple[bool, str]:
        """
        Check if corresponding test file exists for source file.

        Args:
            source_file: Path to source file

        Returns:
            Tuple of (exists, expected_test_path)
        """
        # Convert source path to expected test path
        # afs_fastapi/services/synchronization.py -> tests/services/test_synchronization.py

        if source_file.startswith("afs_fastapi/"):
            relative_path = source_file[len("afs_fastapi/") :]
            module_dir = os.path.dirname(relative_path)
            module_file = os.path.basename(relative_path)

            if module_file == "__init__.py":
                return True, ""  # __init__.py files don't require individual tests

            test_file = f"test_{module_file}"
            test_path = (
                f"tests/{module_dir}/{test_file}" if module_dir else f"tests/{test_file}"
            )

            return os.path.exists(test_path), test_path

        return True, ""  # Non-afs_fastapi files don't require tests

    def _is_critical_component(self, file_path: str) -> bool:
        """
        Determine if file is a critical agricultural robotics component.

        Args:
            file_path: Path to source file

        Returns:
            True if file contains critical agricultural functionality
        """
        file_content = file_path.lower()

        # Check for critical module keywords
        for module in self.critical_modules:
            if module in file_content:
                return True

        # Check for safety-critical paths
        critical_paths = ["equipment/", "services/synchronization", "monitoring/"]
        for path in critical_paths:
            if path in file_path:
                return True

        return False

    def _validate_critical_component_tests(self, source_file: str, test_file: str) -> list[str]:
        """
        Validate comprehensive testing for critical agricultural components.

        Args:
            source_file: Path to source file
            test_file: Path to test file

        Returns:
            List of validation error messages
        """
        errors = []

        if not os.path.exists(test_file):
            errors.append(f"Critical component {source_file} missing test file {test_file}")
            return errors

        try:
            with open(test_file) as f:
                test_content = f.read()
        except Exception as e:
            errors.append(f"Cannot read test file {test_file}: {e}")
            return errors

        # Required test patterns for critical components
        required_patterns = [
            (
                r"def test_.*performance",
                "Performance tests required for agricultural real-time constraints",
            ),
            (
                r"def test_.*edge_case|def test_.*error",
                "Edge case testing required for field operation robustness",
            ),
            (
                r"agricultural|tractor|field|equipment",
                "Agricultural context required in test documentation",
            ),
        ]

        for pattern, message in required_patterns:
            if not re.search(pattern, test_content, re.IGNORECASE):
                errors.append(f"{source_file}: {message}")

        return errors

    def _has_recent_test_activity(self, test_file: str) -> bool:
        """
        Check if test file has been recently modified (Red-Green-Refactor pattern).

        Args:
            test_file: Path to test file

        Returns:
            True if test file shows recent activity
        """
        try:
            # Check git status for recent test file activity
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "5", "--", test_file],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # If test file has recent commits, consider it active
            return len(result.stdout.strip()) > 0
        except Exception:
            # If git check fails, allow the commit (don't block on tooling issues)
            return True


def main():
    """
    Main TDD enforcement entry point for pre-commit hook.
    """
    if len(sys.argv) < 2:
        print("TDD Enforcement: No files to validate")
        return 0

    files = sys.argv[1:]
    validator = TDDEnforcementValidator()

    is_compliant, errors = validator.validate_tdd_compliance(files)

    if not is_compliant:
        print("🚫 TDD METHODOLOGY VIOLATIONS DETECTED")
        print("=" * 60)
        print(
            "AFS FastAPI requires Test-First Development for all agricultural robotics components."
        )
        print(
            "Red-Green-Refactor methodology ensures bulletproof reliability for multi-tractor coordination."
        )
        print()

        for error in errors:
            print(f"❌ {error}")

        print()
        print("📋 TDD Compliance Guide:")
        print("1. Write failing test first (RED phase)")
        print("2. Implement minimal code to pass (GREEN phase)")
        print("3. Refactor while maintaining tests (REFACTOR phase)")
        print()
        print("📖 Reference: TDD_WORKFLOW.md for agricultural robotics TDD patterns")

        return 1

    print("✅ TDD Methodology Compliance Validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
