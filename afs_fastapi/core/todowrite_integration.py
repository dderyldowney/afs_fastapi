"""TodoWrite Integration Module for Claude Code.

Provides seamless integration between Claude Code TodoWrite tool and the
4-level AFS FastAPI hierarchy: Strategic Goal -> Phase -> Step -> Task.

This module enables saving TodoWrite tasks at any level with minimal steps,
fulfilling the user requirement for "as few steps as possible" saving.
"""

from __future__ import annotations

from typing import Any, TypedDict

from afs_fastapi.todos.manager import add_step, add_task, create_node, get_active_items, load_todos


class Context(TypedDict):
    active_goal: str | None
    active_phase: str | None
    active_step: str | None
    active_task: str | None
    suggested_agricultural_contexts: list[str]
    available_levels: list[str]


def add_subtask(
    task_id: str, title: str, description: str, command: str, command_type: str
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Add a new SubTask to the specified Task.
    """
    try:
        import uuid

        subtask_id = f"subtask-{uuid.uuid4().hex[:12]}"
        subtask_data = {
            "id": subtask_id,
            "layer": "SubTask",
            "title": title,
            "description": description,
            "status": "planned",
            "links": {"parents": [task_id], "children": []},
            "metadata": {
                "owner": "system",
                "labels": [],
                "severity": "",
                "work_type": "",
            },
            "command": {
                "ac_ref": "",
                "run": {"command": command, "type": command_type},
                "artifacts": [],
            },
        }

        node = create_node(subtask_data)
        if node:
            subtask_dict = {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status,
            }
            return subtask_dict, None
        else:
            return None, "Failed to create subtask"
    except Exception as e:
        return None, str(e)


class TodoWriteIntegration:
    """Seamless integration interface for TodoWrite tool."""

    @staticmethod
    def save_current_todowrite(
        todowrite_tasks: list[dict[str, Any]],
        agricultural_context: str | None = None,
        target_level: str = "auto",
    ) -> tuple[str, str | None]:
        """Save current TodoWrite tasks with automatic level detection."""
        if not todowrite_tasks:
            return "No tasks to save", None

        todos = load_todos()
        active_items = get_active_items(todos)
        active_phase = active_items.get("Phase")
        active_step = active_items.get("Step")
        active_task = active_items.get("Task")

        created_count = 0
        error_message = None

        if target_level == "auto":
            if active_task:
                for task_data in todowrite_tasks:
                    subtask, err = add_subtask(
                        task_id=active_task.id,
                        title=task_data.get("content", "New SubTask"),
                        description=task_data.get("content", "No description provided."),
                        command=task_data.get("command", "todo"),
                        command_type=task_data.get("command_type", "bash"),
                    )
                    if subtask:
                        created_count += 1
                    if err:
                        error_message = err
                        break
                if created_count > 0:
                    return (
                        f"Saved {created_count} subtasks to active task: {active_task.title}",
                        error_message,
                    )
            elif active_step:
                for task_data in todowrite_tasks:
                    task, err = add_task(
                        step_id=active_step.id,
                        title=task_data.get("content", "New Task"),
                        description=task_data.get("content", "No description provided."),
                    )
                    if task:
                        created_count += 1
                    if err:
                        error_message = err
                        break
                if created_count > 0:
                    return (
                        f"Saved {created_count} tasks to active step: {active_step.title}",
                        error_message,
                    )
            elif active_phase:
                for task_data in todowrite_tasks:
                    step, err = add_step(
                        phase_id=active_phase.id,
                        name=task_data.get("content", "New Step"),
                        description=task_data.get("content", "No description provided."),
                    )
                    if step:
                        created_count += 1
                    if err:
                        error_message = err
                        break
                if created_count > 0:
                    return (
                        f"Saved {created_count} steps to active phase: {active_phase.title}",
                        error_message,
                    )
            else:
                return "", "No active goal, phase, step, or task found for auto-saving."

        elif target_level == "task":
            if active_task:
                for task_data in todowrite_tasks:
                    subtask, err = add_subtask(
                        task_id=active_task.id,
                        title=task_data.get("content", "New SubTask"),
                        description=task_data.get("content", "No description provided."),
                        command=task_data.get("command", "todo"),
                        command_type=task_data.get("command_type", "bash"),
                    )
                    if subtask:
                        created_count += 1
                    if err:
                        error_message = err
                        break
                if created_count > 0:
                    return (
                        f"Saved {created_count} subtasks to active task: {active_task.title}",
                        error_message,
                    )
                return "", error_message or "Failed to save subtasks to active task."
            return "", "No active task found for saving."

        elif target_level == "step":
            if active_step:
                for task_data in todowrite_tasks:
                    task, err = add_task(
                        step_id=active_step.id,
                        title=task_data.get("content", "New Task"),
                        description=task_data.get("content", "No description provided."),
                    )
                    if task:
                        created_count += 1
                    if err:
                        error_message = err
                        break
                if created_count > 0:
                    return (
                        f"Saved {created_count} tasks to active step: {active_step.title}",
                        error_message,
                    )
                return "", error_message or "Failed to save tasks to active step."
            return "", "No active step found for saving."

        elif target_level == "phase":
            if active_phase:
                for task_data in todowrite_tasks:
                    step, err = add_step(
                        phase_id=active_phase.id,
                        name=task_data.get("content", "New Step"),
                        description=task_data.get("content", "No description provided."),
                    )
                    if step:
                        created_count += 1
                    if err:
                        error_message = err
                        break
                if created_count > 0:
                    return (
                        f"Saved {created_count} steps to active phase: {active_phase.title}",
                        error_message,
                    )
                return "", error_message or "Failed to save steps to active phase."
            return "", "No active phase found for saving."

        return "", f"Unknown target level: {target_level}. Use 'auto', 'task', 'step', or 'phase'."

    @staticmethod
    def quick_save(
        content_list: list[str], agricultural_context: str | None = None
    ) -> tuple[str, str | None]:
        """Quick save for simple task lists with minimal interface."""
        if not content_list:
            return "No tasks to save", None

        todowrite_tasks = [
            {
                "content": task_content.strip() if task_content else "",
                "status": "pending",
                "activeForm": f"Working on {task_content.strip() if task_content else ''}",
            }
            for task_content in content_list
            if task_content.strip()
        ]

        return TodoWriteIntegration.save_current_todowrite(todowrite_tasks, agricultural_context)

    @staticmethod
    def save_with_status(
        tasks_with_status: list[dict[str, str]], agricultural_context: str | None = None
    ) -> tuple[str, str | None]:
        """Save tasks that already have completion status."""
        if not tasks_with_status:
            return "No tasks to save", None

        todowrite_tasks = [
            {
                "content": task.get("content", "").strip() if task.get("content") else "",
                "status": task.get("status", "planned"),
                "activeForm": f"Working on {task.get('content', '').strip() if task.get('content') else ''}",
            }
            for task in tasks_with_status
            if task.get("content", "").strip()
        ]

        return TodoWriteIntegration.save_current_todowrite(todowrite_tasks, agricultural_context)

    def get_current_context(self) -> Context:
        """Get current agricultural context for TodoWrite saving."""
        todos = load_todos()
        active_items = get_active_items(todos)
        active_goal = active_items.get("Goal")
        active_phase = active_items.get("Phase")
        active_step = active_items.get("Step")
        active_task = active_items.get("Task")

        context: Context = {
            "active_goal": active_goal.title if active_goal else None,
            "active_phase": active_phase.title if active_phase else None,
            "active_step": active_step.title if active_step else None,
            "active_task": active_task.title if active_task else None,
            "suggested_agricultural_contexts": [
                "CAN Bus Integration",
                "Agricultural Robotics Testing",
                "Tractor Fleet Coordination",
                "Safety Critical Systems",
                "Network Traffic Management",
                "Equipment Telemetry Processing",
            ],
            "available_levels": [],
        }

        if active_task:
            context["available_levels"].append("task")
        if active_step:
            context["available_levels"].append("step")
        if active_phase:
            context["available_levels"].append("phase")
        context["available_levels"].append("auto")

        return context


# Convenience functions for Claude Code integration
def save_todowrite_tasks(
    tasks: list[dict[str, Any]], context: str | None = None
) -> tuple[str, str | None]:
    """Main integration function for Claude Code TodoWrite tool."""
    return TodoWriteIntegration.save_current_todowrite(tasks, context)


def quick_save_tasks(task_list: list[str], context: str | None = None) -> tuple[str, str | None]:
    """Quick save function for simple task lists."""
    return TodoWriteIntegration.quick_save(task_list, context)


def get_save_context() -> Context:
    """Get current context for TodoWrite saving decisions."""
    return TodoWriteIntegration().get_current_context()
