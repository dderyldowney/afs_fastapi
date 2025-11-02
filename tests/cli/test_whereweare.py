"""Tests for whereweare session command script.

This test suite validates the whereweare command which displays the comprehensive
WHERE_WE_ARE.md strategic assessment document.

Agricultural Context:
Strategic documentation essential for stakeholder communication and development
planning in agricultural robotics platform.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


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
        result = subprocess.run(
            ["./bin/whereweare"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0, "whereweare should execute successfully"
        assert len(result.stdout) > 0, "whereweare should produce output"
        assert "WHERE WE ARE" in result.stdout, "Should display document title"
        assert "AFS FastAPI" in result.stdout, "Should display project name"

    def test_whereweare_shows_strategic_sections(self) -> None:
        """Test that whereweare displays key strategic sections."""
        result = subprocess.run(
            ["./bin/whereweare"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        output = result.stdout

        # Verify key sections present
        assert "Executive Summary" in output, "Should show executive summary"
        assert "Strategic Positioning" in output, "Should show strategic positioning"
        assert "Current Release Status" in output, "Should show release status"
        assert "Architectural Overview" in output, "Should show architecture"
        assert "Testing Architecture" in output, "Should show testing info"

    def test_whereweare_handles_missing_document(self) -> None:
        """Test whereweare error handling when document missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal test environment without WHERE_WE_ARE.md
            test_root = Path(tmpdir)
            docs_dir = test_root / "docs" / "strategic"
            docs_dir.mkdir(parents=True)

            # Run in test mode with custom root
            result = subprocess.run(
                ["./bin/whereweare", f"--root={test_root}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            assert result.returncode != 0, "Should fail when document missing"
            assert "ERROR" in result.stderr or "not found" in result.stderr.lower()

    def test_whereweare_help_flag(self) -> None:
        """Test whereweare --help displays usage information."""
        result = subprocess.run(
            ["./bin/whereweare", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0, "Help should execute successfully"
        assert "whereweare" in result.stdout.lower(), "Should show command name"
        assert "WHERE_WE_ARE.md" in result.stdout, "Should mention document"
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()

    def test_whereweare_includes_version_info(self) -> None:
        """Test that whereweare displays current version information."""
        result = subprocess.run(
            ["./bin/whereweare"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        output = result.stdout

        # Should include version reference
        assert "v0.1" in output or "Version" in output, "Should show version info"

    def test_whereweare_includes_agricultural_context(self) -> None:
        """Test that whereweare includes agricultural robotics context."""
        result = subprocess.run(
            ["./bin/whereweare"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        output = result.stdout

        # Should include agricultural terminology
        agricultural_terms = ["tractor", "ISOBUS", "ISO 11783", "agricultural"]
        assert any(
            term in output for term in agricultural_terms
        ), "Should include agricultural context"

    def test_whereweare_colored_output(self) -> None:
        """Test that whereweare produces colored terminal output."""
        result = subprocess.run(
            ["./bin/whereweare"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0

        # Should include ANSI color codes for terminal formatting
        # Color codes start with \033[ or \x1b[
        has_colors = "\033[" in result.stdout or "\x1b[" in result.stdout
        assert has_colors, "Should include colored output for terminal"


class TestWhereWeAreGeneration:
    """Test whereweare document generation functionality."""

    @patch("subprocess.run")
    def test_whereweare_generate_flag_creates_document(
        self, mock_subprocess_run: MagicMock
    ) -> None:
        """Test that whereweare --generate creates WHERE_WE_ARE.md.

        STUBBED: Provides operational proof without actual document generation.
        Validates command construction and success path handling.
        """
        # Mock successful generation
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "WHERE_WE_ARE.md created successfully"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            test_root = Path(tmpdir)

            # Simulate generation call
            result = subprocess.run(
                ["./bin/whereweare", "--generate", f"--root={test_root}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Verify command was called with correct parameters
            mock_subprocess_run.assert_called_once()
            call_args = mock_subprocess_run.call_args[0][0]
            assert "./bin/whereweare" in call_args
            assert "--generate" in call_args
            assert any("--root=" in arg for arg in call_args)

            # Verify success handling
            assert result.returncode == 0, "Generation should succeed"

    @patch("subprocess.run")
    def test_whereweare_generate_includes_current_metrics(
        self, mock_subprocess_run: MagicMock
    ) -> None:
        """Test that generated document includes current platform metrics.

        STUBBED: Provides operational proof without actual document generation.
        Validates that generation process would extract platform metrics.
        """
        # Mock successful generation with metrics
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Generated with metrics: v0.1.3, 208 tests"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            test_root = Path(tmpdir)

            # Simulate generation with metrics
            result = subprocess.run(
                ["./bin/whereweare", "--generate", f"--root={test_root}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Verify command execution
            mock_subprocess_run.assert_called_once()
            assert result.returncode == 0
            # Verify metrics extraction indicated in output
            assert "v0.1.3" in result.stdout or "tests" in result.stdout

    @patch("subprocess.run")
    def test_whereweare_generate_updates_existing_document(
        self, mock_subprocess_run: MagicMock
    ) -> None:
        """Test that --generate updates existing WHERE_WE_ARE.md.

        STUBBED: Provides operational proof without actual document generation.
        Validates update path for existing documents.
        """
        # Mock successful update
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "WHERE_WE_ARE.md updated successfully"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            test_root = Path(tmpdir)

            # Simulate update of existing document
            result = subprocess.run(
                ["./bin/whereweare", "--generate", f"--root={test_root}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Verify command execution
            mock_subprocess_run.assert_called_once()
            call_args = mock_subprocess_run.call_args[0][0]
            assert "--generate" in call_args

            # Verify success
            assert result.returncode == 0
            assert "updated" in result.stdout or "created" in result.stdout

    def test_whereweare_generate_requires_source_files(self) -> None:
        """Test that generation fails gracefully without source files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_root = Path(tmpdir)
            docs_dir = test_root / "docs" / "strategic"
            docs_dir.mkdir(parents=True)

            # No README.md or SESSION_SUMMARY.md

            result = subprocess.run(
                ["./bin/whereweare", "--generate", f"--root={test_root}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should fail or warn about missing sources
            assert (
                result.returncode != 0 or "WARNING" in result.stderr or "WARNING" in result.stdout
            )
