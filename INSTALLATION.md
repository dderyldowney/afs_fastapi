# Claude Subagents Installation Guide

**Step-by-step installation instructions for Claude subagents package**

## 📋 Prerequisites

### **System Requirements:**
- Python 3.8 or higher
- Claude Code installed and accessible
- Git repository (recommended)
- Write permissions to repository and home directory
- Compatible shell (zsh, bash, fish)

### **Environment Check:**
```bash
# Verify Python
python --version
# Expected: Python 3.8.x or higher

# Verify Claude Code
claude --version
# Expected: Claude Code version information

# Verify Git
git --version
# Expected: Git version information
```

## 🚀 Installation Methods

### **Method 1: One-Click Installation (Recommended)**

#### **Step 1: Copy Package**
```bash
# Copy package to your repository
cp -r CLAUDE_SUBAGENTS_PACKAGE/* /path/to/your-repo/

# Navigate to your repository
cd /path/to/your-repo
```

#### **Step 2: Run Setup**
```bash
# Make setup script executable
chmod +x claude_auto_setup.sh

# Run automatic setup
./claude_auto_setup.sh
```

#### **Step 3: Restart Shell**
```bash
# Restart your terminal or source shell profile
source ~/.zshrc  # or ~/.bashrc
```

#### **Step 4: Verify Installation**
```bash
# Test basic functionality
python always_token_sage.py "test query"

# Check environment variables
echo $CLAUDE_DEFAULT_AGENT
# Expected: token-sage
```

### **Method 2: Manual Installation**

#### **Step 1: Copy Files**
```bash
# Copy all package files to repository root
cp CLAUDE_SUBAGENTS_PACKAGE/* /path/to/your-repo/

# Navigate to repository
cd /path/to/your-repo
```

#### **Step 2: Set Permissions**
```bash
# Make Python scripts executable
chmod +x always_token_sage.py
chmod +x token_optimized_agent.py
chmod +x auto_agent.py
chmod +x CLAUDE_WORKFLOW.py
chmod +x .claude_init.py
chmod +x .claude_auto_init.py

# Make setup script executable
chmod +x claude_auto_setup.sh

# Make HAL agents executable
chmod +x hal_agent_loop.py
chmod +x hal_token_savvy_agent.py
```

#### **Step 3: Initialize Claude Environment**
```bash
# Run Claude initialization
python .claude_init.py

# Set up automatic initialization
python .claude_auto_init.py
```

#### **Step 4: Configure Environment**
```bash
# Add to shell profile (~/.zshrc or ~/.bashrc)
export CLAUDE_DEFAULT_AGENT="token-sage"
export CLAUDE_TOKEN_OPTIMIZATION="enabled"
export CLAUDE_HAL_AGENTS="hal_agent_loop.py,hal_token_savvy_agent.py"
export TOKEN_OPTIMIZED_PATH="$(pwd)"

# Create aliases
alias claude-opt='python always_token_sage.py'
alias token-optimize='python token_optimized_agent.py'
alias hal-preprocess='python hal_agent_loop.py'

# Reload shell
source ~/.zshrc  # or ~/.bashrc
```

#### **Step 5: Create Claude Configuration**
```bash
# Create Claude config directory
mkdir -p ~/.claude

# Create config file
cat > ~/.claude/config.json << 'EOF'
{
  "default_agent": "token-sage",
  "auto_optimization": true,
  "hal_agents": ["hal_agent_loop.py", "hal_token_savvy_agent.py"],
  "workflow": "CLAUDE_WORKFLOW.py"
}
EOF

# Create session state
cat > ~/.claude/session_state.json << 'EOF'
{
  "hal_agents_ready": true,
  "token_sage_loaded": true,
  "auto_init_complete": true,
  "last_activity": "$(date -Iseconds)"
}
EOF
```

## ✅ Verification Steps

### **Basic Functionality Tests:**

#### **1. Test Token-Sage Integration:**
```bash
python always_token_sage.py "test query"
# Expected: Success message with context analysis
```

#### **2. Test HAL Agents:**
```bash
python hal_agent_loop.py --help
# Expected: Help message with HAL agent options

python hal_token_savvy_agent.py --help
# Expected: Help message for token-savvy agent
```

#### **3. Test Advanced Agent:**
```bash
python token_optimized_agent.py "test" "pattern"
# Expected: Processing with caching information
```

#### **4. Test Auto-Init:**
```bash
python .claude_auto_init.py
# Expected: Session initialization success
```

### **Environment Verification:**

#### **1. Check Environment Variables:**
```bash
echo "CLAUDE_DEFAULT_AGENT: $CLAUDE_DEFAULT_AGENT"
echo "CLAUDE_TOKEN_OPTIMIZATION: $CLAUDE_TOKEN_OPTIMIZATION"
echo "CLAUDE_HAL_AGENTS: $CLAUDE_HAL_AGENTS"
echo "TOKEN_OPTIMIZED_PATH: $TOKEN_OPTIMIZED_PATH"
```

#### **2. Check Claude Configuration:**
```bash
cat ~/.claude/config.json
# Expected: JSON configuration with token-sage as default

cat ~/.claude/session_state.json
# Expected: Session state with agents ready
```

#### **3. Test Shell Aliases:**
```bash
alias claude-opt
alias token-optimize
alias hal-preprocess
# Expected: Aliases defined and pointing to correct scripts
```

## 🔧 Configuration Options

### **Customizing Environment Variables:**
```bash
# Change default agent (if needed)
export CLAUDE_DEFAULT_AGENT="custom-agent"

# Adjust HAL agent paths
export CLAUDE_HAL_AGENTS="/custom/path/hal1.py,/custom/path/hal2.py"

# Enable/disable features
export CLAUDE_TOKEN_OPTIMIZATION="enabled"  # or "disabled"
export CLAUDE_CACHING="enabled"             # or "disabled"
```

### **Custom Configuration File:**
```bash
# Edit configuration for specific needs
nano ~/.claude/config.json
```

Example custom configuration:
```json
{
  "default_agent": "token-sage",
  "auto_optimization": true,
  "hal_agents": ["hal_agent_loop.py", "hal_token_savvy_agent.py"],
  "workflow": "CLAUDE_WORKFLOW.py",
  "custom_settings": {
    "max_file_size": "5MB",
    "cache_duration": 3600,
    "debug_mode": false
  }
}
```

## 🚨 Troubleshooting

### **Common Installation Issues:**

#### **Permission Denied Errors:**
```bash
# Fix script permissions
chmod +x *.py *.sh
```

#### **Python Not Found:**
```bash
# Try python3 instead
python3 --version
python3 .claude_init.py

# Or update PATH
export PATH="/usr/local/bin:$PATH"
```

#### **Environment Variables Not Set:**
```bash
# Manually set variables
export CLAUDE_DEFAULT_AGENT="token-sage"
export CLAUDE_TOKEN_OPTIMIZATION="enabled"

# Restart shell
source ~/.zshrc
```

#### **Claude Configuration Not Created:**
```bash
# Create config directory manually
mkdir -p ~/.claude

# Run initialization manually
python .claude_init.py
python .claude_auto_init.py
```

### **HAL Agent Issues:**

#### **HAL Agents Not Finding Files:**
```bash
# Check repository has code files
find . -name "*.py" -o -name "*.js" -o -name "*.ts" | head -5

# Test HAL agent directly
python hal_agent_loop.py --query "test" --max-results 5
```

#### **Import Errors:**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Install missing dependencies if needed
pip install -r requirements.txt  # if available
```

### **Token-Sage Issues:**

#### **Token-Sage Not Loading:**
```bash
# Check Claude Code installation
claude --version

# Verify environment
echo $CLAUDE_DEFAULT_AGENT

# Test token-sage directly
python always_token_sage.py "test"
```

## 📊 Performance Validation

### **Token Efficiency Test:**
```bash
# Test with actual code analysis
time python always_token_sage.py "analyze main codebase"

# Expected results:
# - Completion time: <10 seconds
# - Memory usage: <100MB
# - Successful context analysis
```

### **Caching Performance Test:**
```bash
# First run (should process)
time python token_optimized_agent.py "database models" "class.*Model"

# Second run (should be instant)
time python token_optimized_agent.py "database models" "class.*Model"

# Expected: Second run significantly faster
```

## 🎯 Success Criteria

### **Installation Success Indicators:**
- ✅ All scripts execute without permission errors
- ✅ Environment variables are correctly set
- ✅ Claude configuration files created
- ✅ HAL agents can find and process local files
- ✅ Token-sage integration works correctly
- ✅ Shell aliases function properly
- ✅ Session initialization completes successfully

### **Functional Success Indicators:**
- ✅ Token optimization achieved (80-95% savings)
- ✅ Queries process in reasonable time (<10 seconds)
- ✅ Caching reduces repeat query time
- ✅ No manual intervention required for normal operation
- ✅ System works with different codebase types
- ✅ Error handling works gracefully

## 🔄 Maintenance

### **Regular Maintenance Tasks:**
```bash
# Clear cache if it grows too large
rm -rf ~/.token_optimized_cache/*

# Update configuration as needed
nano ~/.claude/config.json

# Monitor performance
time python always_token_sage.py "performance test"

# Backup configuration
cp -r ~/.claude ~/.claude.backup.$(date +%Y%m%d)
```

### **Updates and Upgrades:**
```bash
# Re-run setup to update configuration
./claude_auto_setup.sh

# Check for newer versions
git pull  # if using git repository

# Re-initialize after updates
python .claude_auto_init.py
```

## 📞 Getting Help

### **Self-Service Troubleshooting:**
1. Check this installation guide
2. Run `python .claude_auto_init.py` for diagnostics
3. Test with simple queries first
4. Verify all prerequisites are met

### **Documentation References:**
- **CLAUDE_AUTO_GUIDE.md** - Complete usage documentation
- **README.md** - Package overview and quick start
- **Individual script help** - `python script.py --help`

---

**Installation should take less than 5 minutes. If you encounter issues, follow the troubleshooting steps above.** 🚀

---

*For additional support, refer to the complete documentation in the package.*