#!/usr/bin/env python3
"""
MANDATORY CHANGELOG.md Enforcement Hook for AFS FastAPI

This hook ensures CHANGELOG.md is included in every git commit for the
agricultural robotics platform, maintaining complete version history essential
for ISO 18497/11783 compliance auditing.

ENFORCEMENT:
- All commits must include CHANGELOG.md in staged files
- Exception: Merge commits (already documented in individual commits)
- Rationale: Equipment operators, safety engineers, and compliance auditors
  depend on CHANGELOG.md as authoritative record of platform modifications

Agricultural Context:
- Safety-critical multi-tractor coordination systems require complete change tracking
- ISO 18497 (agricultural machinery safety) audits require documented modifications
- ISO 11783 (ISOBUS) compliance depends on version history documentation
- Emergency incident investigation relies on complete change history
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class ChangelogEnforcementHook:
    """
    Enforce mandatory CHANGELOG.md inclusion in all agricultural platform commits.

    Validates that CHANGELOG.md is present in staged files before allowing commit
    to proceed, ensuring continuous documentation of platform modifications essential
    for safety-critical agricultural robotics systems.
    """

    def __init__(self) -> None:
        """Initialize CHANGELOG.md enforcement hook."""
        self.changelog_filename = "CHANGELOG.md"
        self.project_root = Path.cwd()

    def check_changelog_file_exists(self, repo_path: Path | None = None) -> bool:
        """Check if CHANGELOG.md file exists in repository.

        Args:
            repo_path: Path to repository root (defaults to current directory)

        Returns:
            True if CHANGELOG.md exists, False otherwise
        """
        if repo_path is None:
            repo_path = self.project_root

        changelog_path = repo_path / self.changelog_filename
        return changelog_path.exists()

    def is_merge_commit(self) -> bool:
        """Detect if current commit is a merge commit.

        Merge commits don't require CHANGELOG.md staging as changes are already
        documented in individual commits being merged.

        Returns:
            True if merge commit detected, False otherwise
        """
        # Check for GIT_MERGE_HEAD environment variable (set during merge)
        return "GIT_MERGE_HEAD" in os.environ

    def has_skip_changelog_marker(self) -> bool:
        """Check if commit message contains [skip-changelog] marker.

        The [skip-changelog] marker allows commits that only update CHANGELOG.md
        to bypass enforcement, preventing infinite regeneration loops when
        updatechangelog creates commits with CHANGELOG but no other changes.

        Returns:
            True if [skip-changelog] marker detected, False otherwise
        """
        # Read commit message from COMMIT_EDITMSG if it exists
        git_dir = Path.cwd() / ".git"
        commit_msg_file = git_dir / "COMMIT_EDITMSG"

        if commit_msg_file.exists():
            commit_msg = commit_msg_file.read_text()
            return "[skip-changelog]" in commit_msg

        return False

    def validate_changelog_in_commit(self, staged_files: list[str]) -> bool:
        """Validate CHANGELOG.md is present in staged files.

        Args:
            staged_files: List of files staged for commit

        Returns:
            True if CHANGELOG in staged files, merge commit, or [skip-changelog], False otherwise

        Agricultural Context:
            Every platform modification must be documented in CHANGELOG.md for
            ISO 18497/11783 compliance auditing and safety-critical system tracking.
        """
        # Skip enforcement for merge commits
        if self.is_merge_commit():
            return True

        # Skip enforcement for commits with [skip-changelog] marker
        # This prevents infinite loops when updatechangelog generates commits
        if self.has_skip_changelog_marker():
            return True

        # Check if CHANGELOG.md is in staged files
        changelog_in_staged = any(
            self.changelog_filename in Path(file).name for file in staged_files
        )

        return changelog_in_staged

    def get_error_message(self) -> str:
        """Get helpful error message with agricultural context and remediation.

        Returns:
            Error message explaining violation and how to fix it
        """
        return f"""
❌ CHANGELOG.md Enforcement Violation:
{self.changelog_filename} is not included in staged files for this commit.

📋 MANDATORY REQUIREMENT:
ALL commits to the agricultural robotics platform MUST include {self.changelog_filename}
updates to maintain complete version history essential for ISO 18497/11783
compliance auditing.

🔧 How to Fix:
1. Update {self.changelog_filename} with your changes in the [Unreleased] section
2. Stage the updated file: git add {self.changelog_filename}
3. Complete your commit: git commit

⚙️  Alternative (CHANGELOG-only commits):
If this commit ONLY updates {self.changelog_filename} (e.g., regeneration), add
[skip-changelog] to your commit message to prevent infinite regeneration loops.

        The CHANGELOG.md serves as a critical record of all platform modifications.

📖 See SESSION_SUMMARY.md for complete CHANGELOG.md maintenance protocol."""

    def run_validation(self, hook_input: dict) -> bool:
        """Run CHANGELOG.md enforcement validation.

        Args:
            hook_input: Dictionary containing staged_files list

        Returns:
            True if validation passes, False if CHANGELOG.md missing
        """
        staged_files = hook_input.get("staged_files", [])

        # Validate CHANGELOG.md in commit
        is_valid = self.validate_changelog_in_commit(staged_files)

        if not is_valid:
            # Print error message to stderr
            print(self.get_error_message(), file=sys.stderr)

        return is_valid


def main() -> None:
    """
    Main hook execution for CHANGELOG.md enforcement.

    Reads staged files from command line arguments (provided by pre-commit framework),
    validates CHANGELOG.md presence, and exits with appropriate code.

    Exit Codes:
        0: Validation passed (CHANGELOG.md included or merge commit)
        1: Validation failed (CHANGELOG.md missing from staged files)
    """
    try:
        # Get staged files from command line arguments (pre-commit passes them)
        # If no args, get from git directly
        if len(sys.argv) > 1:
            staged_files = sys.argv[1:]
        else:
            # Fallback: get staged files from git
            import subprocess

            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            staged_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Initialize and run enforcement hook
        enforcement_hook = ChangelogEnforcementHook()
        hook_input = {"staged_files": staged_files}
        is_valid = enforcement_hook.run_validation(hook_input)

        # Exit with appropriate code
        sys.exit(0 if is_valid else 1)

    except Exception as e:
        print(
            f"CHANGELOG.md enforcement hook error: {e}",
            file=sys.stderr,
        )
        # Don't block commits on hook errors (fail open for robustness)
        sys.exit(0)


if __name__ == "__main__":
    main()
