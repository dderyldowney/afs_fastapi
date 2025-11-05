import subprocess


def test_example_command_clear_error_message():
    command_path = "python afs_fastapi/scripts/example_command.py"

    # Test the failing case
    result = subprocess.run(
        f"{command_path} fail", capture_output=True, text=True, check=False, shell=True
    )

    assert result.returncode != 0, "Command unexpectedly succeeded."
    assert (
        "ERROR: This is a simulated failure with a clear message." in result.stderr
    ), f"Error message is not clear: {result.stderr}"
    # Allow for compliance enforcement output in stdout
    if result.stdout.strip():
        assert (
            "COMPLIANCE" in result.stdout or "Agent directives" in result.stdout
        ), f"Unexpected stdout: {result.stdout}"

    # Test the passing case
    result_pass = subprocess.run(
        command_path, capture_output=True, text=True, check=True, shell=True
    )
    assert result_pass.returncode == 0, "Command unexpectedly failed."
    # Check for expected success message, allowing for compliance output
    stdout_lines = result_pass.stdout.strip().split("\n")
    success_line = next(
        (line for line in stdout_lines if "Command executed successfully." in line), None
    )
    assert (
        success_line is not None
    ), f"Expected success message not found in stdout: {result_pass.stdout}"
