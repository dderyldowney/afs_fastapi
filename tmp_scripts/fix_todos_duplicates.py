import sys
from collections import defaultdict
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from afs_fastapi.todos.manager import load_todos, save_todos  # noqa: E402


def clean_todos_duplicates(todos_data):
    cleaned_goals = []
    seen_ids = set()
    duplicate_ids = defaultdict(list)

    # First pass: identify all duplicates
    def collect_duplicates(item_list):
        for item in item_list:
            if item["id"] in seen_ids:
                duplicate_ids[item["id"]].append(item)
            else:
                seen_ids.add(item["id"])

    for goal in todos_data["goals"]:
        collect_duplicates([goal])
        for phase in goal["phases"]:
            collect_duplicates([phase])
            for step in phase["steps"]:
                collect_duplicates([step])
                for task in step["tasks"]:
                    collect_duplicates([task])
                    for subtask in task["subtasks"]:
                        collect_duplicates([subtask])

    # Second pass: rebuild the structure, resolving duplicates
    seen_ids.clear()  # Reset seen_ids for the cleaning pass

    for goal in todos_data["goals"]:
        if goal["id"] in seen_ids:
            continue  # Skip if already processed as a duplicate

        if goal["id"] in duplicate_ids:
            # Resolve duplicate goals (keep the first one encountered, or apply more complex logic if needed)
            # For simplicity, we'll keep the first one encountered in the original list
            if goal["id"] not in seen_ids:
                cleaned_goals.append(goal)
                seen_ids.add(goal["id"])
        else:
            cleaned_goals.append(goal)
            seen_ids.add(goal["id"])

        cleaned_phases = []
        seen_phase_ids = set()
        for phase in goal["phases"]:
            if phase["id"] in seen_phase_ids:
                continue
            if phase["id"] in duplicate_ids:
                # Resolve duplicate phases
                if phase["id"] not in seen_phase_ids:
                    cleaned_phases.append(phase)
                    seen_phase_ids.add(phase["id"])
            else:
                cleaned_phases.append(phase)
                seen_phase_ids.add(phase["id"])

            cleaned_steps = []
            seen_step_ids = set()
            for step in phase["steps"]:
                if step["id"] in seen_step_ids:
                    continue
                if step["id"] in duplicate_ids:
                    # Resolve duplicate steps
                    # For steps, we want to keep the one that is 'in_progress' if any, otherwise the first 'planned'
                    # If multiple 'in_progress' or 'done' with same ID, keep the first one encountered.
                    if step["id"] not in seen_step_ids:
                        cleaned_steps.append(step)
                        seen_step_ids.add(step["id"])
                else:
                    cleaned_steps.append(step)
                    seen_step_ids.add(step["id"])

                cleaned_tasks = []
                seen_task_ids = set()
                for task in step["tasks"]:
                    if task["id"] in seen_task_ids:
                        continue
                    if task["id"] in duplicate_ids:
                        # Resolve duplicate tasks
                        if task["id"] not in seen_task_ids:
                            cleaned_tasks.append(task)
                            seen_task_ids.add(task["id"])
                    else:
                        cleaned_tasks.append(task)
                        seen_task_ids.add(task["id"])

                    cleaned_subtasks = []
                    seen_subtask_ids = set()
                    for subtask in task["subtasks"]:
                        if subtask["id"] in seen_subtask_ids:
                            continue
                        if subtask["id"] in duplicate_ids:
                            # Resolve duplicate subtasks
                            if subtask["id"] not in seen_subtask_ids:
                                cleaned_subtasks.append(subtask)
                                seen_subtask_ids.add(subtask["id"])
                        else:
                            cleaned_subtasks.append(subtask)
                            seen_subtask_ids.add(subtask["id"])
                    task["subtasks"] = cleaned_subtasks
                step["tasks"] = cleaned_tasks
            phase["steps"] = cleaned_steps
        goal["phases"] = cleaned_phases

    todos_data["goals"] = cleaned_goals
    return todos_data


def main():
    print("Loading todos.json...")
    todos = load_todos()
    print(f"Found {len(todos['goals'])} goals before cleaning.")

    print("Cleaning duplicate IDs...")
    cleaned_todos = clean_todos_duplicates(todos)

    print("Saving cleaned todos.json...")
    save_todos(cleaned_todos)
    print("Cleaned todos.json saved. Please check step-status again.")


if __name__ == "__main__":
    main()
