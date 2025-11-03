# Agent Enforcement System - Setup Instructions

## 🚀 Quick Setup (3 Simple Steps)

### Step 1: Extract Files
Extract this zip package to your Python project's root directory.

### Step 2: Run Quick Setup
```bash
python QUICK_DEPLOY.py
```

### Step 3: Commit to Repository
```bash
git add .
git commit -m "feat: add agent enforcement system with KIS directives"
```

## ✅ That's It!

Your project now has **non-bypassable** agent enforcement that automatically:
- Enforces Keep It Simple (KIS) principles
- Ensures PEP compliance (ALL PEPs)
- Mandates CLI tool usage before file operations
- Requires TDD Red-Green-Refactor methodology
- Enforces zero artifact cleanup in tests

## 📁 Files Added to Your Project

- `KIS_DIRECTIVE.md` - Master directive document
- `__agent_enforcer__.py` - Critical enforcement system
- `sitecustomize.py` - Auto-loads in ALL Python sessions
- `agent_config.py` - Centralized configuration
- `.agent_config.py` - Hidden config file
- `setup_agent.py` - Advanced testing script
- `QUICK_DEPLOY.py` - Simple setup verification

## 🧪 Verification

After setup, you can verify the system is active:

```bash
# Quick verification
python QUICK_DEPLOY.py

# Advanced verification
python setup_agent.py

# Test Python session (should show compliance message)
python -c "print('Test')"
```

## 🔧 What Happens Behind the Scenes

1. **Automatic Loading**: `sitecustomize.py` loads automatically in every Python session
2. **Compliance Enforcement**: All agents immediately load KIS directives
3. **Bypass Prevention**: Multiple layers prevent ignoring requirements
4. **Future-Proof**: All future agent sessions will be bound by these rules

## 📚 Documentation

- `AGENT_ENFORCEMENT_SYSTEM.md` - Complete technical documentation
- `PROJECT_INTEGRATION_GUIDE.md` - Detailed integration guide
- `KIS_DIRECTIVE.md` - The actual agent requirements

## ⚠️ Important Notes

- This system is **designed to be non-bypassable**
- All agents working on the project will be automatically bound by these requirements
- The enforcement activates in every Python session without intervention
- Requirements apply to current and all future agent interactions

## 🆘 Need Help?

If you encounter issues:
1. Run `python QUICK_DEPLOY.py` to verify installation
2. Check that all files are in your project's root directory
3. Ensure Python can access the project directory

---

**Result**: Your project now has guaranteed agent compliance with KIS principles, PEP standards, TDD methodology, and zero-artifact cleanup.