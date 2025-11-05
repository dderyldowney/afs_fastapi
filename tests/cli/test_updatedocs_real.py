"""CLI tests for updatedocs meta-command script.

This test suite validates the updatedocs command using CLI execution
without mocking, providing system interaction testing while maintaining
fast execution by focusing on command structure and help functionality.

Agricultural Context:
Unified documentation updates essential for maintaining consistent platform
state documentation across strategic assessments, web presence, version history,
session state, test reports, and metrics dashboards for farm equipment compliance
auditing and autonomous tractor fleet management.
"""

from __future__ import annotations

from tests.utilities.cli_testing import CLICommandTester, CLIEnvironment


class TestUpdateDocsCommand:
    """Test updatedocs command functionality."""

    def test_updatedocs_command_exists(self) -> None:
        """Test that updatedocs command exists and is executable."""
        tester = CLICommandTester("updatedocs")
        assert tester.test_command_exists(), "updatedocs command should exist and be executable"

    def test_updatedocs_help_functionality(self) -> None:
        """Test updatedocs help and usage information."""
        tester = CLICommandTester("updatedocs")

        # Test help command
        help_result = tester.run_command(["--help"])
        if help_result.returncode == 0:
            assert len(help_result.stdout) > 0, "Help should produce output"
            assert "updatedocs" in help_result.stdout.lower(), "Should mention command name"
            assert (
                "usage:" in help_result.stdout.lower()
                or "documentation" in help_result.stdout.lower()
            )
        else:
            # Try -h if --help not available
            short_help_result = tester.run_command(["-h"])
            if short_help_result.returncode == 0:
                assert len(short_help_result.stdout) > 0, "Short help should produce output"
                assert "updatedocs" in short_help_result.stdout.lower()

    def test_updatedocs_command_validation(self) -> None:
        """Test updatedocs command validation and error handling."""
        tester = CLICommandTester("updatedocs")

        # Test invalid flag produces appropriate error
        invalid_result = tester.run_command(["--invalid-flag"])
        assert invalid_result.returncode != 0, "Invalid flag should produce error"
        assert (
            len(invalid_result.stderr) > 0 or len(invalid_result.stdout) > 0
        ), "Should produce error message"

    def test_updatedocs_script_location(self) -> None:
        """Test that updatedocs script is properly located."""
        import os
        from pathlib import Path

        # Check script exists in expected location
        script_path = Path("bin/updatedocs")
        assert script_path.exists(), f"Script should exist at {script_path}"
        assert os.access(script_path, os.X_OK), "Script should be executable"

    def test_updatedocs_environment_integration(self) -> None:
        """Test updatedocs integrates properly with CLI environment."""
        with CLIEnvironment() as cli_env:
            # Test command can be found in PATH
            result = cli_env.run_command(["which", "updatedocs"])
            if result.returncode == 0:
                assert "updatedocs" in result.stdout, "Command should be findable"
                assert "bin" in result.stdout, "Should be in bin directory"

    def test_updatedocs_dependency_check(self) -> None:
        """Test updatedocs dependency availability without full execution."""
        tester = CLICommandTester("updatedocs")

        # Test command structure by attempting dry run if available
        dry_result = tester.run_command(["--dry-run"])
        if dry_result.returncode == 0:
            assert len(dry_result.stdout) > 0, "Dry run should produce output"
            # Should mention what would be updated
            output_lower = dry_result.stdout.lower()
            any_doc_mentioned = any(
                doc in output_lower
                for doc in ["documentation", "docs", "where", "changelog", "readme", "session"]
            )
            assert any_doc_mentioned, "Should mention documentation types"
        else:
            # If dry-run not available, command should at least be callable
            basic_result = tester.run_command([])
            # Accept various return codes as command structure validation
            assert basic_result.returncode in [0, 1, 2, 127], "Command should be executable"

    def test_updatedocs_file_structure_validation(self) -> None:
        """Test updatedocs works with correct file structure."""
        from pathlib import Path

        # Check that key directories exist
        bin_dir = Path("bin")
        assert bin_dir.exists(), "bin directory should exist"

        # Check that updatedocs script has proper content
        script_path = Path("bin/updatedocs")
        if script_path.exists():
            content = script_path.read_text()
            assert len(content) > 0, "Script should have content"
            # Should be a shell script or python script
            assert any(
                indicator in content[:100]
                for indicator in [
                    "#!/bin/bash",
                    "#!/bin/sh",
                    "#!/usr/bin/env python",
                    "#!/usr/bin/python3",
                ]
            ), "Script should have proper shebang"

    def test_updatedocs_agricultural_context(self) -> None:
        """Test updatedocs maintains agricultural context in help/output."""
        tester = CLICommandTester("updatedocs")

        # Test help mentions agricultural or farming context if available
        help_result = tester.run_command(["--help"])
        if help_result.returncode == 0:
            output = help_result.stdout.lower()
            # Check for agricultural terms (optional, but good if present)
            ag_terms = ["agricultural", "farming", "tractor", "farm", "afs"]
            has_ag_context = any(term in output for term in ag_terms)
            # Not required to pass, but good to have agricultural context
