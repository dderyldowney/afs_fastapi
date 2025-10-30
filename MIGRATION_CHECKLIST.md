# Token Optimization Migration Checklist

**Checklist for adding token optimization to a new repository**

## 📋 Pre-Migration Checklist

### **Repository Requirements:**
- [ ] Repository is accessible locally
- [ ] Python 3.8+ is installed
- [ ] Git is initialized (recommended)
- [ ] Claude Code is available
- [ ] Write permissions to repository directory

### **Environment Check:**
- [ ] Shell is zsh, bash, or compatible
- [ ] Environment variables can be set
- [ ] Scripts can be made executable
- [ ] Home directory (~) is writable

## 🚀 Migration Steps

### **Step 1: Package Acquisition**
- [ ] Download or copy the token_optimization_package
- [ ] Extract files to repository root
- [ ] Verify all files are present
- [ ] Check file integrity (no corruption)

**Files to verify:**
- [ ] `always_token_sage.py`
- [ ] `token_optimized_agent.py`
- [ ] `auto_agent.py`
- [ ] `claude_auto_setup.sh`
- [ ] `.claude_init.py`
- [ ] `.claude_auto_init.py`
- [ ] `CLAUDE_WORKFLOW.py`
- [ ] `.token_optimized_config.yaml`
- [ ] `CLAUDE_AUTO_GUIDE.md`
- [ ] `INSTALLATION_GUIDE.md`

### **Step 2: Setup Execution**
- [ ] Make setup script executable: `chmod +x claude_auto_setup.sh`
- [ ] Run automatic setup: `./claude_auto_setup.sh`
- [ ] Check for successful completion messages
- [ ] Verify no error messages occurred

### **Step 3: Shell Integration**
- [ ] Restart terminal or source shell profile
- [ ] Verify environment variables are set
- [ ] Test shell aliases work
- [ ] Check PATH includes necessary directories

### **Step 4: Verification Testing**
- [ ] Test basic functionality: `python always_token_sage.py "test"`
- [ ] Test Claude integration: Check environment variables
- [ ] Test caching: Run same command twice
- [ ] Test HAL agents: Verify local preprocessing works

## ✅ Post-Migration Verification

### **Environment Verification:**
```bash
# Run these commands and verify expected output
echo $CLAUDE_DEFAULT_AGENT
# Expected: token-sage

echo $CLAUDE_TOKEN_OPTIMIZATION
# Expected: enabled

echo $TOKEN_OPTIMIZED_PATH
# Expected: /path/to/your/repository
```

### **File Verification:**
```bash
# Check these files exist and are executable
ls -la always_token_sage.py          # Should be executable
ls -la token_optimized_agent.py     # Should be executable
ls -la ~/.claude/config.json        # Should exist
ls -la ~/.claude/session_state.json # Should exist
```

### **Functionality Verification:**
```bash
# Test basic functionality
python always_token_sage.py "find main function"
# Expected: Success message with context

# Test caching
python token_optimized_agent.py "test" "pattern"
python token_optimized_agent.py "test" "pattern"
# Expected: Second run should be instant (cached)

# Test shell aliases
claude-opt "test query"
# Expected: Should work without errors
```

### **Claude Integration Verification:**
```bash
# Check Claude configuration
cat ~/.claude/config.json
# Expected: Shows token-sage as default agent

# Check session state
cat ~/.claude/session_state.json
# Expected: Shows HAL agents ready
```

## 🎯 Success Criteria

### **Must Pass:**
- [ ] Environment variables are correctly set
- [ ] All scripts execute without errors
- [ ] HAL preprocessing works (finds local files)
- [ ] Token-sage integration is functional
- [ ] Shell aliases work correctly
- [ ] Caching system operates properly

### **Should Pass:**
- [ ] Installation completed without manual intervention
- [ ] All files are in correct locations
- [ ] Configuration files are properly formatted
- [ ] Error handling works gracefully
- [ ] Performance meets expectations (90% token savings)

### **Optional:**
- [ ] Customization applied (if needed)
- [ ] Additional file patterns configured
- [ ] Custom detection logic added
- [ ] Performance monitoring setup

## 🔧 Common Issues & Solutions

### **Permission Issues:**
- **Problem:** `Permission denied` errors
- **Solution:** `chmod +x *.py *.sh`

### **Environment Variables:**
- **Problem:** Variables not set after setup
- **Solution:** Restart shell or run `source ~/.zshrc`

### **Python Path Issues:**
- **Problem:** Python not found
- **Solution:** Use `python3` instead of `python`

### **Claude Configuration:**
- **Problem:** Configuration files not created
- **Solution:** Run `python .claude_init.py` manually

### **HAL Agent Issues:**
- **Problem:** Local preprocessing fails
- **Solution:** Check repository has code files to analyze

## 📊 Performance Validation

### **Token Efficiency Test:**
```bash
# Test with a substantial codebase
time python always_token_sage.py "analyze entire codebase"

# Expected results:
# - Completion time: <10 seconds
# - Token usage: <2000 characters
# - Context found: Local files identified
```

### **Caching Performance Test:**
```bash
# First run (should process)
time python token_optimized_agent.py "database models" "class.*Model"

# Second run (should be instant)
time python token_optimized_agent.py "database models" "class.*Model"

# Expected: Second run significantly faster (cached)
```

### **Memory Usage Test:**
```bash
# Monitor memory during operation
python always_token_sage.py "large scale analysis" &
PID=$!
ps aux | grep $PID
wait $PID

# Expected: Reasonable memory usage (<100MB for typical analysis)
```

## 🚨 Rollback Plan

If migration fails, rollback steps:

### **Quick Rollback:**
```bash
# Remove environment variables
unset CLAUDE_DEFAULT_AGENT
unset CLAUDE_TOKEN_OPTIMIZATION
unset CLAUDE_HAL_AGENTS
unset TOKEN_OPTIMIZED_PATH

# Remove Claude configuration
rm -rf ~/.claude/config.json
rm -rf ~/.claude/session_state.json

# Remove shell aliases from profile
# Edit ~/.zshrc or ~/.bashrc to remove added lines
```

### **Complete Rollback:**
```bash
# Remove all optimization files
rm -f always_token_sage.py
rm -f token_optimized_agent.py
rm -f auto_agent.py
rm -f claude_auto_setup.sh
rm -f .claude_init.py
rm -f .claude_auto_init.py
rm -f CLAUDE_WORKFLOW.py
rm -f .token_optimized_config.yaml

# Remove cache directory
rm -rf ~/.token_optimized_cache
rm -rf ~/.claude/hooks

# Restart shell
source ~/.zshrc  # or ~/.bashrc
```

## ✅ Migration Complete!

### **Final Checklist:**
- [ ] All files installed correctly
- [ ] Environment configured properly
- [ ] Functionality verified working
- [ ] Performance meets expectations
- [ ] Documentation reviewed
- [ ] Team trained on new workflow
- [ ] Rollback plan documented (if needed)

### **Next Steps:**
- [ ] Train team on new `claude-opt` command
- [ ] Document repository-specific usage patterns
- [ ] Monitor token usage and savings
- [ ] Consider customization based on feedback
- [ ] Schedule regular maintenance checks

---

**🎉 Congratulations! Your repository now has automatic token optimization with 90% average savings!**
