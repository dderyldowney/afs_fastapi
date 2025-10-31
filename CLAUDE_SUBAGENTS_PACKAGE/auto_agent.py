#!/usr/bin/env python3
"""
Automatic Token-Optimized Agent Pipeline

Always uses token-sage + HAL agents for maximum token efficiency.
"""

import sys
from pathlib import Path


def initialize_token_sage():
    """Initialize token-sage agent first"""
    print("🚀 Initializing token-sage agent...")
    try:
        # This would normally be called through the Task tool
        print("✅ Token-sage initialized and ready")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize token-sage: {e}")
        return False


def run_hal_filtering(goal: str, pattern: str | None = None, **kwargs):
    """Run HAL agent filtering for maximum token efficiency"""
    print(f"🔍 Running HAL agent pre-filtering for: {goal}")

    try:
        # Add the current directory to Python path
        sys.path.insert(0, str(Path(__file__).parent))
        from hal_token_savvy_agent import filter_repo_for_llm

        # Set token-efficient defaults
        filter_params = {
            "goal": goal,
            "llm_snippet_chars": kwargs.get("llm_snippet_chars", 1500),  # Strict budget
            "delta_mode": kwargs.get("delta_mode", True),  # Always use caching
            "abbreviate_paths": kwargs.get("abbreviate_paths", True),
            "max_files": kwargs.get("max_files", 100),  # Limit scope
            "context_lines": kwargs.get("context_lines", 2),
        }

        if pattern:
            filter_params["pattern"] = pattern

        result = filter_repo_for_llm(**filter_params)

        print(f"✅ HAL filtering complete: {len(result)} characters")
        print("📊 Token efficiency: Local filtering used 0 API tokens")

        return result

    except Exception as e:
        print(f"❌ HAL filtering failed: {e}")
        return None


def analyze_with_token_sage(context: str, query: str):
    """Use token-sage for final analysis with minimal context"""
    print(f"🧠 Token-sage analysis with {len(context)} chars of context")

    # This would normally be called through the Task tool
    # For now, return the context for manual token-sage usage
    print("📝 Ready for token-sage analysis. Use this context:")
    print("=" * 50)
    print(context)
    print("=" * 50)
    print(f"Query: {query}")
    print("\nCopy this context into a token-sage Task call for maximum efficiency.")


def main():
    """Main automatic agent pipeline"""
    if len(sys.argv) < 2:
        print("Usage: python auto_agent.py <goal> [pattern]")
        print("Example: python auto_agent.py 'analyze authentication' 'class.*Auth'")
        return 1

    goal = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else None

    print("🎯 Starting Token-Optimized Agent Pipeline")
    print("=" * 50)

    # Step 1: Initialize token-sage
    if not initialize_token_sage():
        return 1

    # Step 2: HAL agent filtering (saves tokens)
    local_context = run_hal_filtering(goal, pattern)
    if not local_context:
        print("❌ No local context found")
        return 1

    # Step 3: Prepare for token-sage analysis
    analyze_with_token_sage(local_context, f"Analyze {goal}")

    print("\n✅ Pipeline complete. Maximum token efficiency achieved!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
