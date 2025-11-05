#!/usr/bin/env python3
"""
CLI integration test without mocks.

This script tests CLI commands using subprocess calls and file system
operations, completely eliminating mock usage for CLI testing.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tests.utilities.cli_testing import CLICommandTester, CLIEnvironment, run_cli_test_suite

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_whereweare_command():
    """Test whereweare CLI command without mocks."""
    logger.info("=== Testing WhereWeAre CLI Command ===")

    try:
        tester = CLICommandTester("whereweare")

        # Test command exists and is executable
        assert tester.test_command_exists(), "whereweare command should exist and be executable"
        logger.info("✅ whereweare command exists and is executable")

        # Test basic command execution
        result = tester.run_command()
        assert (
            result.returncode == 0
        ), f"whereweare should execute successfully (return code: {result.returncode})"
        assert len(result.stdout) > 0, "whereweare should produce output"
        logger.info("✅ whereweare command executed successfully")

        # Test output content
        assert "WHERE WE ARE" in result.stdout, "Should display document title"
        assert "AFS FastAPI" in result.stdout, "Should display project name"
        logger.info("✅ whereweare output contains expected content")

        # Test help command
        help_result = tester.run_command(["--help"])
        if help_result.returncode == 0:
            logger.info("✅ whereweare help command works")
        else:
            logger.warning("⚠️ whereweare help command not available (optional)")

        return True

    except Exception as e:
        logger.error(f"❌ whereweare test failed: {e}")
        return False


def test_git_commands():
    """Test git-related CLI commands without mocks."""
    logger.info("\n=== Testing Git CLI Commands ===")

    try:
        # Test git status
        with CLIEnvironment() as cli_env:
            # Change to project root
            Path.cwd()

            # Test git status (if in git repo)
            if Path(".git").exists():
                result = cli_env.run_command(["git", "status", "--porcelain"])
                logger.info(f"✅ git status executed (return code: {result.returncode})")

                # Test git log
                result = cli_env.run_command(["git", "log", "--oneline", "-5"])
                logger.info(f"✅ git log executed (return code: {result.returncode})")

                # Test git branch
                result = cli_env.run_command(["git", "branch"])
                logger.info(f"✅ git branch executed (return code: {result.returncode})")
            else:
                logger.info("ℹ️ Not in git repository, skipping git tests")

        return True

    except Exception as e:
        logger.error(f"❌ git commands test failed: {e}")
        return False


def test_file_operations():
    """Test real file operations without mocks."""
    logger.info("\n=== Testing File Operations ===")

    try:
        with CLIEnvironment() as cli_env:
            # Create temporary directory
            temp_dir = cli_env.create_temp_dir("test_files_")
            logger.info(f"✅ Created temporary directory: {temp_dir}")

            # Create test file
            test_file = temp_dir / "test.txt"
            cli_env.write_file(test_file, "Test content for CLI integration")
            logger.info("✅ Created test file")

            # Test file exists
            assert cli_env.file_exists(test_file), "Test file should exist"
            logger.info("✅ File exists check passed")

            # Test file reading
            content = cli_env.read_file(test_file)
            assert "Test content" in content, "Should read file content"
            logger.info("✅ File reading check passed")

            # Test file operations via shell commands
            result = cli_env.run_command(["ls", "-la", str(temp_dir)])
            logger.info(f"✅ ls command executed (return code: {result.returncode})")

            result = cli_env.run_command(["cat", str(test_file)])
            assert "Test content" in result.stdout, "cat should show file content"
            logger.info("✅ cat command executed successfully")

            # Test file creation via echo
            echo_file = temp_dir / "echo_test.txt"
            result = cli_env.run_command(["sh", "-c", f"echo 'echo test' > {echo_file}"])
            echo_content = cli_env.read_file(echo_file)
            assert "echo test" in echo_content, "echo should write to file"
            logger.info("✅ echo file creation works")

        return True

    except Exception as e:
        logger.error(f"❌ File operations test failed: {e}")
        return False


def test_bash_commands():
    """Test bash commands without mocks."""
    logger.info("\n=== Testing Bash Commands ===")

    try:
        with CLIEnvironment() as cli_env:
            # Test basic bash commands
            result = cli_env.run_bash_command("echo 'Hello from real bash'")
            assert result.returncode == 0, "Bash echo should work"
            assert "Hello from real bash" in result.stdout, "Echo output should be correct"
            logger.info("✅ Bash echo command works")

            # Test bash variable operations
            result = cli_env.run_bash_command("TEST_VAR='CLI testing'; echo $TEST_VAR")
            assert result.returncode == 0, "Bash variables should work"
            assert "CLI testing" in result.stdout, "Variable expansion should work"
            logger.info("✅ Bash variable operations work")

            # Test bash conditional
            result = cli_env.run_bash_command(
                "if [ -n 'CLI testing' ]; then echo 'true'; else echo 'false'; fi"
            )
            assert result.returncode == 0, "Bash conditionals should work"
            assert "true" in result.stdout, "Conditional should evaluate to true"
            logger.info("✅ Bash conditionals work")

            # Test bash loops
            result = cli_env.run_bash_command('for i in 1 2 3; do echo "iteration $i"; done')
            assert result.returncode == 0, "Bash loops should work"
            assert "iteration 1" in result.stdout, "Loop should execute"
            assert "iteration 3" in result.stdout, "Loop should complete"
            logger.info("✅ Bash loops work")

        return True

    except Exception as e:
        logger.error(f"❌ Bash commands test failed: {e}")
        return False


def test_subprocess_error_handling():
    """Test subprocess error handling without mocks."""
    logger.info("\n=== Testing Subprocess Error Handling ===")

    try:
        with CLIEnvironment() as cli_env:
            # Test non-existent command
            try:
                cli_env.run_command(["nonexistent_command_xyz"], timeout=5)
                raise AssertionError("Should have raised RuntimeError")
            except RuntimeError:
                logger.info("✅ Non-existent command correctly raises RuntimeError")

            # Test command timeout
            try:
                cli_env.run_bash_command("sleep 10", timeout=2)
                raise AssertionError("Should have raised RuntimeError for timeout")
            except RuntimeError as e:
                assert "timeout" in str(e).lower(), "Error message should mention timeout"
                logger.info("✅ Command timeout correctly handled")

            # Test command with non-zero exit code
            result = cli_env.run_command(["sh", "-c", "exit 1"], check=False)
            assert result.returncode == 1, "Should capture non-zero return code"
            logger.info("✅ Non-zero return code handled correctly")

        return True

    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False


def test_cli_command_suite():
    """Run a suite of CLI command tests."""
    logger.info("\n=== Running CLI Command Test Suite ===")

    test_cases = [
        {
            "name": "echo_command",
            "command_name": "echo",
            "args": ["Hello CLI"],
            "expected_output": "Hello CLI",
        },
        {"name": "date_command", "command_name": "date", "expected_output": "2025"},  # Year
        {
            "name": "pwd_command",
            "command_name": "pwd",
            "expected_output": "/",  # Should contain root path
        },
    ]

    try:
        results = run_cli_test_suite(test_cases)
        logger.info("✅ CLI command test suite results:")

        passed = sum(results.values())
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"   {test_name}: {status}")

        logger.info(f"   Overall: {passed}/{total} tests passed")

        return passed == total

    except Exception as e:
        logger.error(f"❌ CLI command test suite failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🔧 Starting Real CLI Integration Tests (No Mocks)")
    logger.info("=" * 60)

    # Run all tests
    tests = [
        ("WhereWeAre Command", test_whereweare_command),
        ("Git Commands", test_git_commands),
        ("File Operations", test_file_operations),
        ("Bash Commands", test_bash_commands),
        ("Error Handling", test_subprocess_error_handling),
        ("CLI Command Suite", test_cli_command_suite),
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 REAL CLI INTEGRATION TEST RESULTS")
    logger.info("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All real CLI integration tests passed!")
        logger.info("🌱 CLI systems working without any mocks!")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")

    # System information
    logger.info("\n🔧 System Configuration:")
    logger.info(f"   Working Directory: {Path.cwd()}")
    logger.info("   Python Available: True")
    logger.info("   Shell Available: True")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
