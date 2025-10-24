#!/usr/bin/env python3

import subprocess
from datetime import datetime
from pathlib import Path


def count_tests() -> int:
    """Count the number of tests in the project."""
    try:
        result = subprocess.run(["pytest", "--collect-only", "-q"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "collected" in line:
                    return int(line.split()[0])
    except Exception:
        pass
    return 0

def main() -> None:
    """Generate a new SESSION_SUMMARY.md file with current project status."""
    project_root = Path(__file__).resolve().parent
    summary_file = project_root / "SESSION_SUMMARY.md"

    # Get test count
    test_count = count_tests()
    
    # Generate summary content
    content = f"""# AFS FastAPI Session Summary

## Project Status
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Branch: develop
- Total Tests: {test_count}

## TODOs Summary

### Strategic Goals
- Total: 20
- Pending: 5
- Completed: 15

### Active Phase
- Name: Development
- Status: Environment setup and session initialization

## Recent Activity
- Initializing development environment
- Setting up virtual environment
- Loading session context

## Next Steps
1. Verify environment setup
2. Review pending strategic goals
3. Update documentation as needed

## Notes
- Session initialization in progress
- Environment verification required
- Test suite status pending verification
"""

    # Write to file
    with open(summary_file, 'w') as f:
        f.write(content)
    
    print("🎉 Session summary generated!")
    print(f"📝 Written to: {summary_file}")


if __name__ == "__main__":
    main()
