#!/bin/bash
# Generated command script for CMD-CANLATENCY
# Proves acceptance criteria: AC-CAN-LATENCY

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🎯 Executing command: CMD-CANLATENCY"
echo "📋 Validating AC: AC-CAN-LATENCY"
echo "📁 Working directory: $(pwd)"

# Load command YAML and execute
python3 -c "
import yaml
import subprocess
import sys
from pathlib import Path

# Load command definition
with open('ToDoWrite/configs/commands/CMD-CANLATENCY.yaml', 'r') as f:
    cmd_data = yaml.safe_load(f)

# Execute shell command
shell_cmd = cmd_data['command']['run']['shell']
print(f'Executing: {shell_cmd}')

try:
    result = subprocess.run(
        shell_cmd,
        shell=True,
        check=True,
        capture_output=True,
        text=True,
        env=cmd_data['command']['run']['env']
    )
    print('✅ Command completed successfully')
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f'❌ Command failed: {e}')
    print(f'STDOUT: {e.stdout}')
    print(f'STDERR: {e.stderr}')
    sys.exit(1)
"

echo "✅ CMD-CANLATENCY completed"
