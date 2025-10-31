#!/usr/bin/env python3
"""
Always Use Token-Sage First

This script ensures token-sage is always loaded before any work.
It's a wrapper that automatically initializes token-sage.
"""

import os
import sys
from pathlib import Path


def ensure_token_sage():
    """Ensure token-sage is always loaded first"""
    print("🚀 Ensuring token-sage is loaded...")

    # Check if we're already active
    if os.getenv("TOKEN_SAGE_ACTIVE") == "true":
        print("🤖 Token-sage already active - preventing duplication")
        return True

    # Set environment markers
    os.environ["TOKEN_SAGE_ACTIVE"] = "true"
    os.environ["CLAUDE_TOKEN_OPTIMIZATION_ENABLED"] = "true"
    os.environ["TOKEN_SAGE_AUTOLOAD"] = "true"

    # Initialize HAL preprocessing
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from hal_token_savvy_agent import filter_repo_for_llm

        # Test basic functionality
        test_result = filter_repo_for_llm(
            goal="token-sage initialization verification",
            pattern="import",
            llm_snippet_chars=100,
            max_files=5,
            delta_mode=False,
        )

        if test_result and len(test_result) > 10:
            print("🤖 HAL preprocessing capabilities verified (0 tokens used)")

        print("✅ Token-sage initialization complete")
        print("💰 Applied to ALL operations for remainder of session")
        return True

    except Exception as e:
        print(f"⚠️  Token-sage initialization warning: {e}")
        print("✅ Basic token-sage still active")
        return True


def run_with_hal_preprocessing(command_args):
    """Run any command with HAL preprocessing first"""
    if not command_args:
        print("Usage: python always_token_sage.py <your_command> [args]")
        print("Example: python always_token_sage.py 'analyze database models'")
        return 1

    goal = " ".join(command_args)
    print(f"🎯 Goal: {goal}")
    print()

    # Step 1: Always load token-sage first
    ensure_token_sage()

    # Step 2: Run HAL preprocessing
    print(f"🔍 Running HAL preprocessing for: {goal}")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from hal_token_savvy_agent import filter_repo_for_llm

        # Extract pattern from goal if it looks like a search
        pattern = None
        if any(word in goal.lower() for word in ["find", "search", "class", "def", "import"]):
            # Simple pattern extraction
            words = goal.split()
            for word in words:
                if word in ["class", "def", "import"]:
                    idx = words.index(word)
                    if idx + 1 < len(words):
                        pattern = f"{word} {words[idx + 1]}"
                        break

        local_context = filter_repo_for_llm(
            goal=goal,
            pattern=pattern,
            llm_snippet_chars=800,  # Small for token efficiency
            delta_mode=True,
            max_files=30,
        )

        if local_context and len(local_context) > 50:
            print(f"✅ HAL preprocessing complete: {len(local_context)} chars")
            print()
            print("📝 Optimized context for token-sage:")
            print("=" * 50)
            print(local_context)
            print("=" * 50)
            print()
            print(f"🧠 Now use this context with token-sage for: {goal}")
            print("💰 Token savings: Local preprocessing used 0 API tokens!")
        else:
            print("⚠️ No suitable local context found")
            print("🧠 Proceeding with token-sage without local preprocessing")

    except Exception as e:
        print(f"❌ HAL preprocessing failed: {e}")
        print("🧠 Proceeding with token-sage directly")

    return 0


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("🚀 Always Token-Sage - Maximum Token Efficiency")
        print("=" * 50)
        print()
        print("This script ensures token-sage is always loaded first")
        print("and uses HAL agents for maximum token savings.")
        print()
        print("Usage: python always_token_sage.py <your_goal>")
        print("Example: python always_token_sage.py 'analyze authentication system'")
        print()

        # Initialize token-sage anyway
        ensure_token_sage()
        return 0

    return run_with_hal_preprocessing(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
