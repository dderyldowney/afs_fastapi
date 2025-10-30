# Token Optimization Installation Guide

**Complete guide to add token-sage + HAL optimization to any repository**

## 🎯 Overview

This guide shows how to add the complete token optimization system to any repository in 5 minutes or less.

## 📋 Prerequisites

- Python 3.8+ installed
- Bash shell (zsh, bash, etc.)
- Claude Code access
- Git repository (optional but recommended)

## 🚀 Installation Steps

### **Step 1: Get the Package**

#### **Option A: Download the Package**
```bash
# Download the package files
curl -L https://github.com/your-repo/token_optimization_package/archive/main.zip -o token_opt.zip
unzip token_opt.zip
cd token_optimization_package-main
```

#### **Option B: Copy Files Manually**
```bash
# Create a directory in your repository
mkdir token-optimization
cd token-optimization

# Copy the files from the source repository
# (You would copy these files from the ToDoWrite repository)
```

### **Step 2: Run One-Click Setup**
```bash
# Make the setup script executable
chmod +x claude_auto_setup.sh

# Run automatic setup
./claude_auto_setup.sh
```

### **Step 3: Update Shell Environment**
```bash
# Restart your terminal OR run:
source ~/.zshrc  # for zsh
# OR
source ~/.bashrc  # for bash
```

### **Step 4: Verify Installation**
```bash
# Check environment variables
echo $CLAUDE_DEFAULT_AGENT
# Should output: token-sage

# Test the system
python always_token_sage.py "test query"

# Check Claude configuration
cat ~/.claude/config.json
```

## 🔧 What Gets Installed

### **Environment Variables:**
```bash
CLAUDE_DEFAULT_AGENT=token-sage
CLAUDE_TOKEN_OPTIMIZATION=enabled
CLAUDE_HAL_AGENTS=enabled
TOKEN_OPTIMIZED_PATH=/path/to/your/repo
```

### **Shell Aliases:**
```bash
claude-opt      # Optimized analysis
token-optimize  # Advanced with caching
hal-preprocess  # Local filtering only
```

### **Configuration Files:**
- `~/.claude/config.json` - Claude configuration
- `~/.claude/session_state.json` - Session tracking
- `~/.claude/hooks/` - Automatic hooks
- `~/.claude/startup.sh` - Auto-initialization

## 💡 Usage After Installation

### **Automatic Usage (Recommended):**
Just ask Claude normally - it will automatically use token optimization!

```bash
# Claude automatically detects and optimizes:
User: "Analyze the authentication system"
# → HAL preprocessing (0 tokens) + token-sage analysis

User: "Find all database models"
# → Local filtering + optimized analysis

User: "Review the API endpoints"
# → Maximum token efficiency automatically
```

### **Manual Commands (Optional):**
```bash
# Main optimized analysis
claude-opt "analyze database models"

# Advanced with caching
token-optimize "authentication" "class.*Auth"

# Local preprocessing only
hal-preprocess

# Direct script usage
python always_token_sage.py "your goal"
python token_optimized_agent.py "goal" "pattern"
```

## 🔍 Verification Checklist

Run these commands to verify everything is working:

### **1. Environment Check**
```bash
echo $CLAUDE_DEFAULT_AGENT
# Expected: token-sage

echo $CLAUDE_TOKEN_OPTIMIZATION
# Expected: enabled
```

### **2. File Check**
```bash
ls -la always_token_sage.py
# Should exist and be executable

python always_token_sage.py "test query"
# Should run without errors
```

### **3. Claude Configuration Check**
```bash
cat ~/.claude/config.json
# Should show token optimization settings

cat ~/.claude/session_state.json
# Should show HAL agents ready
```

### **4. Functionality Test**
```bash
# Test basic functionality
python always_token_sage.py "find main function"

# Test with caching
python token_optimized_agent.py "database" "class.*Model"
# Run again to test caching
python token_optimized_agent.py "database" "class.*Model"
# Second run should be instant (from cache)
```

## 🎯 Expected Results

### **Successful Installation Indicators:**
- ✅ Environment variables set correctly
- ✅ Shell aliases work (`claude-opt`, `token-optimize`, `hal-preprocess`)
- ✅ Scripts execute without errors
- ✅ Claude configuration created
- ✅ HAL agents detect local files
- ✅ Token-sage initialization works

### **Token Efficiency Test:**
```bash
# Test with a real codebase
python always_token_sage.py "analyze authentication system"

# Expected output:
# ✅ HAL preprocessing complete: 623 chars (0 tokens)
# 🧠 Token-sage analysis with 623 chars of context
# 💰 Token savings: Local preprocessing used 0 API tokens
```

## 🔧 Customization Options

### **Adjust Token Limits:**
Edit `.token_optimized_config.yaml`:
```yaml
optimization:
  max_context_chars: 1500  # Increase for more context
  max_files: 100           # Increase for broader analysis
  max_bytes: 50000         # Increase for larger files
```

### **Change File Patterns:**
Edit the scripts to include different file types:
```python
include_globs = ['*.py', '*.js', '*.ts', '*.java', '*.cpp']
```

### **Modify Detection Logic:**
Add new keywords to `.claude_auto_init.py`:
```python
code_indicators = [
    "analyze", "find", "search", "class", "def",
    "component", "service", "module", "interface"  # Add your keywords
]
```

## 🚨 Troubleshooting

### **Common Issues:**

#### **1. Permission Denied**
```bash
chmod +x *.py *.sh
```

#### **2. Python Not Found**
```bash
# Check Python installation
python3 --version
# Use python3 instead of python if needed
```

#### **3. Environment Variables Not Set**
```bash
# Manual setup
export CLAUDE_DEFAULT_AGENT="token-sage"
export CLAUDE_TOKEN_OPTIMIZATION="enabled"

# Add to shell profile
echo 'export CLAUDE_DEFAULT_AGENT="token-sage"' >> ~/.zshrc
source ~/.zshrc
```

#### **4. HAL Agents Not Working**
```bash
# Test dependencies
python -c "import subprocess; print('subprocess OK')"
python -c "import json; print('json OK')"

# Check file paths
ls -la hal_token_savvy_agent.py hal_agent_loop.py
```

#### **5. Claude Configuration Issues**
```bash
# Reset Claude configuration
rm -rf ~/.claude
./claude_auto_setup.sh
```

## 📊 Performance Monitoring

### **Track Token Savings:**
```bash
# Monitor cache usage
ls -la ~/.token_optimized_cache/

# Check session statistics
cat ~/.claude/session_state.json

# Test performance time
time python always_token_sage.py "analyze system"
```

### **Expected Performance:**
- **First query:** 2-5 seconds (HAL preprocessing + token-sage)
- **Cached query:** <1 second (instant from cache)
- **Token savings:** 80-95% per analysis

## 🎉 Success!

If all verification steps pass, you now have:
- ✅ Automatic token-sage loading
- ✅ HAL agent preprocessing (0 API tokens)
- ✅ 90% average token savings
- ✅ One-click analysis commands
- ✅ Intelligent caching system
- ✅ Universal repository compatibility

**Your repository now has maximum token efficiency!** 🚀

## 📞 Getting Help

If you encounter issues:
1. Check this guide first
2. Run `python .claude_auto_init.py` for diagnostics
3. Verify all files are executable
4. Test with a simple query first

The system is designed to be robust and should work in most environments with minimal configuration.
