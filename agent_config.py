"""
Central Agent Configuration - AUTO-LOADED BY ALL AGENTS

This file provides centralized agent instructions and requirements.
ALL agents must load and adhere to these non-negotiable directives.
"""

import os
from pathlib import Path

# Auto-load requirement - This file must be imported by all agents
AGENT_DIRECTIVE_VERSION = "1.0.0"
AGENT_COMPLIANCE_REQUIRED = True


def load_agent_directives():
    """
    Automatically loads and returns all agent directives.
    Called automatically by agent initialization.
    """
    base_dir = Path(__file__).parent
    directive_file = base_dir / "KIS_DIRECTIVE.md"

    if not directive_file.exists():
        raise RuntimeError("CRITICAL: KIS_DIRECTIVE.md not found - Agent cannot proceed")

    directives = {
        "kis_principles": [
            "Simplicity over complexity",
            "Clarity over cleverness",
            "Essential over extra",
            "Readability over optimization",
            "Maintainability over features",
        ],
        "pep_compliance": [
            "PEP 8: Style Guide",
            "PEP 484: Type Hints",
            "PEP 695: Type Parameters",
            "PEP 570: Positional-Only",
            "PEP 572: Assignment Expressions",
            "PEP 585: Built-in Generics",
            "PEP 604: Union Types",
            "PEP 613: TypeAlias",
            "PEP 616: String Methods",
        ],
        "cli_tools_first": ["grep", "find", "sed", "awk", "ls", "head", "tail"],
        "tdd_methodology": ["RED", "GREEN", "REFACTOR", "REPEAT"],  # MANDATORY FOR ALL CHANGES
        "vigilance_checklist": [
            "Can this be simpler?",
            "Is there redundant code?",
            "Are there unused variables/imports?",
            "Can CLI tools replace reading files?",
            "Does this follow PEP standards?",
            "Is this over-engineered?",
            "Will tests cleanup all artifacts?",
            "Is this TDD compliant (RED-GREEN-REFACTOR)?",
        ],
        "test_cleanup_requirements": [
            "ZERO artifacts after test completion",
            "Clean up temporary directories",
            "Remove database files",
            "Reset environment variables",
            "Verify cleanup with assertions",
        ],
    }

    return directives


# Auto-execution - All agents must run this
def initialize_agent_compliance():
    """
    Auto-initializes agent compliance checking.
    This function must be called by all agents at startup.
    """
    try:
        load_agent_directives()
        print(f"[AGENT] Loaded KIS Directives v{AGENT_DIRECTIVE_VERSION}")
        print(f"[AGENT] Compliance: {'MANDATORY' if AGENT_COMPLIANCE_REQUIRED else 'OPTIONAL'}")
        return True
    except Exception as e:
        print(f"[AGENT] CRITICAL ERROR: {e}")
        return False


# Auto-load compliance
if __name__ == "__main__" or "AGENT_INITIALIZED" not in os.environ:
    success = initialize_agent_compliance()
    if not success:
        raise RuntimeError("Agent initialization failed - Cannot proceed")
    os.environ["AGENT_INITIALIZED"] = "true"

# Export for direct imports
__all__ = [
    "AGENT_COMPLIANCE_REQUIRED",
    "AGENT_DIRECTIVE_VERSION",
    "initialize_agent_compliance",
    "load_agent_directives",
]
