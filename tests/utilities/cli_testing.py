"""
CLI testing utilities without mocks.

This module provides utilities for testing CLI commands using subprocess
calls and file system operations, replacing mocks with actual system interactions.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class CLIEnvironment:
    """CLI environment for testing with system calls.

    This class provides a clean environment for CLI testing with
    subprocess calls and file system operations.
    """

    def __init__(self, cleanup: bool = True) -> None:
        """Initialize CLI environment.

        Parameters
        ----------
        cleanup : bool, default True
            Whether to cleanup temporary files and directories
        """
        self.cleanup = cleanup
        self._temp_dirs: list[Path] = []
        self._temp_files: list[Path] = []
        self._env_vars: dict[str, str] = {}

    def create_temp_dir(self, prefix: str = "test_cli_") -> Path:
        """Create a temporary directory for testing.

        Parameters
        ----------
        prefix : str, default "test_cli_"
            Prefix for temporary directory name

        Returns
        -------
        Path
            Path to created temporary directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self._temp_dirs.append(temp_dir)
        return temp_dir

    def create_temp_file(self, content: str, suffix: str = ".tmp") -> Path:
        """Create a temporary file for testing.

        Parameters
        ----------
        content : str
            Content to write to file
        suffix : str, default ".tmp"
            File suffix

        Returns
        -------
        Path
            Path to created temporary file
        """
        temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()

        file_path = Path(temp_file.name)
        self._temp_files.append(file_path)
        return file_path

    def set_env_var(self, key: str, value: str) -> None:
        """Set environment variable for CLI testing.

        Parameters
        ----------
        key : str
            Environment variable name
        value : str
            Environment variable value
        """
        old_value = os.environ.get(key)
        os.environ[key] = value
        self._env_vars[key] = old_value if old_value is not None else ""

    def run_command(
        self,
        args: list[str] | str,
        cwd: Path | str | None = None,
        timeout: int = 30,
        capture_output: bool = True,
        check: bool = False,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess:
        """Run a CLI command with real subprocess.

        Parameters
        ----------
        args : List[str] | str
            Command arguments
        cwd : Path | str, optional
            Working directory
        timeout : int, default 30
            Command timeout in seconds
        capture_output : bool, default True
            Whether to capture stdout/stderr
        check : bool, default False
            Whether to raise exception on non-zero return
        **kwargs : Any
            Additional subprocess.run arguments

        Returns
        -------
        subprocess.CompletedProcess
            Process result
        """
        if isinstance(args, str):
            args = [args]

        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                check=False,  # We'll handle return code checking manually
                **kwargs,
            )

            if check and result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, args, result.stdout, result.stderr
                )

            return result

        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Command timed out after {timeout}s: {' '.join(args)}") from e
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {' '.join(args)} - {e}") from e

    def run_bash_command(
        self, command: str, cwd: Path | str | None = None, timeout: int = 30, **kwargs: Any
    ) -> subprocess.CompletedProcess:
        """Run a bash command.

        Parameters
        ----------
        command : str
            Bash command to execute
        cwd : Path | str, optional
            Working directory
        timeout : int, default 30
            Command timeout in seconds
        **kwargs : Any
            Additional subprocess.run arguments

        Returns
        -------
        subprocess.CompletedProcess
            Process result
        """
        return self.run_command(["bash", "-c", command], cwd=cwd, timeout=timeout, **kwargs)

    def make_file_executable(self, file_path: Path | str) -> None:
        """Make a file executable.

        Parameters
        ----------
        file_path : Path | str
            Path to file to make executable
        """
        path = Path(file_path)
        current_permissions = path.stat().st_mode
        path.chmod(current_permissions | 0o755)

    def file_exists(self, file_path: Path | str) -> bool:
        """Check if file exists.

        Parameters
        ----------
        file_path : Path | str
            Path to check

        Returns
        -------
        bool
            True if file exists
        """
        return Path(file_path).exists()

    def read_file(self, file_path: Path | str) -> str:
        """Read file contents.

        Parameters
        ----------
        file_path : Path | str
            Path to file

        Returns
        -------
        str
            File contents
        """
        return Path(file_path).read_text()

    def write_file(self, file_path: Path | str, content: str) -> None:
        """Write content to file.

        Parameters
        ----------
        file_path : Path | str
            Path to file
        content : str
            Content to write
        """
        Path(file_path).write_text(content)

    def cleanup_all(self) -> None:
        """Clean up all temporary files and directories."""
        # Clean up temporary files
        for temp_file in self._temp_files:
            try:
                temp_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors

        # Clean up temporary directories
        for temp_dir in self._temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # Ignore cleanup errors

        # Restore environment variables
        for key, old_value in self._env_vars.items():
            if old_value:
                os.environ[key] = old_value
            else:
                os.environ.pop(key, None)

        self._temp_files.clear()
        self._temp_dirs.clear()
        self._env_vars.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.cleanup:
            self.cleanup_all()


class CLICommandTester:
    """Utility for testing specific CLI commands."""

    def __init__(self, command_name: str, command_path: str | None = None) -> None:
        """Initialize CLI command tester.

        Parameters
        ----------
        command_name : str
            Name of the CLI command
        command_path : str, optional
            Path to command executable. If None, uses default paths.
        """
        self.command_name = command_name
        self.command_path = self._find_command_path(command_path)

    def _find_command_path(self, provided_path: str | None) -> Path:
        """Find the command path using multiple strategies.

        Parameters
        ----------
        provided_path : str | None
            Explicitly provided path

        Returns
        -------
        Path
            Path to command executable
        """
        if provided_path:
            return Path(provided_path)

        # Try common locations
        search_paths = [
            Path(f"bin/{self.command_name}"),
            Path(f"scripts/{self.command_name}"),
            Path(f"cli/{self.command_name}"),
            Path(self.command_name),
        ]

        for search_path in search_paths:
            if search_path.exists() and search_path.is_file():
                return search_path

        raise FileNotFoundError(f"Command not found: {self.command_name}")

    def run_command(
        self, args: list[str] | None = None, **kwargs: Any
    ) -> subprocess.CompletedProcess:
        """Run the CLI command.

        Parameters
        ----------
        args : List[str], optional
            Additional arguments
        **kwargs : Any
            Additional run arguments

        Returns
        -------
        subprocess.CompletedProcess
            Process result
        """
        cmd_args = [str(self.command_path)]
        if args:
            cmd_args.extend(args)

        with CLIEnvironment() as cli_env:
            return cli_env.run_command(cmd_args, **kwargs)

    def test_command_exists(self) -> bool:
        """Test that the command exists and is executable.

        Returns
        -------
        bool
            True if command exists and is executable
        """
        return (
            self.command_path.exists()
            and self.command_path.is_file()
            and os.access(self.command_path, os.X_OK)
        )

    def test_command_help(self) -> subprocess.CompletedProcess:
        """Test command help output.

        Returns
        -------
        subprocess.CompletedProcess
            Process result
        """
        return self.run_command(["--help"])

    def test_command_version(self) -> subprocess.CompletedProcess:
        """Test command version output.

        Returns
        -------
        subprocess.CompletedProcess
            Process result
        """
        return self.run_command(["--version"])


# Convenience functions for common CLI testing patterns
def test_cli_command(
    command_name: str,
    args: list[str] | None = None,
    expected_output: str | None = None,
    expected_return_code: int = 0,
    **kwargs: Any,
) -> bool:
    """Test a CLI command with simple assertions.

    Parameters
    ----------
    command_name : str
        Name of the CLI command
    args : List[str], optional
        Command arguments
    expected_output : str, optional
        Expected output substring
    expected_return_code : int, default 0
        Expected return code
    **kwargs : Any
        Additional arguments

    Returns
    -------
    bool
        True if test passes
    """
    try:
        tester = CLICommandTester(command_name)

        # Test command exists
        if not tester.test_command_exists():
            return False

        # Run command
        result = tester.run_command(args, **kwargs)

        # Check return code
        if result.returncode != expected_return_code:
            return False

        # Check output
        if expected_output and expected_output not in result.stdout:
            return False

        return True

    except Exception:
        return False


def run_cli_test_suite(test_cases: list[dict[str, Any]]) -> dict[str, bool]:
    """Run a suite of CLI tests.

    Parameters
    ----------
    test_cases : List[Dict[str, Any]]
        List of test case dictionaries

    Returns
    -------
    Dict[str, bool]
        Results of test cases
    """
    results = {}

    for i, test_case in enumerate(test_cases):
        test_name = test_case.get("name", f"test_{i+1}")
        success = test_cli_command(**test_case)
        results[test_name] = success

    return results


# Backward compatibility
RealCLIEnvironment = CLIEnvironment
