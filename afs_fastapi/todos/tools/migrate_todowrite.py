#!/usr/bin/env python3
"""
TodoWrite Migration Tool
Converts existing 5-layer JSON system to new 12-layer YAML system
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class TodoWriteMigrator:
    """Migrates TodoWrite data from 5-layer JSON to 12-layer YAML system."""

    def __init__(self) -> None:
        self.source_data: dict[str, Any] = {}
        self.migrated_nodes: dict[str, dict[str, Any]] = {}
        self.migration_log: list[str] = []
        self.id_mapping: dict[str, str] = {}  # old_id -> new_id

    def load_legacy_data(self, json_path: Path) -> bool:
        """Load legacy todos.json file."""
        try:
            if not json_path.exists():
                self.migration_log.append(f"⚠️  Legacy file not found: {json_path}")
                return False

            with open(json_path) as f:
                self.source_data = json.load(f)

            self.migration_log.append(f"✅ Loaded legacy data from {json_path}")
            return True

        except Exception as e:
            self.migration_log.append(f"❌ Error loading {json_path}: {e}")
            return False

    def generate_new_id(self, old_id: str, layer: str) -> str:
        """Generate new ID format based on layer."""
        # Extract meaningful part from old ID
        id_part = old_id.replace("_", "-").upper()

        # Remove timestamp suffix if present
        id_part = re.sub(r"-\d{8}-\d{6}$", "", id_part)

        layer_prefixes = {
            "Goal": "GOAL",
            "Concept": "CON",
            "Context": "CTX",
            "Constraints": "CST",
            "Requirements": "R",
            "AcceptanceCriteria": "AC",
            "InterfaceContract": "IF",
            "Phase": "PH",
            "Step": "STP",
            "Task": "TSK",
            "SubTask": "SUB",
            "Command": "CMD",
        }

        prefix = layer_prefixes.get(layer, "UNKNOWN")

        # Create new ID
        if id_part.startswith(prefix + "-"):
            new_id = id_part
        else:
            new_id = f"{prefix}-{id_part}"

        # Ensure uniqueness
        counter = 1
        base_id = new_id
        while new_id in self.id_mapping.values():
            new_id = f"{base_id}-{counter:03d}"
            counter += 1

        self.id_mapping[old_id] = new_id
        return new_id

    def migrate_goal(self, goal_data: dict[str, Any]) -> dict[str, Any]:
        """Migrate a Goal item."""
        old_id = goal_data.get("id", "")
        new_id = self.generate_new_id(old_id, "Goal")

        migrated: dict[str, Any] = {
            "id": new_id,
            "layer": "Goal",
            "title": goal_data.get("title", ""),
            "description": goal_data.get("description", ""),
            "metadata": {
                "owner": "product-team",
                "labels": ["work:architecture", "agricultural"],
                "severity": goal_data.get("priority", "med").lower(),
                "work_type": "architecture",
                "migrated_from": old_id,
                "migration_date": datetime.now().isoformat(),
            },
            "links": {"parents": [], "children": []},
        }

        return migrated

    def migrate_phase(self, phase_data: dict[str, Any], goal_id: str) -> dict[str, Any]:
        """Migrate a Phase item."""
        old_id = phase_data.get("id", "")
        new_id = self.generate_new_id(old_id, "Phase")

        migrated: dict[str, Any] = {
            "id": new_id,
            "layer": "Phase",
            "title": phase_data.get("title", ""),
            "description": phase_data.get("description", ""),
            "metadata": {
                "owner": "development-team",
                "labels": ["work:implementation", "phase"],
                "severity": "med",
                "work_type": "implementation",
                "migrated_from": old_id,
                "migration_date": datetime.now().isoformat(),
            },
            "links": {"parents": [goal_id], "children": []},
        }

        return migrated

    def migrate_step(self, step_data: dict[str, Any], phase_id: str) -> dict[str, Any]:
        """Migrate a Step item."""
        old_id = step_data.get("id", "")
        new_id = self.generate_new_id(old_id, "Step")

        migrated: dict[str, Any] = {
            "id": new_id,
            "layer": "Step",
            "title": step_data.get("title", ""),
            "description": step_data.get("description", ""),
            "metadata": {
                "owner": "development-team",
                "labels": ["work:implementation", "step"],
                "severity": "med",
                "work_type": "implementation",
                "migrated_from": old_id,
                "migration_date": datetime.now().isoformat(),
            },
            "links": {"parents": [phase_id], "children": []},
        }

        return migrated

    def migrate_task(self, task_data: dict[str, Any], step_id: str) -> dict[str, Any]:
        """Migrate a Task item."""
        old_id = task_data.get("id", "")
        new_id = self.generate_new_id(old_id, "Task")

        migrated: dict[str, Any] = {
            "id": new_id,
            "layer": "Task",
            "title": task_data.get("title", ""),
            "description": task_data.get("description", ""),
            "metadata": {
                "owner": "developer",
                "labels": ["work:implementation", "task"],
                "severity": "low",
                "work_type": "implementation",
                "migrated_from": old_id,
                "migration_date": datetime.now().isoformat(),
            },
            "links": {"parents": [step_id], "children": []},
        }

        return migrated

    def migrate_subtask_and_command(
        self, subtask_data: dict[str, Any], task_id: str
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Migrate SubTask and create corresponding Command."""
        old_id = subtask_data.get("id", "")
        subtask_new_id = self.generate_new_id(old_id, "SubTask")

        # Create SubTask (declarative)
        subtask: dict[str, Any] = {
            "id": subtask_new_id,
            "layer": "SubTask",
            "title": subtask_data.get("title", ""),
            "description": subtask_data.get("description", ""),
            "metadata": {
                "owner": "developer",
                "labels": ["work:implementation", "subtask"],
                "severity": "low",
                "work_type": "implementation",
                "migrated_from": old_id,
                "migration_date": datetime.now().isoformat(),
            },
            "links": {"parents": [task_id], "children": []},
        }

        # Create Command if SubTask had executable content
        command_to_return: dict[str, Any] | None = None
        if subtask_data.get("command"):
            command_id = self.generate_new_id(f"{old_id}-CMD", "Command")

            # Create a synthetic Acceptance Criteria reference
            ac_id = self.generate_new_id(f"{old_id}-AC", "AcceptanceCriteria")

            command_to_return = {
                "id": command_id,
                "layer": "Command",
                "title": f"Execute {subtask_data.get('title', '')}",
                "description": f"Execute command for: {subtask_data.get('description', '')}",
                "metadata": {
                    "owner": "developer",
                    "labels": ["work:implementation", "command", "migrated"],
                    "work_type": "implementation",
                    "migrated_from": old_id,
                    "migration_date": datetime.now().isoformat(),
                },
                "links": {"parents": [ac_id], "children": []},  # Commands must reference AC
                "command": {
                    "ac_ref": ac_id,
                    "run": {
                        "shell": subtask_data.get("command", "echo 'No command specified'"),
                        "workdir": ".",
                        "env": {"PATH": "/usr/bin:/bin"},
                    },
                    "artifacts": [f"results/{command_id}/execution_log.txt"],
                },
            }

            # Update SubTask to reference Command
        return subtask, command_to_return

    def create_synthetic_acceptance_criteria(
        self, subtask_data: dict[str, Any], subtask_id: str
    ) -> dict[str, Any]:
        """Create synthetic Acceptance Criteria for migrated SubTasks."""
        old_id = subtask_data.get("id", "")
        ac_id = self.generate_new_id(f"{old_id}-AC", "AcceptanceCriteria")

        ac: dict[str, Any] = {
            "id": ac_id,
            "layer": "AcceptanceCriteria",
            "title": f"Verify completion of {subtask_data.get('title', '')}",
            "description": f"Given the implementation, when executed, then {subtask_data.get('description', '')} is completed successfully.",
            "metadata": {
                "owner": "test-team",
                "labels": ["work:validation", "migrated", "synthetic"],
                "work_type": "validation",
                "migrated_from": old_id,
                "migration_date": datetime.now().isoformat(),
                "synthetic": True,
            },
            "links": {"parents": [subtask_id], "children": []},
        }

        return ac

    def migrate_hierarchy(self) -> None:
        """Migrate the complete hierarchy."""
        if not self.source_data.get("goals"):
            self.migration_log.append("⚠️  No goals found in source data")
            return

        for goal_data in self.source_data["goals"]:
            # Migrate Goal
            goal = self.migrate_goal(goal_data)
            self.migrated_nodes[goal["id"]] = goal

            # Migrate Phases
            for phase_data in goal_data.get("phases", []):
                phase = self.migrate_phase(phase_data, goal["id"])
                self.migrated_nodes[phase["id"]] = phase
                goal["links"]["children"].append(phase["id"])

                # Migrate Steps
                for step_data in phase_data.get("steps", []):
                    step = self.migrate_step(step_data, phase["id"])
                    self.migrated_nodes[step["id"]] = step
                    phase["links"]["children"].append(step["id"])

                    # Migrate Tasks
                    for task_data in step_data.get("tasks", []):
                        task = self.migrate_task(task_data, step["id"])
                        self.migrated_nodes[task["id"]] = task
                        step["links"]["children"].append(task["id"])

                        # Migrate SubTasks and Commands
                        for subtask_data in task_data.get("subtasks", []):
                            subtask, command_data_dict = self.migrate_subtask_and_command(
                                subtask_data, task["id"]
                            )
                            self.migrated_nodes[subtask["id"]] = subtask
                            task["links"]["children"].append(subtask["id"])

                            if command_data_dict:
                                # Create synthetic AC first
                                ac = self.create_synthetic_acceptance_criteria(
                                    subtask_data, subtask["id"]
                                )
                                self.migrated_nodes[ac["id"]] = ac

                                # Then add command
                                self.migrated_nodes[command_data_dict["id"]] = command_data_dict

        self.migration_log.append(f"✅ Migrated {len(self.migrated_nodes)} nodes")

    def write_yaml_files(self, output_dir: Path) -> None:
        """Write migrated nodes to YAML files in appropriate directories."""
        # Create directory structure
        layer_dirs = {
            "Goal": output_dir / "plans" / "goals",
            "Concept": output_dir / "plans" / "concepts",
            "Context": output_dir / "plans" / "contexts",
            "Constraints": output_dir / "plans" / "constraints",
            "Requirements": output_dir / "plans" / "requirements",
            "AcceptanceCriteria": output_dir / "plans" / "acceptance_criteria",
            "InterfaceContract": output_dir / "plans" / "interface_contracts",
            "Phase": output_dir / "plans" / "phases",
            "Step": output_dir / "plans" / "steps",
            "Task": output_dir / "plans" / "tasks",
            "SubTask": output_dir / "plans" / "subtasks",
            "Command": output_dir / "commands",
        }

        # Create directories
        for dir_path in layer_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        # Write files
        files_written = 0
        for node_id, node_data in self.migrated_nodes.items():
            layer = node_data["layer"]
            target_dir = layer_dirs[layer]
            file_path = target_dir / f"{node_id}.yaml"

            with open(file_path, "w") as f:
                yaml.dump(node_data, f, default_flow_style=False, sort_keys=False)

            files_written += 1

        self.migration_log.append(f"✅ Wrote {files_written} YAML files")

    def create_migration_report(self, output_dir: Path) -> None:
        """Create a detailed migration report."""
        layer_statistics: dict[str, int] = {}
        report: dict[str, Any] = {
            "migration_summary": {
                "timestamp": datetime.now().isoformat(),
                "source_system": "TodoWrite 5-layer JSON",
                "target_system": "TodoWrite 12-layer YAML",
                "nodes_migrated": len(self.migrated_nodes),
                "id_mappings": len(self.id_mapping),
            },
            "layer_statistics": layer_statistics,
            "id_mappings": self.id_mapping,
            "migration_log": self.migration_log,
        }

        # Calculate layer statistics
        for node_data in self.migrated_nodes.values():
            layer = node_data["layer"]
            layer_statistics[layer] = layer_statistics.get(layer, 0) + 1

        # Write report
        report_path = output_dir / "migration_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.migration_log.append(f"✅ Migration report written to {report_path}")

    def run_migration(self, source_file: Path, output_dir: Path) -> bool:
        """Run the complete migration process."""
        self.migration_log.append("🚀 Starting TodoWrite migration...")

        # Load legacy data
        if not self.load_legacy_data(source_file):
            return False

        # Migrate hierarchy
        self.migrate_hierarchy()

        # Write YAML files
        self.write_yaml_files(output_dir)

        # Create migration report
        self.create_migration_report(output_dir)

        self.migration_log.append("✅ Migration completed successfully!")
        return True


def main() -> None:
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate TodoWrite from 5-layer JSON to 12-layer YAML system"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(".claude/todos.json"),
        help="Source todos.json file (default: .claude/todos.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("."),
        help="Output directory for migrated files (default: current directory)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be migrated without writing files"
    )

    args = parser.parse_args()

    # Run migration
    migrator = TodoWriteMigrator()

    if args.dry_run:
        print("🔍 Dry run mode - no files will be written")
        if migrator.load_legacy_data(args.source):
            migrator.migrate_hierarchy()
            print(f"Would migrate {len(migrator.migrated_nodes)} nodes:")
            for layer in [
                "Goal",
                "Phase",
                "Step",
                "Task",
                "SubTask",
                "Command",
                "AcceptanceCriteria",
            ]:
                count = sum(
                    1 for node in migrator.migrated_nodes.values() if node["layer"] == layer
                )
                if count > 0:
                    print(f"  {layer}: {count}")
    else:
        success = migrator.run_migration(args.source, args.output)

        # Print log
        for log_entry in migrator.migration_log:
            print(log_entry)

        if success:
            print("\n🎉 Migration completed! Next steps:")
            print("  1. Run: make tw-deps  (install dependencies)")
            print("  2. Run: make tw-all   (validate migrated files)")
            print("  3. Run: make tw-test  (test complete system)")
            sys.exit(0)
        else:
            print("\n❌ Migration failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
