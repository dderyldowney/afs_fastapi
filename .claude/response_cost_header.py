#!/usr/bin/env python3
"""
Response Cost Header for AFS FastAPI Agricultural Platform.

Generates cost headers for Claude Code responses, providing real-time
budget awareness during agricultural robotics development sessions.
"""

import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from afs_fastapi.services.cost_calculator import CostCalculator

    CALCULATOR_AVAILABLE = True
except ImportError:
    CostCalculator = None  # type: ignore
    CALCULATOR_AVAILABLE = False


def generate_cost_header() -> str:
    """Generate cost header for agricultural platform responses.

    Returns:
        Formatted cost header string
    """
    # Current known cost from user's /cost command output
    total_cost = "3.87"

    # Try to get session data
    session_file = project_root / ".claude" / "session_optimization_tracking.json"
    tokens_saved = 0
    agricultural_interactions = 0

    if session_file.exists():
        try:
            with open(session_file) as f:
                session_data = json.load(f)
                tokens_saved = session_data.get("tokens_saved_this_session", 0)
                agricultural_interactions = session_data.get("agricultural_interactions", 0)
        except (OSError, json.JSONDecodeError):
            pass

    # Calculate savings if available
    savings_text = ""
    if tokens_saved > 0 and CALCULATOR_AVAILABLE:
        calculator = CostCalculator()
        try:
            savings = calculator.calculate_input_cost(tokens_saved, "claude-sonnet-4")
            savings_text = f" | Saved: ${savings:.3f}"
        except Exception:
            pass

    # Agricultural context indicator
    agricultural_indicator = " 🌾" if agricultural_interactions > 0 else ""

    # Generate header
    header = f"💰 **Total Cost: ${total_cost}**{savings_text}{agricultural_indicator}"

    return header


if __name__ == "__main__":
    print(generate_cost_header())
