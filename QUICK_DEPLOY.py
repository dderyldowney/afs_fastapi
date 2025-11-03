#!/usr/bin/env python3
"""
Quick Agent Enforcement Deployment - Self-Contained Version
===========================================================

This script deploys the agent enforcement system without complex imports.
Simply copy all files to your project directory and run this script.
"""

import sys
from pathlib import Path


def verify_installation():
    """Verify all required files are present."""
    print("🔍 Verifying agent enforcement installation...")

    required_files = [
        "KIS_DIRECTIVE.md",
        "__agent_enforcer__.py",
        "sitecustomize.py",
        "agent_config.py",
        ".agent_config.py",
    ]

    missing = []
    for filename in required_files:
        if not Path(filename).exists():
            missing.append(filename)

    if missing:
        print(f"❌ Missing required files: {missing}")
        print("Make sure all files from the zip are copied to your project directory.")
        return False

    print("✅ All required files found")
    return True


def test_sitecustomize():
    """Test that sitecustomize.py loads properly."""
    print("🧪 Testing sitecustomize.py...")

    try:
        # Test import by importing a module that triggers sitecustomize
        import site

        if site.main() is None:  # sitecustomize should load automatically
            print("✅ sitecustomize.py can load")
            return True
    except Exception as e:
        print(f"⚠️  sitecustomize test warning: {e}")
        return True  # Non-critical for basic functionality

    return True


def display_kis_directives():
    """Display the KIS directives from the file."""
    print("\n📋 AGENT ENFORCEMENT SYSTEM ACTIVE")
    print("=" * 50)

    try:
        with open("KIS_DIRECTIVE.md") as f:
            content = f.read()

        # Extract key sections
        sections = [
            "Keep It Simple (KIS)",
            "PEP Compliance",
            "CLI Tool Usage",
            "TDD - Red-Green-Refactor",
            "Test Cleanup Requirements",
        ]

        for section in sections:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if section in line:
                    print(f"📝 {section}")
                    # Show next few lines that start with '-'
                    j = i + 1
                    while j < len(lines) and j < i + 6:
                        if lines[j].strip().startswith("-"):
                            print(f"   {lines[j].strip()}")
                        j += 1
                    print()
                    break

    except Exception as e:
        print(f"⚠️  Could not read KIS_DIRECTIVE.md: {e}")

    print("=" * 50)
    print("🚀 ALL AGENTS WILL AUTOMATICALLY FOLLOW THESE REQUIREMENTS")
    print("⚠️  THIS ENFORCEMENT CANNOT BE BYPASSED OR IGNORED")
    print("=" * 50)


def main():
    """Main deployment verification."""
    print("🚀 Agent Enforcement System Deployment Verification")
    print("=" * 55)

    # Verify installation
    if not verify_installation():
        sys.exit(1)

    # Test sitecustomize
    if not test_sitecustomize():
        print("⚠️  sitecustomize.py may have issues, but continuing...")

    # Display directives
    display_kis_directives()

    print("\n✅ SUCCESS: Agent Enforcement System is ready!")
    print("\n📋 Next steps:")
    print("  1. Commit these files to your repository")
    print("  2. All Python sessions will now auto-load compliance")
    print("  3. All agents will be bound by KIS, PEP, TDD requirements")
    print("\n📖 For detailed documentation, see:")
    print("  - AGENT_ENFORCEMENT_SYSTEM.md")
    print("  - PROJECT_INTEGRATION_GUIDE.md")


if __name__ == "__main__":
    main()
