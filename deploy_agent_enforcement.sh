#!/bin/bash
# Agent Enforcement System Deployment Script
# =========================================
# Simple bash script to deploy agent enforcement to any project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if target directory provided
if [ $# -eq 0 ]; then
    print_error "Usage: $0 /path/to/target/project"
    exit 1
fi

TARGET_DIR="$1"
TODOWRITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_status "Deploying Agent Enforcement System to: $TARGET_DIR"
echo "================================================================="

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    print_error "Target directory does not exist: $TARGET_DIR"
    exit 1
fi

# Check if this looks like a Python project
PYTHON_INDICATORS=("pyproject.toml" "setup.py" "requirements.txt" "Pipfile" "poetry.lock")
IS_PYTHON_PROJECT=false

for indicator in "${PYTHON_INDICATORS[@]}"; do
    if [ -f "$TARGET_DIR/$indicator" ]; then
        IS_PYTHON_PROJECT=true
        break
    fi
done

if [ "$IS_PYTHON_PROJECT" = false ]; then
    print_warning "No Python project indicators found in $TARGET_DIR"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled"
        exit 0
    fi
fi

# Files to copy
ENFORCEMENT_FILES=(
    "KIS_DIRECTIVE.md"
    "__agent_enforcer__.py"
    "sitecustomize.py"
    "agent_config.py"
    "setup_agent.py"
    "AGENT_ENFORCEMENT_SYSTEM.md"
    "AGENT_ENFORCEMENT_PACKAGE.py"
)

# Copy enforcement files
print_status "Copying enforcement files..."
for file in "${ENFORCEMENT_FILES[@]}"; do
    if [ -f "$TODOWRITE_DIR/$file" ]; then
        cp "$TODOWRITE_DIR/$file" "$TARGET_DIR/"
        print_success "✅ $file"
    else
        print_error "❌ Missing file: $file"
    fi
done

# Create/update .gitignore
GITIGNORE_FILE="$TARGET_DIR/.gitignore"
if [ -f "$GITIGNORE_FILE" ]; then
    if ! grep -q "Agent Enforcement System" "$GITIGNORE_FILE"; then
        echo "" >> "$GITIGNORE_FILE"
        echo "# Agent Enforcement System - DO NOT REMOVE THESE LINES" >> "$GITIGNORE_FILE"
        echo "__pycache__/" >> "$GITIGNORE_FILE"
        echo "*.pyc" >> "$GITIGNORE_FILE"
        echo ".env" >> "$GITIGNORE_FILE"
        echo ".venv/" >> "$GITIGNORE_FILE"
        echo "venv/" >> "$GITIGNORE_FILE"
        echo "env/" >> "$GITIGNORE_FILE"
        print_success "✅ Updated .gitignore"
    else
        print_status "⏭️ .gitignore already contains agent patterns"
    fi
else
    echo "# Agent Enforcement System" > "$GITIGNORE_FILE"
    echo "__pycache__/" >> "$GITIGNORE_FILE"
    echo "*.pyc" >> "$GITIGNORE_FILE"
    echo ".env" >> "$GITIGNORE_FILE"
    echo ".venv/" >> "$GITIGNORE_FILE"
    echo "venv/" >> "$GITIGNORE_FILE"
    echo "env/" >> "$GITIGNORE_FILE"
    print_success "✅ Created .gitignore"
fi

# Verify installation
print_status "Verifying installation..."
REQUIRED_FILES=("KIS_DIRECTIVE.md" "__agent_enforcer__.py" "sitecustomize.py" "agent_config.py")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$TARGET_DIR/$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    print_error "Installation incomplete - missing files: ${MISSING_FILES[*]}"
    exit 1
fi

print_success "✅ All required files installed"

# Test enforcement system
print_status "Testing enforcement system..."
cd "$TARGET_DIR"

if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from agent_config import initialize_agent_compliance
    success = initialize_agent_compliance()
    if success:
        print('✅ Agent enforcement system active')
    else:
        print('❌ Agent enforcement system failed to initialize')
        sys.exit(1)
except Exception as e:
    print(f'❌ Error testing enforcement: {e}')
    sys.exit(1)
"; then
    print_success "✅ Enforcement system test passed"
else
    print_error "❌ Enforcement system test failed"
    exit 1
fi

echo "================================================================="
print_success "🎉 Agent Enforcement System deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. cd $TARGET_DIR"
echo "  2. python3 setup_agent.py    # Test enforcement"
echo "  3. git add . && git commit -m 'feat: add agent enforcement system'"
echo "  4. All agents will now automatically load compliance requirements"
echo ""
print_warning "⚠️  The enforcement system is now ACTIVE and cannot be bypassed!"
print_warning "    All agents will automatically load KIS, PEP, TDD, and cleanup requirements."