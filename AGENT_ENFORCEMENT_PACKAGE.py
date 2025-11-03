#!/usr/bin/env python3
"""
Portable Agent Enforcement System Package
==========================================

This script extracts and deploys the agent enforcement system to any Python project.
It ensures all agents automatically load and comply with KIS, PEP, TDD, and cleanup requirements.

Usage:
    python AGENT_ENFORCEMENT_PACKAGE.py /path/to/target/project

This will copy all enforcement files and configure them for the target project.
"""

import shutil
import sys
from pathlib import Path


class AgentEnforcementPackage:
    """Portable package for deploying agent enforcement system."""

    def __init__(self):
        self.enforcement_files = {
            # Core enforcement files
            "KIS_DIRECTIVE.md": "KIS_DIRECTIVE.md",
            "__agent_enforcer__.py": "__agent_enforcer__.py",
            "sitecustomize.py": "sitecustomize.py",
            "agent_config.py": "agent_config.py",
            "setup_agent.py": "setup_agent.py",
            # Documentation
            "AGENT_ENFORCEMENT_SYSTEM.md": "AGENT_ENFORCEMENT_SYSTEM.md",
            # Configuration templates
            "AGENT_ENFORCEMENT_PACKAGE.py": "AGENT_ENFORCEMENT_PACKAGE.py",
        }

        self.project_specific_content = {
            "README.md": "# Agent Enforcement System\n\nThis project uses mandatory agent compliance enforcement.\nSee `AGENT_ENFORCEMENT_SYSTEM.md` for details.\n",
            ".gitignore": "*.pyc\n__pycache__/\n.venv/\nvenv/\nenv/\n.env\n",
        }

    def validate_project(self, target_path: Path) -> bool:
        """Validate target project is a Python project."""
        if not target_path.exists():
            print(f"❌ Error: Target path {target_path} does not exist")
            return False

        # Check for Python project indicators
        python_indicators = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
        ]

        has_python = any((target_path / indicator).exists() for indicator in python_indicators)

        if not has_python:
            print("⚠️  Warning: No Python project indicators found")
            response = input("Continue anyway? (y/N): ")
            return response.lower().startswith("y")

        return True

    def copy_enforcement_files(self, source_root: Path, target_root: Path) -> None:
        """Copy core enforcement files to target project."""
        print("📦 Copying enforcement files...")

        for source_file, target_file in self.enforcement_files.items():
            source_path = source_root / source_file
            target_path = target_root / target_file

            if source_path.exists():
                print(f"  ✅ {target_file}")
                shutil.copy2(source_path, target_path)
            else:
                print(f"  ❌ Missing: {source_file}")

    def create_project_files(self, target_root: Path) -> None:
        """Create project-specific files."""
        print("📝 Creating project files...")

        for filename, content in self.project_specific_content.items():
            target_path = target_root / filename

            # Don't overwrite existing files (except .gitignore)
            if target_path.exists() and filename != ".gitignore":
                print(f"  ⏭️  Skipping existing {filename}")
                continue

            print(f"  ✅ {filename}")
            target_path.write_text(content)

    def update_gitignore(self, target_root: Path) -> None:
        """Update .gitignore with agent enforcement patterns."""
        gitignore_path = target_root / ".gitignore"

        agent_patterns = """
# Agent Enforcement System - DO NOT REMOVE THESE LINES
__pycache__/
*.pyc
.env
.venv/
venv/
env/
"""

        if gitignore_path.exists():
            existing = gitignore_path.read_text()
            if "Agent Enforcement System" not in existing:
                gitignore_path.write_text(existing + "\n" + agent_patterns)
                print("  ✅ Updated .gitignore")
            else:
                print("  ⏭️  .gitignore already contains agent patterns")
        else:
            gitignore_path.write_text(agent_patterns.strip() + "\n")
            print("  ✅ Created .gitignore")

    def verify_installation(self, target_root: Path) -> bool:
        """Verify enforcement system is properly installed."""
        print("🔍 Verifying installation...")

        required_files = [
            "KIS_DIRECTIVE.md",
            "__agent_enforcer__.py",
            "sitecustomize.py",
            "agent_config.py",
        ]

        missing = []
        for filename in required_files:
            if not (target_root / filename).exists():
                missing.append(filename)

        if missing:
            print(f"❌ Installation incomplete - missing files: {missing}")
            return False

        print("✅ All required files installed")
        return True

    def test_enforcement(self, target_root: Path) -> None:
        """Test that enforcement system loads properly."""
        print("🧪 Testing enforcement system...")

        try:
            # Add target to Python path and test import
            sys.path.insert(0, str(target_root))

            # Test agent config loading
            from agent_config import initialize_agent_compliance

            success = initialize_agent_compliance()

            if success:
                print("✅ Agent enforcement system active")
            else:
                print("❌ Agent enforcement system failed to initialize")

        except Exception as e:
            print(f"❌ Error testing enforcement: {e}")
        finally:
            # Clean up Python path
            if str(target_root) in sys.path:
                sys.path.remove(str(target_root))

    def deploy(self, target_path: str | Path) -> bool:
        """Deploy enforcement system to target project."""
        target_root = Path(target_path).resolve()
        source_root = Path(__file__).parent

        print(f"🚀 Deploying Agent Enforcement System to: {target_root}")
        print("=" * 60)

        # Validate target project
        if not self.validate_project(target_root):
            return False

        # Copy enforcement files
        self.copy_enforcement_files(source_root, target_root)

        # Create project-specific files
        self.create_project_files(target_root)

        # Update .gitignore
        self.update_gitignore(target_root)

        # Verify installation
        if not self.verify_installation(target_root):
            return False

        # Test enforcement
        self.test_enforcement(target_root)

        print("=" * 60)
        print("🎉 Agent Enforcement System deployed successfully!")
        print("\n📋 Next steps:")
        print("  1. cd " + str(target_root))
        print("  2. python setup_agent.py  # Test enforcement")
        print("  3. git add . && git commit -m 'feat: add agent enforcement system'")
        print("  4. All agents will now automatically load compliance requirements")

        return True


def main():
    """Main deployment entry point."""
    if len(sys.argv) != 2:
        print("Usage: python AGENT_ENFORCEMENT_PACKAGE.py /path/to/target/project")
        sys.exit(1)

    target_path = sys.argv[1]
    deployer = AgentEnforcementPackage()

    success = deployer.deploy(target_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
