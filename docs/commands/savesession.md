# savesession Command Documentation

> **Command**: `bin/savesession` or `savesession`
> **Purpose**: Save complete session state (conceptual, contextual, functional) with mandatory compaction protocol
> **Universal Access**: ALL humans and AI agents (Claude, GPT, Gemini, Copilot, CodeWhisperer)
> **Session Persistence**: CRITICAL - Command must be remembered across ALL sessions

---

## Overview

The `savesession` command creates a comprehensive snapshot of the current project state across three dimensions:
- **Conceptual**: What requirements and standards exist
- **Contextual**: What the current platform status is
- **Functional**: How the session initialization and enforcement systems work

**CRITICAL REQUIREMENT**: Session state MUST be compacted into SESSION_SUMMARY.md before applying any new changes. This ensures knowledge remains accessible and prevents fragmentation.

---

## Command Usage

### Basic Execution

```bash
# From project root
./bin/savesession

# Or if bin/ is in PATH
savesession
```

### When to Use

**End of Session** (RECOMMENDED):
- Before closing a development session
- After completing major feature work
- When preparing to switch contexts or tasks
- Before pushing commits to remote

**Before Major Changes**:
- Prior to architectural refactoring
- Before implementing breaking changes
- When starting new feature branches

**Periodic Snapshots**:
- Daily during active development
- After significant platform updates
- When platform metrics change (test count, version bump)

### When NOT to Use

- **During active development** - Wait for logical stopping point
- **With uncommitted changes** - Commit or stash first (recommended)
- **Multiple times per day** - One snapshot per day typically sufficient

---

## What savesession Does

### 1. Verification

Checks if session state snapshot already exists for current date:
- **If exists**: Warns about potential overwrite
- **If clean**: Proceeds with snapshot creation

### 2. State Collection

Gathers comprehensive platform information:
- **Git state**: Current branch, commits ahead, working directory status
- **Platform metrics**: Version, test count, code quality status
- **Recent activity**: Last 5 commits for context
- **Compliance status**: ISO 11783, ISO 18497 implementation status

### 3. Snapshot Creation

Creates `docs/monitoring/SESSION_STATE_YYYY_MM_DD.md` with:
- **Compaction reminder**: CRITICAL requirement at top of file
- **Conceptual state**: All 5 MANDATORY requirements for ALL AI agents
- **Contextual state**: Current platform metrics and recent activity
- **Functional state**: 6-phase architecture and enforcement mechanisms
- **Git state**: Branch status and recent commits
- **Next actions**: Compaction protocol and strategic priorities

### 4. Compaction Reminder

Displays prominent reminders about mandatory compaction:
- Why compaction is required
- Steps for proper compaction
- Consequences of skipping compaction

---

## CRITICAL: Compaction Protocol

### Why Compaction is Mandatory

**Knowledge Fragmentation Prevention**:
- Without compaction, session knowledge spreads across multiple dated snapshot files
- Future sessions (human or AI) struggle to find authoritative current state
- SESSION_SUMMARY.md becomes stale and misleading

**Accessibility**:
- SESSION_SUMMARY.md loaded automatically by `loadsession` command
- Snapshot files require manual discovery and reading
- Compacted knowledge immediately available to all agents

**Cross-Session Continuity**:
- Next session inherits clear understanding of current state
- No need to review multiple historical snapshots
- Single source of truth for platform status

### How to Compact

**Step 1: Review Snapshot**
```bash
# Read the created snapshot
cat docs/monitoring/SESSION_STATE_$(date +%Y_%m_%d).md
```

**Step 2: Identify Critical Achievements**
- New features implemented
- Requirements added or changed
- Platform metrics updated
- Strategic priorities shifted

**Step 3: Update SESSION_SUMMARY.md**
```bash
# Edit SESSION_SUMMARY.md
# Add new "Current Session Achievements" section
# Update platform metrics (version, test count)
# Add strategic priorities
```

**Step 4: Archive Old Snapshots**
```bash
# Move old snapshots to archive or remove
mkdir -p docs/monitoring/archive
mv docs/monitoring/SESSION_STATE_2025_09_*.md docs/monitoring/archive/
```

**Step 5: Verify Compaction**
```bash
# Run loadsession to see updated context
./bin/loadsession
```

### Compaction Checklist

- [ ] Reviewed snapshot file completely
- [ ] Identified critical achievements from session
- [ ] Updated SESSION_SUMMARY.md "Current Session Achievements" section
- [ ] Updated platform metrics (version, test count) if changed
- [ ] Updated strategic priorities and next steps
- [ ] Archived or removed old session state snapshots
- [ ] Ran `loadsession` to verify updated context loads correctly
- [ ] Committed SESSION_SUMMARY.md updates with proper commit message

---

## Output Format

### Visual Structure

```
💾 AFS FastAPI Session State Snapshot with Compaction
=====================================================

📋 CRITICAL: Session State Compaction Protocol
================================================
Session state MUST be compacted before applying changes.
This ensures knowledge remains accessible across all sessions.

🔍 Verifying session state compaction...
✅ Proceeding with session state snapshot

📊 Gathering Current Project State...
   • Branch: develop
   • Version: v0.1.3+
   • Tests: 148 tests
   • Commits ahead: 4

📝 Creating Session State Snapshot...
✅ Session state snapshot created
   Location: docs/monitoring/SESSION_STATE_2025_09_30.md

📊 Session State Summary
========================
   Platform: v0.1.3+
   Branch: develop
   Tests: 148 tests
   Status: Snapshot ready for compaction

⚠️  CRITICAL REMINDER: COMPACTION REQUIRED
=========================================
This snapshot captures current state in detail, but MUST be compacted
into SESSION_SUMMARY.md before starting new work.

Compaction ensures:
   • SESSION_SUMMARY.md remains authoritative source of truth
   • Knowledge is accessible to all future sessions
   • Session history doesn't fragment across multiple files
   • New AI agents can quickly understand platform state

Next steps:
   1. Review: docs/monitoring/SESSION_STATE_2025_09_30.md
   2. Compact: Update SESSION_SUMMARY.md with critical achievements
   3. Clean: Archive or remove old session state snapshots
   4. Verify: SESSION_SUMMARY.md reflects current state

💾 Session State Snapshot Complete!
⚠️  Remember to compact before starting new work
```

---

## Files Created/Modified

### Created
- `docs/monitoring/SESSION_STATE_YYYY_MM_DD.md` - Dated snapshot file

### Should Be Modified (During Compaction)
- `docs/monitoring/SESSION_SUMMARY.md` - Update with compacted knowledge
- `CHANGELOG.md` - Document session achievements

### May Be Archived
- Old `SESSION_STATE_*.md` files - Move to archive directory

---

## Integration with Other Commands

### Related Commands

**loadsession** - Loads SESSION_SUMMARY.md context
```bash
./bin/loadsession  # Should be run AFTER compaction
```

**whereweare** - Generates strategic assessment
```bash
./bin/whereweare  # Can be run before savesession for context
```

**updatechangelog** - Regenerates CHANGELOG.md
```bash
./updatechangelog  # Often run alongside savesession
```

### Typical Workflow

```bash
# 1. Complete session work
git add -A
git commit -m "feat(feature): description"

# 2. Save session state
./bin/savesession

# 3. Review snapshot
cat docs/monitoring/SESSION_STATE_$(date +%Y_%m_%d).md

# 4. Compact into SESSION_SUMMARY.md
# (Edit SESSION_SUMMARY.md manually)

# 5. Update CHANGELOG
./updatechangelog

# 6. Commit compacted state
git add docs/monitoring/SESSION_SUMMARY.md CHANGELOG.md
git commit -m "docs(monitoring): Compact session state into SESSION_SUMMARY"

# 7. Verify with loadsession
./bin/loadsession
```

---

## Rationale: Why savesession Command Exists

### Problem Statement

**Before savesession**:
- Session state captured inconsistently (if at all)
- Knowledge scattered across git commits, files, and memory
- No standard process for session completion
- Future sessions lost context of what was accomplished
- AI agents couldn't easily understand platform evolution

### Solution

**With savesession**:
- **Standardized process**: Every session can end the same way
- **Complete capture**: Conceptual, contextual, functional state preserved
- **Compaction protocol**: Ensures knowledge consolidation prevents fragmentation
- **Universal access**: All humans and AI agents use same command
- **Cross-session memory**: Platform evolution traceable and accessible

### Agricultural Robotics Justification

**Safety-Critical Requirements**:
- ISO 18497/11783 compliance auditing requires documented platform state
- Equipment operators need confidence platform evolution is traceable
- Multi-tractor coordination systems demand clear state documentation

**Universal AI Agent Context**:
- All AI assistants (Claude, GPT, Gemini, Copilot) need consistent state access
- Prevents quality degradation when switching between AI tools
- Ensures all agents understand current mandatory requirements

**Knowledge Continuity**:
- Session state snapshots enable smooth transitions between development sessions
- New contributors can quickly understand platform status
- Educational value preserved alongside functional capabilities

---

## Advanced Usage

### Scripting with savesession

```bash
# End-of-day automation
#!/bin/bash
echo "End of day development session..."
git status
./bin/savesession
echo "Session state saved. Remember to compact tomorrow!"
```

### Pre-Push Hook Integration

```bash
# .git/hooks/pre-push
#!/bin/bash
# Remind about session state before pushing
echo "⚠️  Reminder: Have you run 'savesession' today?"
read -p "Continue push? (y/N): " -n 1 -r
echo
[[ $REPLY =~ ^[Yy]$ ]]
```

### CI/CD Integration

```yaml
# .github/workflows/session-check.yml
# Verify SESSION_SUMMARY.md is kept current
- name: Check session summary freshness
  run: |
    LAST_MODIFIED=$(stat -f "%Sm" -t "%s" docs/monitoring/SESSION_SUMMARY.md)
    AGE_DAYS=$(( ($(date +%s) - $LAST_MODIFIED) / 86400 ))
    if [ $AGE_DAYS -gt 7 ]; then
      echo "⚠️  SESSION_SUMMARY.md hasn't been updated in $AGE_DAYS days"
      echo "Consider running savesession and compacting"
    fi
```

---

## Troubleshooting

### "Session state file already exists"

**Cause**: Snapshot already created for current date
**Solution**: Either overwrite (type 'y') or cancel and review existing snapshot

### "Permission denied"

**Cause**: Script not executable
**Solution**:
```bash
chmod +x bin/savesession
```

### "PROJECT_ROOT not found"

**Cause**: Running from wrong directory
**Solution**: Run from project root or use `./bin/savesession`

### "Git command failed"

**Cause**: Not in a git repository or git not installed
**Solution**: Ensure you're in AFS FastAPI project directory

---

## Cross-Session Persistence

### How Command is Remembered

**Documentation References**:
- [CLAUDE.md](../../CLAUDE.md) - Listed in command integration section
- [AGENTS.md](../../AGENTS.md) - Referenced in how to use section
- [SESSION_SUMMARY.md](../monitoring/SESSION_SUMMARY.md) - Mentioned in workflow protocols
- This file - Complete specification and rationale

**Automatic Loading**:
- `bin/loadsession` displays reminder about savesession at end of session
- SESSION_SUMMARY.md includes session completion protocol
- .claude/commands/ directory indexed for command discovery

**Universal Agent Access**:
- All AI agents (Claude, GPT, Gemini, Copilot, CodeWhisperer) can execute
- Command documented in multiple locations for discoverability
- Rationale explained for why command exists and must be remembered

---

## Maintenance

### Updating savesession Script

**When to update**:
- Platform version detection changes
- New metrics to capture
- Additional state dimensions needed
- Output format improvements

**How to update**:
1. Edit `bin/savesession` script
2. Test with `./bin/savesession` in clean state
3. Update this documentation (docs/commands/savesession.md)
4. Update references in CLAUDE.md, AGENTS.md
5. Commit with `feat(commands): enhance savesession` or similar

### Versioning

- Command versioning implicit via git history
- Breaking changes should be documented in CHANGELOG.md
- Backward compatibility preferred for cross-session stability

---

**Command Status**: ✅ OPERATIONAL - Available for all humans and AI agents
**Cross-Session Memory**: ✅ DOCUMENTED - References in CLAUDE.md, AGENTS.md, SESSION_SUMMARY.md
**Compaction Protocol**: ⚠️  MANDATORY - Must compact before new work
**Universal Access**: ✅ ALL AI AGENTS - Claude, GPT, Gemini, Copilot, CodeWhisperer