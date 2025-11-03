#!/usr/bin/env python3
"""
Agent Setup Script - AUTO-LOAD FOR ALL AGENTS

This script ensures all agents automatically load and comply with the directives.
Run this before any agent interaction or development work.
"""

import sys
from pathlib import Path


def load_agent_directives():
    """Load and display agent directives."""
    config_file = Path(__file__).parent / ".agent_config.py"
    directive_file = Path(__file__).parent / "KIS_DIRECTIVE.md"

    if not config_file.exists():
        print("❌ ERROR: .agent_config.py not found")
        return False

    if not directive_file.exists():
        print("❌ ERROR: KIS_DIRECTIVE.md not found")
        return False

    try:
        # Import the agent config
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            from agent_config import initialize_agent_compliance, load_agent_directives
        except ImportError:
            # Fallback for standalone deployment
            from .agent_config import initialize_agent_compliance, load_agent_directives

        # Initialize compliance
        success = initialize_agent_compliance()
        if success:
            load_agent_directives()

            print("🚀 AGENT DIRECTIVES LOADED SUCCESSFULLY")
            print("=" * 50)
            print("📋 MANDATORY REQUIREMENTS:")
            print("  ✅ KIS (Keep It Simple) Principles")
            print("  ✅ PEP Compliance (ALL PEPs)")
            print("  ✅ CLI Tool Usage (grep, find, sed before Read)")
            print("  ✅ Constant Vigilance for Simplification")
            print("  ✅ TDD Red-Green-Refactor Methodology")
            print("  ✅ Test Simplification Principles")
            print("=" * 50)
            print("⚠️  VIOLATIONS ARE NOT ACCEPTABLE")
            print("⚠️  MONITORING IS ACTIVE")
            print("=" * 50)

            return True
        else:
            return False

    except Exception as e:
        print(f"❌ ERROR loading directives: {e}")
        return False


if __name__ == "__main__":
    success = load_agent_directives()
    sys.exit(0 if success else 1)
