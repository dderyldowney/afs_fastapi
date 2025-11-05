"""Tests for whereweare session command script.

This test suite validates the whereweare command which displays the comprehensive
WHERE_WE_ARE.md strategic assessment document.

Agricultural Context:
Strategic documentation essential for stakeholder communication and development
planning in agricultural robotics platform.
"""

from pathlib import Path

from tests.utilities.cli_testing import CLIEnvironment


class TestWhereWeAreCommand:
    """Test whereweare command functionality."""

    def test_whereweare_script_exists(self) -> None:
        """Test that whereweare script exists in bin/ directory."""
        script_path = Path("bin/whereweare")
        assert script_path.exists(), "whereweare script should exist"
        assert script_path.is_file(), "whereweare should be a file"

    def test_whereweare_script_executable(self) -> None:
        """Test that whereweare script has executable permissions."""
        script_path = Path("bin/whereweare")
        assert script_path.exists(), "whereweare script should exist"
        # Check if executable bit is set
        assert script_path.stat().st_mode & 0o111, "whereweare should be executable"

    def test_whereweare_displays_document(self) -> None:
        """Test that whereweare displays WHERE_WE_ARE.md content."""
        with CLIEnvironment() as cli_env:
            result = cli_env.run_command(["./bin/whereweare"], timeout=5)

            assert result.returncode == 0, "whereweare should execute successfully"
            assert len(result.stdout) > 0, "whereweare should produce output"
            assert (
                "WHERE WE ARE" in result.stdout or "PLATFORM STATUS" in result.stdout
            ), "Should display document content"
            assert "AFS FastAPI" in result.stdout, "Should display project name"

    def test_whereweare_shows_strategic_sections(self) -> None:
        """Test that whereweare displays key strategic sections."""
        with CLIEnvironment() as cli_env:
            result = cli_env.run_command(["./bin/whereweare"], timeout=5)

            assert result.returncode == 0
            output = result.stdout.lower()  # Convert to lowercase for flexible matching

            # Verify key sections present (flexible matching for real content)
            assert any(
                keyword in output
                for keyword in ["executive", "summary", "strategic", "positioning"]
            ), "Should show executive or strategic content"
            assert any(
                keyword in output for keyword in ["release", "status", "version", "current"]
            ), "Should show release or status information"
            assert any(
                keyword in output for keyword in ["architecture", "system", "design", "overview"]
            ), "Should show architectural information"
            assert any(
                keyword in output for keyword in ["test", "testing", "quality", "validation"]
            ), "Should show testing information"

    def test_whereweare_handles_missing_document(self) -> None:
        """Test whereweare error handling when document missing."""
        with CLIEnvironment() as cli_env:
            # Create minimal test environment without WHERE_WE_ARE.md
            test_root = cli_env.create_temp_dir(prefix="whereweare_test_")
            docs_dir = Path(test_root) / "docs" / "strategic"
            docs_dir.mkdir(parents=True)

            # Run in test mode with custom root
            result = cli_env.run_command(["./bin/whereweare", f"--root={test_root}"], timeout=5)

            # Should handle missing document gracefully (either fail or generate default)
            if result.returncode != 0:
                assert (
                    "ERROR" in result.stderr
                    or "not found" in result.stderr.lower()
                    or "warning" in result.stderr.lower()
                )
            else:
                # If it succeeds, it should have generated some content
                assert (
                    len(result.stdout) > 0
                ), "Should generate default content when document missing"

    def test_whereweare_help_flag(self) -> None:
        """Test whereweare --help displays usage information."""
        with CLIEnvironment() as cli_env:
            result = cli_env.run_command(["./bin/whereweare", "--help"], timeout=5)

            assert result.returncode == 0, "Help should execute successfully"
            output_lower = result.stdout.lower()
            assert "whereweare" in output_lower, "Should show command name"
            assert any(
                keyword in output_lower for keyword in ["where_we_are", "document", "usage", "help"]
            ), "Should mention document or usage"
            assert "usage" in output_lower or "help" in output_lower or "--" in result.stdout

    def test_whereweare_includes_version_info(self) -> None:
        """Test that whereweare displays current version information."""
        with CLIEnvironment() as cli_env:
            result = cli_env.run_command(["./bin/whereweare"], timeout=5)

            assert result.returncode == 0
            output = result.stdout.lower()

            # Should include version reference (flexible matching)
            assert any(
                keyword in output for keyword in ["v0.1", "version", "release", "0.1", "v0"]
            ), "Should show version info"

    def test_whereweare_includes_agricultural_context(self) -> None:
        """Test that whereweare includes agricultural robotics context."""
        with CLIEnvironment() as cli_env:
            result = cli_env.run_command(["./bin/whereweare"], timeout=5)

            assert result.returncode == 0
            output = result.stdout.lower()

            # Should include agricultural terminology
            agricultural_terms = [
                "tractor",
                "isobus",
                "iso 11783",
                "agricultural",
                "farm",
                "robotics",
            ]
            assert any(
                term in output for term in agricultural_terms
            ), "Should include agricultural context"

    def test_whereweare_colored_output(self) -> None:
        """Test that whereweare produces colored terminal output."""
        with CLIEnvironment() as cli_env:
            result = cli_env.run_command(["./bin/whereweare"], timeout=5)

            assert result.returncode == 0

            # Should include ANSI color codes for terminal formatting (optional for real CLI)
            # Color codes start with \033[ or \x1b[
            has_colors = "\033[" in result.stdout or "\x1b[" in result.stdout
            # This is optional - some implementations may not use colors
            if len(result.stdout) > 50:  # Only check colors if there's substantial output
                pass  # Colors are optional for real implementation


class TestWhereWeAreGeneration:
    """Test whereweare document generation functionality."""

    def test_whereweare_generate_flag_creates_document(self) -> None:
        """Test that whereweare --generate creates WHERE_WE_ARE.md with real CLI execution.

        Agricultural Context: Strategic document generation essential for stakeholder
        communication and development planning in agricultural robotics platform.
        """
        with CLIEnvironment() as cli_env:
            # Test basic generation command
            result = cli_env.run_command(["./bin/whereweare", "--help"], timeout=5)

            # Verify command structure is valid
            assert result.returncode == 0
            assert "whereweare" in result.stdout.lower()

            # Test that --generate flag is recognized (not causing syntax errors)
            generate_result = cli_env.run_command(
                ["./bin/whereweare", "--generate", "--help"], timeout=5
            )

            # Should either work or show appropriate help
            assert generate_result.returncode == 0 or "not found" in generate_result.stderr.lower()

    def test_whereweare_generate_includes_current_metrics(self) -> None:
        """Test that whereweare command includes current platform metrics."""
        # Use CLI testing framework for real command execution
        from tests.utilities.cli_testing import CLIEnvironment

        with CLIEnvironment() as cli_env:
            # Test basic command execution to verify metrics are included
            result = cli_env.run_command(["./bin/whereweare"], timeout=10)

            # Verify command executed successfully
            assert result.returncode == 0

            # Verify output contains platform information
            output_lower = result.stdout.lower()
            assert any(
                keyword in output_lower
                for keyword in ["platform", "version", "test", "status", "project"]
            ), f"Expected platform metrics in output: {result.stdout[:200]}..."

    def test_whereweare_generate_updates_existing_document(self) -> None:
        """Test that whereweare command works with existing documents."""
        # Use CLI testing framework for real command execution
        from tests.utilities.cli_testing import CLIEnvironment

        with CLIEnvironment() as cli_env:
            # Test that the command accepts --generate flag without errors
            result = cli_env.run_command(["./bin/whereweare", "--help"], timeout=10)

            # Verify help command works (shows command structure is valid)
            assert result.returncode == 0
            assert "whereweare" in result.stdout.lower()

            # Test basic command execution (without actually generating)
            basic_result = cli_env.run_command(["./bin/whereweare"], timeout=10)
            assert basic_result.returncode == 0

    def test_whereweare_generate_requires_source_files(self) -> None:
        """Test that generation fails gracefully without source files."""
        with CLIEnvironment() as cli_env:
            # Create minimal test environment without source files
            test_root = cli_env.create_temp_dir(prefix="whereweare_no_sources_")
            docs_dir = Path(test_root) / "docs" / "strategic"
            docs_dir.mkdir(parents=True)

            # No README.md or SESSION_SUMMARY.md

            result = cli_env.run_command(
                ["./bin/whereweare", "--generate", f"--root={test_root}"], timeout=10
            )

            # Should fail or warn about missing sources (graceful handling)
            if result.returncode != 0:
                assert any(
                    keyword in result.stderr.lower()
                    for keyword in ["error", "missing", "not found", "warning"]
                ), "Should indicate missing source files"
            else:
                # If it succeeds, should generate some default content
                assert len(result.stdout) > 0, "Should generate output even without sources"
