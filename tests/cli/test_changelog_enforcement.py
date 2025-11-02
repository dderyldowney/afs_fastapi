"""
Test-First Development: CHANGELOG.md Enforcement Hook Tests

RED PHASE: These tests describe desired behavior for mandatory CHANGELOG.md
inclusion in all git commits for agricultural robotics platform.

Agricultural Context:
- Complete version history essential for ISO 18497/11783 compliance auditing
- Equipment operators, safety engineers, compliance auditors depend on CHANGELOG.md
- Every platform modification must be documented for safety-critical systems
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


class TestChangelogEnforcementHook:
    """Test mandatory CHANGELOG.md enforcement for agricultural platform commits."""

    @pytest.fixture
    def temp_git_repo(self, tmp_path: Path) -> Path:
        """Create temporary git repository for testing."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Create CHANGELOG.md
        changelog = repo_dir / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [Unreleased]\n")

        return repo_dir

    @pytest.fixture
    def hook_module(self):
        """Import the changelog enforcement hook module for testing."""
        import importlib.util

        hook_path = (
            Path(__file__).parent.parent.parent.parent
            / ".claude"
            / "hooks"
            / "changelog_enforcement.py"
        )

        spec = importlib.util.spec_from_file_location("changelog_enforcement", hook_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    def test_rejects_commit_without_changelog_in_staged_files(
        self, temp_git_repo: Path, hook_module
    ) -> None:
        """Test RED: Should reject commit when CHANGELOG.md not in staged files.

        Agricultural scenario: Developer commits equipment control changes
        without updating CHANGELOG.md, violating mandatory documentation
        requirements for safety-critical agricultural robotics systems.
        """
        # Create and stage a source file without CHANGELOG.md
        source_file = temp_git_repo / "equipment.py"
        source_file.write_text("class Tractor:\n    pass\n")

        subprocess.run(
            ["git", "add", "equipment.py"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Simulate hook receiving staged files (without CHANGELOG.md)
        hook_input = {"staged_files": ["equipment.py"]}

        # Hook should detect missing CHANGELOG.md and reject
        validator = hook_module.ChangelogEnforcementHook()
        result = validator.validate_changelog_in_commit(hook_input["staged_files"])

        assert result is False, "Hook should reject commit without CHANGELOG.md"

    def test_accepts_commit_with_changelog_in_staged_files(
        self, temp_git_repo: Path, hook_module
    ) -> None:
        """Test RED: Should accept commit when CHANGELOG.md is in staged files.

        Agricultural scenario: Developer commits equipment control changes
        and properly updates CHANGELOG.md, following mandatory documentation
        protocol for agricultural robotics platform version history.
        """
        # Create and stage source file plus CHANGELOG.md
        source_file = temp_git_repo / "equipment.py"
        source_file.write_text("class Tractor:\n    pass\n")

        changelog = temp_git_repo / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [Unreleased]\n- Added Tractor class\n")

        subprocess.run(
            ["git", "add", "equipment.py", "CHANGELOG.md"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Simulate hook receiving staged files (including CHANGELOG.md)
        hook_input = {"staged_files": ["equipment.py", "CHANGELOG.md"]}

        # Hook should accept commit with CHANGELOG.md
        validator = hook_module.ChangelogEnforcementHook()
        result = validator.validate_changelog_in_commit(hook_input["staged_files"])

        assert result is True, "Hook should accept commit with CHANGELOG.md"

    def test_provides_helpful_error_message_for_agricultural_context(
        self, temp_git_repo: Path, hook_module
    ) -> None:
        """Test RED: Should provide agricultural robotics context in error message.

        Agricultural scenario: Error message explains why CHANGELOG.md is
        mandatory for ISO 18497/11783 compliance and safety-critical systems.
        """
        # Stage file without CHANGELOG.md
        source_file = temp_git_repo / "safety.py"
        source_file.write_text("def emergency_stop(): pass\n")

        subprocess.run(
            ["git", "add", "safety.py"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Hook should provide agricultural context in error
        validator = hook_module.ChangelogEnforcementHook()
        error_message = validator.get_error_message()

        assert "CHANGELOG.md" in error_message
        assert "agricultural" in error_message.lower() or "ISO" in error_message
        assert "mandatory" in error_message.lower() or "required" in error_message.lower()

    def test_accepts_changelog_only_commits(self, temp_git_repo: Path, hook_module) -> None:
        """Test RED: Should accept commits that only modify CHANGELOG.md.

        Agricultural scenario: Documentation-only commits updating CHANGELOG.md
        for retroactive documentation or consolidation are valid and should pass.
        """
        # Stage only CHANGELOG.md
        changelog = temp_git_repo / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [Unreleased]\n- Documentation update\n")

        subprocess.run(
            ["git", "add", "CHANGELOG.md"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        hook_input = {"staged_files": ["CHANGELOG.md"]}

        # Hook should accept CHANGELOG.md-only commits
        validator = hook_module.ChangelogEnforcementHook()
        result = validator.validate_changelog_in_commit(hook_input["staged_files"])

        assert result is True, "Hook should accept CHANGELOG.md-only commits"

    def test_rejects_multiple_files_without_changelog(
        self, temp_git_repo: Path, hook_module
    ) -> None:
        """Test RED: Should reject commits with multiple files but no CHANGELOG.md.

        Agricultural scenario: Developer commits multiple equipment coordination
        changes across several files without updating CHANGELOG.md, violating
        version history documentation requirements.
        """
        # Create and stage multiple files without CHANGELOG.md
        files = ["equipment.py", "coordination.py", "monitoring.py"]
        for filename in files:
            file_path = temp_git_repo / filename
            file_path.write_text(f"# {filename}\npass\n")

        subprocess.run(
            ["git", "add"] + files,
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        hook_input = {"staged_files": files}

        # Hook should reject commit without CHANGELOG.md
        validator = hook_module.ChangelogEnforcementHook()
        result = validator.validate_changelog_in_commit(hook_input["staged_files"])

        assert result is False, "Hook should reject multi-file commit without CHANGELOG.md"

    def test_hook_integrates_with_git_workflow(self, temp_git_repo: Path, hook_module) -> None:
        """Test RED: Should integrate with git pre-commit workflow.

        Agricultural scenario: Hook runs automatically during git commit,
        validating CHANGELOG.md presence before commit completes, ensuring
        continuous compliance with documentation requirements.
        """
        # Create hook main function input (simulates git pre-commit)
        source_file = temp_git_repo / "api.py"
        source_file.write_text("def get_equipment(): pass\n")

        subprocess.run(
            ["git", "add", "api.py"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        staged_files = result.stdout.strip().split("\n")

        # Hook should return non-zero exit code (rejection)
        # Note: This tests the integration pattern, actual exit handled by main()
        validator = hook_module.ChangelogEnforcementHook()
        should_reject = not validator.validate_changelog_in_commit(staged_files)

        assert should_reject is True, "Hook should integrate with git to reject commit"

    def test_provides_remediation_instructions(self, temp_git_repo: Path, hook_module) -> None:
        """Test RED: Should provide clear instructions for fixing violation.

        Agricultural scenario: Error message guides developers on how to update
        CHANGELOG.md and restage files to complete commit successfully.
        """
        validator = hook_module.ChangelogEnforcementHook()
        error_message = validator.get_error_message()

        # Error message should include remediation steps
        assert "add" in error_message.lower() or "stage" in error_message.lower()
        assert "git" in error_message.lower()

    def test_validates_changelog_exists_in_repository(
        self, temp_git_repo: Path, hook_module
    ) -> None:
        """Test RED: Should validate CHANGELOG.md file exists in repository.

        Agricultural scenario: Ensures CHANGELOG.md file is present in repository
        structure before validating its inclusion in commits.
        """
        # Remove CHANGELOG.md from repository
        changelog = temp_git_repo / "CHANGELOG.md"
        if changelog.exists():
            changelog.unlink()

        validator = hook_module.ChangelogEnforcementHook()
        changelog_exists = validator.check_changelog_file_exists(temp_git_repo)

        assert changelog_exists is False, "Hook should detect missing CHANGELOG.md file"

    def test_skips_merge_commits(self, temp_git_repo: Path, hook_module) -> None:
        """Test RED: Should skip enforcement for merge commits.

        Agricultural scenario: Merge commits from branch integration don't
        require CHANGELOG.md staging as changes are already documented in
        individual commits. Prevents duplicate documentation requirements.
        """
        # Simulate merge commit detection
        validator = hook_module.ChangelogEnforcementHook()

        # Mock environment to indicate merge commit
        with patch.dict("os.environ", {"GIT_MERGE_HEAD": "abc123"}):
            is_merge = validator.is_merge_commit()
            assert is_merge is True, "Hook should detect merge commits"

            # Merge commits should skip CHANGELOG.md enforcement
            result = validator.validate_changelog_in_commit(["equipment.py"])
            assert result is True, "Hook should skip CHANGELOG.md enforcement for merge commits"

    def test_skips_changelog_with_skip_marker(self, temp_git_repo: Path, hook_module) -> None:
        """Test RED: Should skip enforcement when [skip-changelog] marker present.

        Agricultural scenario: CHANGELOG-only commits (e.g., from updatechangelog)
        use [skip-changelog] marker to prevent infinite regeneration loops where
        updatechangelog creates commits that trigger more changelog updates.
        """
        # Create a commit message file with [skip-changelog] marker
        git_dir = temp_git_repo / ".git"
        commit_msg_file = git_dir / "COMMIT_EDITMSG"
        commit_msg_file.write_text(
            "docs(changelog): Update CHANGELOG.md with recent commits\n\n[skip-changelog]"
        )

        # Create validator and validate it detects marker
        validator = hook_module.ChangelogEnforcementHook()

        # Mock the Path.cwd() to return our test repo
        with patch("pathlib.Path.cwd", return_value=temp_git_repo):
            has_marker = validator.has_skip_changelog_marker()
            assert has_marker is True, "Hook should detect [skip-changelog] marker"

            # Commits with marker should skip enforcement even without CHANGELOG.md
            result = validator.validate_changelog_in_commit(["equipment.py"])
            assert (
                result is True
            ), "Hook should skip CHANGELOG.md enforcement for [skip-changelog] commits"

    def test_enforces_changelog_without_skip_marker(self, temp_git_repo: Path, hook_module) -> None:
        """Test RED: Should enforce CHANGELOG.md when [skip-changelog] marker absent.

        Agricultural scenario: Regular commits without [skip-changelog] marker
        must include CHANGELOG.md to maintain complete version history for
        safety-critical agricultural robotics platform.
        """
        # Create commit message file WITHOUT [skip-changelog] marker
        git_dir = temp_git_repo / ".git"
        commit_msg_file = git_dir / "COMMIT_EDITMSG"
        commit_msg_file.write_text("feat(equipment): Add tractor control interface")

        validator = hook_module.ChangelogEnforcementHook()

        # Mock the Path.cwd() to return our test repo
        with patch("pathlib.Path.cwd", return_value=temp_git_repo):
            has_marker = validator.has_skip_changelog_marker()
            assert has_marker is False, "Hook should not detect marker in regular commits"

            # Regular commits without marker must include CHANGELOG.md
            result = validator.validate_changelog_in_commit(["equipment.py"])
            assert (
                result is False
            ), "Hook should enforce CHANGELOG.md for commits without [skip-changelog]"

    def test_error_message_documents_skip_changelog_option(
        self, temp_git_repo: Path, hook_module
    ) -> None:
        """Test RED: Error message should document [skip-changelog] option.

        Agricultural scenario: Error message guides developers on using
        [skip-changelog] marker for CHANGELOG-only commits to prevent
        infinite regeneration loops in automated documentation workflows.
        """
        validator = hook_module.ChangelogEnforcementHook()
        error_message = validator.get_error_message()

        # Error message should mention [skip-changelog] option
        assert "[skip-changelog]" in error_message, "Error should document [skip-changelog] option"
        assert (
            "CHANGELOG-only" in error_message or "regeneration" in error_message
        ), "Error should explain when to use [skip-changelog]"
