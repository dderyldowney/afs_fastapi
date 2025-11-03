#!/bin/bash
# Quick deployment script for Agent Enforcement System

echo "🚀 Deploying Agent Enforcement System..."
echo "========================================="

# Check if we're in a git repository
if [ -d ".git" ]; then
    echo "✅ Git repository detected"
else
    echo "⚠️  Not a git repository (recommended but not required)"
fi

# Make deployment scripts executable
chmod +x deploy_agent_enforcement.sh
chmod +x AGENT_ENFORCEMENT_PACKAGE.py

echo "📦 Available deployment options:"
echo ""
echo "1. Automated Python deployment:"
echo "   python AGENT_ENFORCEMENT_PACKAGE.py ."
echo ""
echo "2. Bash script deployment:"
echo "   ./deploy_agent_enforcement.sh ."
echo ""
echo "3. Manual file activation:"
echo "   (Files are already in place - just need to test)"
echo ""

read -p "Choose deployment method (1/2/3): " choice

case $choice in
    1)
        echo "🔧 Running Python deployment..."
        python AGENT_ENFORCEMENT_PACKAGE.py .
        ;;
    2)
        echo "🔧 Running Bash deployment..."
        ./deploy_agent_enforcement.sh .
        ;;
    3)
        echo "✅ Files already in place - testing installation..."
        python setup_agent.py
        ;;
    *)
        echo "❌ Invalid choice. Please run this script again and choose 1, 2, or 3."
        exit 1
        ;;
esac

echo ""
echo "🎉 Agent Enforcement System deployment complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Test: python setup_agent.py"
echo "  2. Commit: git add . && git commit -m 'feat: add agent enforcement system'"
echo "  3. All agents will now automatically comply with KIS, PEP, TDD requirements"