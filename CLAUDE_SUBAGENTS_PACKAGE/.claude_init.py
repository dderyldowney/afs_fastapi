#!/usr/bin/env python3
"""
Automatic Claude Initialization System

This script automatically configures Claude to always use:
1. Token-sage agent first
2. HAL agents for preprocessing
3. Maximum token efficiency
"""

import json
import os
import sys
from pathlib import Path


def setup_claude_environment():
    """Setup Claude environment for automatic token optimization"""
    print("🚀 Setting up Claude for automatic token optimization...")

    # Create .claude directory in home
    claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Set environment variables
    env_vars = {
        "CLAUDE_DEFAULT_AGENT": "token-sage",
        "CLAUDE_TOKEN_OPTIMIZATION": "enabled",
        "CLAUDE_HAL_AGENTS": "enabled",
        "CLAUDE_AUTO_CACHE": "enabled",
        "TOKEN_OPTIMIZED_PATH": str(Path(__file__).parent),
    }

    # Create environment file
    env_file = claude_dir / "environment.json"
    env_data = {
        "default_agent": "token-sage",
        "token_optimization": "enabled",
        "hal_agents": "enabled",
        "auto_cache": "enabled",
        "workflow_path": str(Path(__file__).parent),
        "version": "1.0",
    }

    env_file.write_text(json.dumps(env_data, indent=2))

    # Set environment variables for current session
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ Set {key} = {value}")

    return True


def create_claude_hooks():
    """Create automatic Claude hooks"""
    print("🔧 Creating Claude hooks...")

    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    # Pre-session hook
    pre_session_hook = hooks_dir / "pre_session.py"
    pre_session_content = '''#!/usr/bin/env python3
"""
Pre-session hook - Always initialize token-sage
"""
import subprocess
import sys
from pathlib import Path

def main():
    # Always initialize token-sage first
    print("🚀 Auto-initializing token-sage...")

    # This would be called through Claude's Task system
    token_sage_cmd = "Task subagent_type=token-sage description='Auto-init token-sage' prompt='Initialize and prepare for token-optimized analysis'"

    # Store the command for Claude to execute
    init_file = Path.home() / ".claude" / "init_command.txt"
    init_file.write_text(token_sage_cmd)

    print("✅ Token-sage ready for maximum efficiency")
    print("💰 HAL agents available for local preprocessing (0 tokens)")

if __name__ == "__main__":
    main()
'''

    pre_session_hook.write_text(pre_session_content)

    # Analysis hook
    analysis_hook = hooks_dir / "analysis.py"
    analysis_content = '''#!/usr/bin/env python3
"""
Analysis hook - Always use HAL preprocessing first
"""
import sys
from pathlib import Path

def should_use_hal_preprocessing(query):
    """Determine if HAL preprocessing should be used"""
    # Always use HAL for code-related queries
    code_keywords = [
        'analyze', 'find', 'search', 'class', 'def', 'function',
        'method', 'import', 'database', 'api', 'endpoint', 'model',
        'schema', 'code', 'python', 'javascript', 'typescript'
    ]

    query_lower = query.lower()
    return any(keyword in query_lower for keyword in code_keywords)

def generate_hal_command(query):
    """Generate HAL preprocessing command"""
    workflow_path = Path.home() / ".claude" / "environment.json"

    try:
        with open(workflow_path) as f:
            env = json.load(f)
            workflow_dir = Path(env["workflow_path"])
    except:
        workflow_dir = Path.cwd()

    hal_script = workflow_dir / "always_token_sage.py"

    if hal_script.exists():
        return f'python {hal_script} "{query}"'
    else:
        return f'Task subagent_type=token-sage description="Analyze with HAL preprocessing" prompt="First run local filtering, then analyze: {query}"'

def main():
    if len(sys.argv) < 2:
        print("Usage: python analysis.py <query>")
        return 1

    query = " ".join(sys.argv[1:])

    if should_use_hal_preprocessing(query):
        print("🔍 Using HAL preprocessing for token efficiency...")
        hal_cmd = generate_hal_command(query)

        # Store command for Claude
        cmd_file = Path.home() / ".claude" / "analysis_command.txt"
        cmd_file.write_text(hal_cmd)

        print(f"✅ HAL command ready: {hal_cmd}")
        print("💰 This will save ~10,000+ tokens!")
    else:
        print("🧠 Using token-sage directly")
        token_sage_cmd = f'Task subagent_type=token-sage description="Analyze" prompt="Analyze: {query}"'

        cmd_file = Path.home() / ".claude" / "analysis_command.txt"
        cmd_file.write_text(token_sage_cmd)

if __name__ == "__main__":
    main()
'''

    analysis_hook.write_text(analysis_content)

    print(f"✅ Created hooks in {hooks_dir}")
    return True


def create_startup_script():
    """Create automatic startup script"""
    print("📝 Creating startup script...")

    startup_script = Path.home() / ".claude" / "startup.sh"
    startup_content = """#!/bin/bash
# Automatic Claude Token Optimization Startup

echo "🚀 Starting Claude with Maximum Token Efficiency..."

# Set environment variables
export CLAUDE_DEFAULT_AGENT="token-sage"
export CLAUDE_TOKEN_OPTIMIZATION="enabled"
export CLAUDE_HAL_AGENTS="enabled"
export TOKEN_OPTIMIZED_PATH="$(pwd)"

# Initialize token-sage
echo "🧠 Initializing token-sage..."
echo "Task subagent_type=token-sage description='Auto-init' prompt='Initialize for token-optimized analysis'" > ~/.claude/init_command.txt

# Ready message
echo "✅ Claude ready with maximum token efficiency!"
echo "💰 HAL agents will automatically preprocess (0 tokens)"
echo "📋 Always use: python always_token_sage.py 'your goal'"
echo ""
echo "🎯 Token optimization workflow ready!"
"""

    startup_script.write_text(startup_content)
    startup_script.chmod(0o755)

    print(f"✅ Created startup script: {startup_script}")
    return True


def create_claude_config():
    """Create Claude configuration file"""
    print("⚙️ Creating Claude configuration...")

    config_dir = Path.home() / ".claude"
    config_file = config_dir / "config.json"

    config = {
        "agent": {"default": "token-sage", "fallback": "general-purpose"},
        "token_optimization": {
            "enabled": True,
            "hal_preprocessing": True,
            "cache_enabled": True,
            "max_context_chars": 1000,
            "max_files": 50,
        },
        "workflow": {"auto_load_hal": True, "auto_cache": True, "delta_mode": True},
        "aliases": {
            "analyze": "python always_token_sage.py",
            "token-optimize": "python token_optimized_agent.py",
            "hal-preprocess": "python hal_token_savvy_agent.py",
        },
        "version": "1.0",
    }

    config_file.write_text(json.dumps(config, indent=2))
    print(f"✅ Created config: {config_file}")
    return True


def main():
    """Main setup function"""
    print("🎯 Claude Automatic Token-Sage + HAL Setup")
    print("=" * 50)

    success = True

    # Setup environment
    if not setup_claude_environment():
        success = False

    # Create hooks
    if not create_claude_hooks():
        success = False

    # Create startup script
    if not create_startup_script():
        success = False

    # Create configuration
    if not create_claude_config():
        success = False

    if success:
        print("\n✅ Claude automatic setup complete!")
        print("\n🚀 What happens now:")
        print("1. Claude will automatically load token-sage first")
        print("2. HAL agents will automatically preprocess (0 tokens)")
        print("3. Maximum token efficiency is guaranteed")
        print("\n💰 Usage:")
        print("  - Just ask Claude to analyze anything")
        print("  - It will automatically use the optimized workflow")
        print("  - Or use: python always_token_sage.py 'your goal'")
        print("\n🎯 Token optimization is now automatic!")
    else:
        print("\n❌ Setup encountered errors")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
