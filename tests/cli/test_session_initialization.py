"""
Test-First Development: Session Initialization Hook Tests

RED PHASE: These tests describe desired behavior for automatic session
initialization with 5-minute staleness detection to handle /new restarts.

Agricultural Context:
- Safety-critical multi-tractor coordination requires reliable context restoration
- ISO 18497 and ISO 11783 compliance context must persist across sessions
- Test-First Development methodology must be enforced continuously
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSessionInitializationHook:
    """Test automatic session initialization with staleness detection."""

    @pytest.fixture
    def temp_project_root(self, tmp_path: Path) -> Path:
        """Create temporary project structure for testing."""
        project_root = tmp_path / "afs_fastapi"
        project_root.mkdir()

        # Create .claude directory structure
        claude_dir = project_root / ".claude"
        claude_dir.mkdir()

        # Create bin directory with mock loadsession scripts
        bin_dir = project_root / "bin"
        bin_dir.mkdir()

        # Create the actual loadsession Python script
        loadsession_script = bin_dir / "loadsession"
        loadsession_script.write_text("#!/usr/bin/env python3\nprint('Session loaded')")
        loadsession_script.chmod(0o755)

        # Create the wrapper script that the hook expects
        wrapper_script = bin_dir / "run_loadsession.sh"
        wrapper_script.write_text('#!/bin/bash\npython3 "$(dirname "$0")"/loadsession "$@"')
        wrapper_script.chmod(0o755)

        return project_root

    @pytest.fixture
    def session_hook(self, temp_project_root: Path):
        """Create session initialization hook instance for testing."""
        # Import here to avoid issues with module loading
        sys.path.insert(0, str(temp_project_root.parent))

        # Mock the hook class - we'll patch Path.cwd() to use temp directory
        with patch("pathlib.Path.cwd", return_value=temp_project_root):
            # Import the actual hook module
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "session_initialization",
                Path(__file__).parent.parent.parent.parent
                / ".claude"
                / "hooks"
                / "session_initialization.py",
            )
            assert spec is not None
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)

            hook = module.UniversalSessionInitializationHook()
            return hook

    def test_detects_new_session_with_no_markers(
        self, session_hook, temp_project_root: Path
    ) -> None:
        """Test RED: Should detect new session when no markers exist.

        Agricultural scenario: First-time session initialization for
        tractor fleet coordination system deployment.
        """
        # Verify no markers exist
        assert not (temp_project_root / ".claude" / ".session_initialized").exists()
        assert not (temp_project_root / ".claude" / ".global_session_state").exists()

        # Should detect as new session
        assert session_hook.is_new_session() is True

    def test_detects_new_session_with_stale_markers_over_5_minutes(
        self, session_hook, temp_project_root: Path
    ) -> None:
        """Test RED: Should detect new session when markers are stale (>5 minutes).

        Agricultural scenario: Session restarted after /new command during
        multi-tractor field operation planning, requiring context restoration.
        """
        # Create markers with old timestamps (6 minutes ago)
        six_minutes_ago = time.time() - 360  # 6 minutes in seconds

        session_marker = temp_project_root / ".claude" / ".session_initialized"
        session_marker.touch()
        global_marker = temp_project_root / ".claude" / ".global_session_state"
        global_marker.touch()

        # Manually set old modification times
        import os

        os.utime(session_marker, (six_minutes_ago, six_minutes_ago))
        os.utime(global_marker, (six_minutes_ago, six_minutes_ago))

        # Create agent registry with old agent
        registry = {
            "agent_old_123": {
                "initialized_at": six_minutes_ago,
                "project_root": str(temp_project_root),
                "loadsession_executed": True,
            }
        }
        registry_file = temp_project_root / ".claude" / ".agent_registry.json"
        registry_file.write_text(json.dumps(registry))

        # Should detect as new session (markers too old)
        assert session_hook.is_new_session() is True

    def test_recognizes_active_session_with_fresh_markers(
        self, session_hook, temp_project_root: Path
    ) -> None:
        """Test RED: Should NOT reinitialize when markers are fresh (<5 minutes).

        Agricultural scenario: Ongoing session for tractor coordination
        development should not duplicate initialization during active work.
        """
        # Create fresh markers (2 minutes ago)
        two_minutes_ago = time.time() - 120  # 2 minutes in seconds

        session_marker = temp_project_root / ".claude" / ".session_initialized"
        session_marker.touch()
        global_marker = temp_project_root / ".claude" / ".global_session_state"
        global_marker.touch()

        # Set recent modification times
        import os

        os.utime(session_marker, (two_minutes_ago, two_minutes_ago))
        os.utime(global_marker, (two_minutes_ago, two_minutes_ago))

        # Create agent registry with recent agent
        registry = {
            "agent_recent_456": {
                "initialized_at": two_minutes_ago,
                "project_root": str(temp_project_root),
                "loadsession_executed": True,
            }
        }
        registry_file = temp_project_root / ".claude" / ".agent_registry.json"
        registry_file.write_text(json.dumps(registry))

        # Should recognize active session (markers fresh)
        assert session_hook.is_new_session() is False

    def test_boundary_condition_just_under_5_minutes(
        self, session_hook, temp_project_root: Path
    ) -> None:
        """Test RED: Should recognize active session just under 5 minutes (299 seconds).

        Agricultural scenario: Session that's 4:59 into tractor coordination
        development should not trigger reinitialization.

        Note: Tests 299 seconds (not 300) to avoid floating-point precision
        issues at exact boundary where test execution time pushes over 300.
        """
        # Create markers at 299 seconds (just under 5 minutes)
        just_under_five_minutes = time.time() - 299

        session_marker = temp_project_root / ".claude" / ".session_initialized"
        session_marker.touch()
        global_marker = temp_project_root / ".claude" / ".global_session_state"
        global_marker.touch()

        import os

        os.utime(session_marker, (just_under_five_minutes, just_under_five_minutes))
        os.utime(global_marker, (just_under_five_minutes, just_under_five_minutes))

        # Create agent registry with recent agent
        registry = {
            "agent_recent": {
                "initialized_at": just_under_five_minutes,
                "project_root": str(temp_project_root),
                "loadsession_executed": True,
            }
        }
        registry_file = temp_project_root / ".claude" / ".agent_registry.json"
        registry_file.write_text(json.dumps(registry))

        # At 299 seconds, should be considered active (299 + test time < 300)
        assert session_hook.is_new_session() is False

    def test_creates_markers_on_initialization(self, session_hook, temp_project_root: Path) -> None:
        """Test RED: Should create all three types of markers on initialization.

        Agricultural scenario: First initialization of tractor fleet
        coordination system creates persistent session state.
        """
        # Verify markers don't exist yet
        session_marker = temp_project_root / ".claude" / ".session_initialized"
        global_marker = temp_project_root / ".claude" / ".global_session_state"
        universal_marker = temp_project_root / ".claude" / ".universal_access_enabled"

        assert not session_marker.exists()
        assert not global_marker.exists()
        assert not universal_marker.exists()

        # Mark session as initialized
        session_hook.mark_session_initialized()

        # All markers should now exist
        assert session_marker.exists()
        assert global_marker.exists()
        assert universal_marker.exists()

    def test_registers_agent_in_registry(self, session_hook, temp_project_root: Path) -> None:
        """Test RED: Should register agent in persistent registry.

        Agricultural scenario: Track all agents (main + subagents) for
        multi-tractor coordination system development.
        """
        # Mark session initialized
        session_hook.mark_session_initialized()

        # Registry should exist and contain current agent
        registry_file = temp_project_root / ".claude" / ".agent_registry.json"
        assert registry_file.exists()

        registry = json.loads(registry_file.read_text())
        assert session_hook.current_agent_id in registry
        assert registry[session_hook.current_agent_id]["loadsession_executed"] is True

    def test_execute_loadsession_runs_script(self, session_hook, temp_project_root: Path) -> None:
        """Test RED: Should execute loadsession script successfully.

        Agricultural scenario: Restore full project context including
        ISO 18497 safety requirements and Test-First Development methodology.
        """
        # Execute loadsession
        result = session_hook.execute_loadsession()

        # Should succeed
        assert result is True

    def test_execute_loadsession_handles_missing_script(
        self, session_hook, temp_project_root: Path
    ) -> None:
        """Test RED: Should handle missing loadsession script gracefully.

        Agricultural scenario: Graceful degradation if loadsession script
        unavailable during development environment setup.
        """
        # Remove wrapper script that the hook expects
        wrapper_script = temp_project_root / "bin" / "run_loadsession.sh"
        wrapper_script.unlink()

        # Should fail gracefully
        result = session_hook.execute_loadsession()
        assert result is False

    def test_multiple_strategies_provide_redundancy(
        self, session_hook, temp_project_root: Path
    ) -> None:
        """Test RED: Should detect new session if ANY strategy indicates staleness.

        Agricultural scenario: Robust session detection ensures safety-critical
        context restoration even if some markers fail.
        """
        # Create scenario: session marker fresh, but global marker stale
        two_minutes_ago = time.time() - 120
        seven_minutes_ago = time.time() - 420

        session_marker = temp_project_root / ".claude" / ".session_initialized"
        session_marker.touch()
        global_marker = temp_project_root / ".claude" / ".global_session_state"
        global_marker.touch()

        import os

        os.utime(session_marker, (two_minutes_ago, two_minutes_ago))
        os.utime(global_marker, (seven_minutes_ago, seven_minutes_ago))

        # Should detect as new session (global marker stale)
        assert session_hook.is_new_session() is True

    def test_agent_registry_pruning_by_age(self, session_hook, temp_project_root: Path) -> None:
        """Test RED: Should ignore agents older than 5 minutes in registry.

        Agricultural scenario: Only recent agents count as active for
        multi-agent agricultural robotics coordination.
        """
        # Create registry with mix of fresh and stale agents
        current_time = time.time()
        two_minutes_ago = current_time - 120
        ten_minutes_ago = current_time - 600

        registry = {
            "agent_fresh": {
                "initialized_at": two_minutes_ago,
                "project_root": str(temp_project_root),
                "loadsession_executed": True,
            },
            "agent_stale": {
                "initialized_at": ten_minutes_ago,
                "project_root": str(temp_project_root),
                "loadsession_executed": True,
            },
        }
        registry_file = temp_project_root / ".claude" / ".agent_registry.json"
        registry_file.write_text(json.dumps(registry))

        # Create fresh file markers to test registry-only logic
        session_marker = temp_project_root / ".claude" / ".session_initialized"
        session_marker.touch()
        global_marker = temp_project_root / ".claude" / ".global_session_state"
        global_marker.touch()

        import os

        os.utime(session_marker, (two_minutes_ago, two_minutes_ago))
        os.utime(global_marker, (two_minutes_ago, two_minutes_ago))

        # Should recognize active session (fresh agent exists)
        assert session_hook.is_new_session() is False
