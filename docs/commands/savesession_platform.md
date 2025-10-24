# `savesession` Command Documentation

## Purpose

The `savesession` command is a critical platform tool designed to capture and snapshot the current state of your development session within the AFS FastAPI Agricultural Robotics Platform. Its primary goal is to ensure that all relevant session data, including the dual TODO system (strategic and task-level objectives), is preserved. This preservation is essential for maintaining development continuity, especially in a multi-agent or long-running development environment.

## Usage

To save the current session state, execute the `savesession` command from your project's root directory:

```bash
./bin/savesession
```

## Key Features

*   **Session State Snapshot**: Captures the current state of the dual TODO system, including active tasks, pending subtasks, and completed objectives.
*   **Development Continuity**: Ensures that your progress and context are not lost across different development sessions or agent interactions.
*   **Compaction Protocol**: The command is designed to work in conjunction with a session state compaction protocol. If a session state file for the current day already exists, it will issue a warning, indicating that the existing state should be reviewed or compacted into `SESSION_SUMMARY.md` before proceeding with further changes.

## Agricultural Context

In the context of the AFS FastAPI Agricultural Robotics Platform, `savesession` plays a vital role in:

*   **Traceability**: Maintaining a clear record of development progress, which is crucial for compliance with agricultural safety standards like ISO 18497 and ISO 11783.
*   **Multi-Agent Coordination**: Facilitating seamless handoffs and collaboration between different AI agents or human developers by ensuring a consistent and up-to-date understanding of the project's state.
*   **Incident Investigation**: Providing snapshots of the development state at various points, which can be invaluable for investigating the root cause of issues or unexpected behavior in safety-critical agricultural robotics systems.

## Warnings and Considerations

*   **Existing Session State**: If a `SESSION_STATE_YYYY_MM_DD.md` file already exists for the current day, `savesession` will issue a warning. This is to prevent accidental overwrites and encourage the compaction of daily session states into `SESSION_SUMMARY.md` for better long-term record-keeping.
*   **Compaction**: For long-term preservation and to avoid cluttering the `docs/monitoring` directory, it is recommended to periodically compact daily session state files into `SESSION_SUMMARY.md`.
