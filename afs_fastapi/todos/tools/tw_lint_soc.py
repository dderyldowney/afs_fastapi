#!/usr/bin/env python3
"""
TodoWrite Separation of Concerns (SoC) Linter
Enforces that layers 1-11 are non-executable (declarative only)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


class SoCViolation:
    """Represents a Separation of Concerns violation."""

    def __init__(
        self, file_path: Path, violation_type: str, message: str, line_number: int | None = None
    ) -> None:
        self.file_path = file_path
        self.violation_type = violation_type
        self.message = message
        self.line_number = line_number

    def __str__(self) -> str:
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
        return f"{location} - {self.violation_type}: {self.message}"


class SoCLinter:
    """Lints TodoWrite YAML files for Separation of Concerns violations."""

    # Layers that must NOT contain executable content
    NON_EXECUTABLE_LAYERS = {
        "Goal",
        "Concept",
        "Context",
        "Constraints",
        "Requirements",
        "AcceptanceCriteria",
        "InterfaceContract",
        "Phase",
        "Step",
        "Task",
        "SubTask",
    }

    # Keywords that suggest executable content
    EXECUTABLE_KEYWORDS = {
        "command",
        "cmd",
        "shell",
        "bash",
        "run",
        "execute",
        "exec",
        "script",
        "call",
        "invoke",
        "launch",
        "start",
        "stop",
        "git",
        "npm",
        "pip",
        "make",
        "docker",
        "kubectl",
        "curl",
        "python",
        "node",
        "java",
        "mvn",
        "gradle",
    }

    # Shell command patterns
    SHELL_PATTERNS = [
        r"\$\(",  # $(command)
        r"`[^`]+`",  # `command`
        r"&&",  # command chaining
        r"\|\|",  # or chaining
        r"[;&|]",  # shell operators
        r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s+",  # command at start of line
    ]

    def __init__(self) -> None:
        self.violations: list[SoCViolation] = []

    def lint_file(self, file_path: Path) -> list[SoCViolation]:
        """Lint a single YAML file for SoC violations."""
        try:
            with open(file_path) as f:
                content = f.read()
                yaml_data = yaml.safe_load(content)

            if not yaml_data:
                return []

            file_violations = []

            # Check if this is a non-executable layer
            layer = yaml_data.get("layer", "")
            if layer in self.NON_EXECUTABLE_LAYERS:
                file_violations.extend(
                    self._check_non_executable_content(file_path, yaml_data, content)
                )

            # Check for single concern violations
            file_violations.extend(self._check_single_concern(file_path, yaml_data))

            return file_violations

        except Exception as e:
            return [SoCViolation(file_path, "PARSE_ERROR", f"Failed to parse file: {e}")]

    def _check_non_executable_content(
        self, file_path: Path, yaml_data: dict[str, Any], content: str
    ) -> list[SoCViolation]:
        """Check for executable content in non-executable layers."""
        violations = []

        # Check for command field presence
        if "command" in yaml_data:
            violations.append(
                SoCViolation(
                    file_path,
                    "EXECUTABLE_CONTENT",
                    f"Layer '{yaml_data.get('layer')}' contains 'command' field but must be declarative only",
                )
            )

        # Check for executable keywords in strings
        text_fields = ["title", "description"]
        for field in text_fields:
            if field in yaml_data:
                text = str(yaml_data[field]).lower()
                for keyword in self.EXECUTABLE_KEYWORDS:
                    if keyword in text:
                        violations.append(
                            SoCViolation(
                                file_path,
                                "EXECUTABLE_KEYWORD",
                                f"'{field}' contains executable keyword '{keyword}' - declarative layers should describe what, not how",
                            )
                        )

        # Check for shell command patterns
        for line_num, line in enumerate(content.split("\n"), 1):
            for pattern in self.SHELL_PATTERNS:
                if re.search(pattern, line):
                    violations.append(
                        SoCViolation(
                            file_path,
                            "SHELL_PATTERN",
                            f"Line contains shell command pattern '{pattern}' - not allowed in declarative layers",
                            line_num,
                        )
                    )

        return violations

    def _check_single_concern(
        self, file_path: Path, yaml_data: dict[str, Any]
    ) -> list[SoCViolation]:
        """Check for single concern violations."""
        violations = []

        # Check title and description for multiple concerns
        title = yaml_data.get("title", "")
        description = yaml_data.get("description", "")

        # Look for conjunction words that suggest multiple concerns
        concern_indicators = ["and", "or", "&", "+", "also", "additionally", "furthermore"]

        for field, text in [("title", title), ("description", description)]:
            if text:
                text_lower = text.lower()
                for indicator in concern_indicators:
                    if f" {indicator} " in text_lower:
                        violations.append(
                            SoCViolation(
                                file_path,
                                "MULTIPLE_CONCERNS",
                                f"'{field}' may contain multiple concerns ('{indicator}' detected) - consider splitting into separate items",
                            )
                        )

                # Check for multiple action verbs
                action_verbs = [
                    "implement",
                    "create",
                    "build",
                    "test",
                    "validate",
                    "verify",
                    "configure",
                    "setup",
                    "install",
                    "deploy",
                    "monitor",
                    "analyze",
                ]
                found_verbs = [verb for verb in action_verbs if verb in text_lower]
                if len(found_verbs) > 1:
                    violations.append(
                        SoCViolation(
                            file_path,
                            "MULTIPLE_ACTIONS",
                            f"'{field}' contains multiple action verbs {found_verbs} - each item should have one primary action",
                        )
                    )

        return violations

    def lint_directory(self, plans_dir: Path) -> list[SoCViolation]:
        """Lint all YAML files in a directory."""
        all_violations = []

        if not plans_dir.exists():
            return [
                SoCViolation(
                    plans_dir, "DIRECTORY_NOT_FOUND", f"Plans directory does not exist: {plans_dir}"
                )
            ]

        # Find all YAML files
        yaml_files: list[Path] = []
        for pattern in ["*.yaml", "*.yml"]:
            yaml_files.extend(plans_dir.rglob(pattern))

        for yaml_file in yaml_files:
            file_violations = self.lint_file(yaml_file)
            all_violations.extend(file_violations)

        return all_violations

    def generate_report(self, violations: list[SoCViolation]) -> dict[str, Any]:
        """Generate a linting report."""
        violation_counts: dict[str, int] = {}
        for violation in violations:
            violation_counts[violation.violation_type] = (
                violation_counts.get(violation.violation_type, 0) + 1
            )

        return {
            "total_violations": len(violations),
            "violation_types": violation_counts,
            "violations": [
                {
                    "file": str(v.file_path),
                    "type": v.violation_type,
                    "message": v.message,
                    "line": v.line_number,
                }
                for v in violations
            ],
        }


def main() -> None:
    """Main linting function."""
    parser = argparse.ArgumentParser(
        description="Lint TodoWrite YAML files for Separation of Concerns violations"
    )
    parser.add_argument(
        "--plans",
        type=Path,
        default=Path("plans"),
        help="Plans directory containing YAML files (default: plans)",
    )
    parser.add_argument("--report", type=Path, help="Output JSON report to file")
    parser.add_argument(
        "--strict", action="store_true", help="Exit with error code on any violations"
    )

    args = parser.parse_args()

    linter = SoCLinter()
    violations = linter.lint_directory(args.plans)

    # Generate report
    report = linter.generate_report(violations)

    # Print violations
    if violations:
        print(f"🔍 Found {len(violations)} SoC violations:")
        print()
        for violation in violations:
            print(f"❌ {violation}")
        print()

        # Print summary
        print("📊 Violation Summary:")
        for violation_type, count in report["violation_types"].items():
            print(f"   {violation_type}: {count}")
    else:
        print("✅ No SoC violations found!")

    # Write report if requested
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report written to {args.report}")

    # Exit with appropriate code
    if violations and args.strict:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
