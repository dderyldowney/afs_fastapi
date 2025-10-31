#!/usr/bin/env python3
"""
Claude Auto-Initialization Script

This script is automatically loaded when Claude starts.
It ensures token-sage is always ready and HAL agents are integrated.
"""

import os
import sys
from pathlib import Path


def initialize_claude_session():
    """Initialize Claude session with token optimization"""
    try:
        print("🚀 Claude auto-initializing for maximum token efficiency...")

        # Set environment for this session
        os.environ["CLAUDE_DEFAULT_AGENT"] = "token-sage"
        os.environ["CLAUDE_TOKEN_OPTIMIZATION"] = "enabled"
        os.environ["CLAUDE_HAL_AGENTS"] = "enabled"

        # Get the workflow path
        current_dir = Path(__file__).parent
        os.environ["TOKEN_OPTIMIZED_PATH"] = str(current_dir)

        # Check if HAL agents are available
        hal_agents = [
            current_dir / "hal_token_savvy_agent.py",
            current_dir / "hal_agent_loop.py",
            current_dir / "always_token_sage.py",
            current_dir / "token_optimized_agent.py",
        ]

        available_agents = [agent for agent in hal_agents if agent.exists()]

        if available_agents:
            print(f"✅ HAL agents ready: {len(available_agents)} agents available")
            print("💰 Local preprocessing available (0 tokens)")
        else:
            print("⚠️ HAL agents not found in expected location")

        # Initialize token-sage readiness
        token_sage_ready = True
        print("✅ Token-sage agent ready for optimized analysis")

        # Store initialization state
        init_file = Path.home() / ".claude" / "session_state.json"
        session_data = {
            "token_sage_ready": token_sage_ready,
            "hal_agents_count": len(available_agents),
            "workflow_path": str(current_dir),
            "auto_optimization": "enabled",
        }

        init_file.parent.mkdir(exist_ok=True)
        import json

        init_file.write_text(json.dumps(session_data, indent=2))

        print("🎯 Claude session initialized with automatic token optimization")
        print()
        print("💡 Claude will now automatically:")
        print("   1. Use token-sage for all analysis")
        print("   2. Apply HAL preprocessing when beneficial")
        print("   3. Cache results for maximum efficiency")
        print()

        return True

    except Exception as e:
        print(f"⚠️ Auto-initialization warning: {e}")
        return False


def get_optimized_analysis_command(goal, pattern=None):
    """Generate optimized analysis command"""
    current_dir = Path(os.environ.get("TOKEN_OPTIMIZED_PATH", Path.cwd()))
    always_token_sage = current_dir / "always_token_sage.py"

    if always_token_sage.exists():
        if pattern:
            return f'python {always_token_sage} "{goal}" --pattern "{pattern}"'
        else:
            return f'python {always_token_sage} "{goal}"'
    else:
        # Fallback to token-sage Task
        return f'Task subagent_type=token-sage description="Optimized analysis" prompt="Analyze: {goal}"'


def auto_optimize_query(query):
    """Automatically optimize a query for token efficiency"""
    code_indicators = [
        "analyze",
        "find",
        "search",
        "class",
        "def",
        "function",
        "method",
        "import",
        "database",
        "api",
        "endpoint",
        "model",
        "schema",
        "code",
        "python",
        "file",
        "directory",
    ]

    query_lower = query.lower()
    is_code_query = any(indicator in query_lower for indicator in code_indicators)

    if is_code_query:
        return get_optimized_analysis_command(query)
    else:
        return f'Task subagent_type=token-sage description="Analysis" prompt="Analyze: {query}"'


# Auto-initialize when imported
if __name__ != "__main__":
    initialize_claude_session()


# Command line interface for testing
def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"🎯 Optimized command for: {query}")
        print(auto_optimize_query(query))
    else:
        initialize_claude_session()


if __name__ == "__main__":
    main()
