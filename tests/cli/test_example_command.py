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
    assert result.stdout == "", "Unexpected stdout for failing command."

    # Test the passing case
    result_pass = subprocess.run(
        command_path, capture_output=True, text=True, check=True, shell=True
    )
    assert result_pass.returncode == 0, "Command unexpectedly failed."
    assert (
        result_pass.stdout.strip() == "Command executed successfully."
    ), "Unexpected stdout for passing command."
    assert result_pass.stderr == "", "Unexpected stderr for passing command."
