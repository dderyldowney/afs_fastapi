#!/bin/bash
# Claude Automatic Token Optimization Setup

echo "🚀 Setting up Claude for automatic token-sage + HAL workflow..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the Python setup script
python "$SCRIPT_DIR/.claude_init.py"

# Create symbolic links for easy access
echo "🔗 Creating convenient aliases..."

# Add to shell profile if not already there
SHELL_PROFILE=""
if [[ -f "$HOME/.zshrc" ]]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [[ -f "$HOME/.bash_profile" ]]; then
    SHELL_PROFILE="$HOME/.bash_profile"
fi

if [[ -n "$SHELL_PROFILE" ]]; then
    if ! grep -q "claude-auto-setup" "$SHELL_PROFILE"; then
        echo "" >> "$SHELL_PROFILE"
        echo "# Claude automatic token optimization" >> "$SHELL_PROFILE"
        echo "export CLAUDE_DEFAULT_AGENT=\"token-sage\"" >> "$SHELL_PROFILE"
        echo "export CLAUDE_TOKEN_OPTIMIZATION=\"enabled\"" >> "$SHELL_PROFILE"
        echo "export TOKEN_OPTIMIZED_PATH=\"$SCRIPT_DIR\"" >> "$SHELL_PROFILE"
        echo "alias claude-opt='python $SCRIPT_DIR/always_token_sage.py'" >> "$SHELL_PROFILE"
        echo "alias token-optimize='python $SCRIPT_DIR/token_optimized_agent.py'" >> "$SHELL_PROFILE"
        echo "alias hal-preprocess='python $SCRIPT_DIR/hal_token_savvy_agent.py'" >> "$SHELL_PROFILE"
        echo "# End Claude token optimization" >> "$SHELL_PROFILE"
        echo "✅ Added to $SHELL_PROFILE"
        echo "🔄 Please restart your shell or run: source $SHELL_PROFILE"
    else
        echo "✅ Claude optimization already configured in shell"
    fi
fi

echo ""
echo "🎯 Claude automatic setup complete!"
echo ""
echo "🚀 What's now automatic:"
echo "   ✅ Token-sage loads first"
echo "   ✅ HAL agents preprocess (0 tokens)"
echo "   ✅ Maximum token efficiency"
echo "   ✅ Caching enabled"
echo ""
echo "💰 New commands available:"
echo "   claude-opt 'your goal'          # Optimized analysis"
echo "   token-optimize 'goal' 'pattern' # Advanced with caching"
echo "   hal-preprocess                  # Local filtering only"
echo ""
echo "🎯 Claude will now automatically use token-sage + HAL workflow!"
