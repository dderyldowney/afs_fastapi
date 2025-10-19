# `saveandpush` Command Documentation

## Purpose

The `saveandpush` command is a comprehensive platform tool designed to automate the process of saving the current development session state, committing any changes to the Git repository, and pushing those changes to the remote `origin/develop` branch. It streamlines the workflow for AI agents and human developers, ensuring that progress is consistently recorded and synchronized.

## Usage

To save and push your current session state and changes, execute the `saveandpush` command from your project's root directory:

```bash
./bin/saveandpush
```

## Key Features

*   **TODO State Synchronization**: Automatically synchronizes the dual TODO system (strategic and task-level objectives), ensuring the latest progress is captured.
*   **Session State Saving**: Attempts to save the current session state. It will issue a warning if a session state file for the current day already exists, prompting for compaction if necessary.
*   **Git Status Check**: Identifies all modified and untracked files that need to be committed.
*   **CHANGELOG.md Update**: Automatically updates `CHANGELOG.md` based on recent commit history, ensuring documentation of changes.
*   **File Staging**: Stages all modified files, including the updated `CHANGELOG.md` and internal session state files.
*   **Automated Commit**: Generates a descriptive commit message (e.g., `docs(session): Update documentation and session state`) and creates a new Git commit.
*   **Remote Push**: Pushes the newly created commit to the `origin/develop` branch, synchronizing local changes with the remote repository.

## Agricultural Context

In the context of the AFS FastAPI Agricultural Robotics Platform, `saveandpush` is crucial for:

*   **Continuous Integration/Continuous Delivery (CI/CD)**: Facilitating a smooth CI/CD pipeline by ensuring frequent and consistent updates to the codebase.
*   **Collaboration**: Enabling seamless collaboration among multiple AI agents and human engineers by keeping the remote repository up-to-date with the latest development state.
*   **Compliance and Auditing**: Providing a robust mechanism for tracking all changes, which is vital for compliance with agricultural safety standards (ISO 18497, ISO 11783) and for auditing development progress.
*   **Disaster Recovery**: Regularly pushing changes to a remote repository acts as a safeguard against local data loss.

## Warnings and Considerations

*   **Session State Compaction**: Similar to `savesession`, if a `SESSION_STATE_YYYY_MM_DD.md` file already exists for the current day, `saveandpush` will issue a warning. It is recommended to periodically compact daily session state files into `SESSION_SUMMARY.md`.
*   **Pre-commit Hooks**: `saveandpush` triggers pre-commit hooks during the commit process. Ensure your pre-commit configuration is correctly set up to maintain code quality and standards.
