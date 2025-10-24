# AFS FastAPI TODO System

This document provides a comprehensive guide to the new hierarchical TODOs system used in the AFS FastAPI project. The system is designed to be accessible and manageable by both humans and AI agents, ensuring a clear and structured development workflow.

## 12-Layer Hierarchy

The TODOs system is organized into a 12-layer hierarchy as defined in `ToDoWrite.md`:

1.  **Goal**
2.  **Concept**
3.  **Context**
4.  **Constraints**
5.  **Requirements**
6.  **Acceptance Criteria**
7.  **Interface Contract**
8.  **Phase**
9.  **Step**
10. **Task**
11. **SubTask**
12. **Command**

This structure ensures that all development work is aligned with the strategic goals of the project.

## Data Storage

All TODOs are stored in a single JSON file located at `.claude/todos.json`. This file is the single source of truth for the entire TODOs system.

## Command-Line Interface

A set of command-line scripts are provided in the `bin` directory to manage the TODOs at all three levels.

### Strategic Goal Commands

-   `strategic-list`: Lists all strategic goals.
-   `strategic-status`: Shows a detailed status of all strategic goals.
-   `strategic-status-brief`: Shows a brief summary of the strategic goals.
-   `strategic-add "<description>" [--category <category>] [--priority <priority>]`: Adds a new strategic goal.
-   `strategic-complete <goal_id>`: Marks a strategic goal as completed.
-   `strategic-delete <goal_id>`: Deletes a strategic goal.
-   `strategic-reorder <goal_id> <new_position>`: Reorders a strategic goal.
-   `strategic-pause <goal_id>`: Pauses a pending strategic goal.
-   `strategic-resume <goal_id>`: Resumes a paused strategic goal.



### Task Commands

-   `task-add "<description>"`: Adds a new task to the active phase.
-   `task-complete <task_id>`: Marks a task as completed.
-   `task-delete <task_id>`: Deletes a task.
-   `task-reorder <task_id> <new_position>`: Reorders a task within its phase.
-   `task-pause <task_id>`: Pauses a pending task.
-   `task-resume <task_id>`: Resumes a paused task.

## Session Management

-   `loadsession`: Displays a summary of the current session, including the TODOs status, from `SESSION_SUMMARY.md`.
-   `savesession`: Creates a `SESSION_SUMMARY.md` file with a summary of the current TODOs state.

This new system provides a robust and flexible way to manage the development workflow of the AFS FastAPI project.
