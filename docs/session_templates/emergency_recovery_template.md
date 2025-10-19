# Emergency Session Recovery Template

## 🚨 Session Failure Recovery Checklist

### Step 1: Assess Current State
- [ ] Check git status: `git status`
- [ ] Check last commit: `git log -1 --oneline`
- [ ] Check available resume points: `./bin/resume-from list`
- [ ] Check current todo status: `./bin/todo status`

### Step 2: Identify Last Known Good State
**Last Commit:** [git hash and description]
**Last Checkpoint:** [checkpoint ID and description]
**Last Pause Point:** [pause point ID and description]

### Step 3: Recovery Options

#### Option A: Resume from Last Checkpoint/Pause Point
```bash
./bin/resume-from [checkpoint_id or pause_id]
```
- **Advantages:** Full context preservation
- **When to use:** When last savepoint is recent and complete

#### Option B: Git Reset to Last Good Commit
```bash
git reset --hard [commit_hash]
./bin/resume-from [closest_checkpoint_id]
```
- **Advantages:** Clean state
- **When to use:** When current state is corrupted or incomplete

#### Option C: Manual Context Reconstruction
1. Review git log: `git log --oneline -10`
2. Check todo status: `./bin/todo status`
3. Review session summary: `cat SESSION_SUMMARY.md`
4. Create new pause point: `./bin/pause-here "Recovery point" "[next action]"`

### Step 4: Validate Recovery
- [ ] Verify git state is clean: `git status`
- [ ] Confirm todo alignment: `./bin/todo status`
- [ ] Test basic functionality: [run key tests]
- [ ] Document recovery process: [add notes below]

### Step 5: Prevention for Next Session
- [ ] Set more frequent checkpoints (every 10-15 min)
- [ ] Use explicit pause points before risky operations
- [ ] Maintain better session documentation
- [ ] Set session time limits with alerts

## 📝 Recovery Notes

**What Happened:** [Describe the failure/interruption]

**Root Cause:** [What led to the state loss]

**Recovery Method Used:** [Which option was chosen and why]

**Work Lost:** [Estimate of work that needs to be redone]

**Prevention Measures:** [What will be done differently next time]

## 🎯 Resumption Plan

**Immediate Next Steps:**
1. [First action to take]
2. [Second action to take]
3. [Third action to take]

**Phase Step Focus:** [Which phase step to prioritize]

**Time Estimate:** [How long to get back to previous state]

## 🔄 Recovery Verification

- [ ] All systems functioning correctly
- [ ] Phase context properly restored
- [ ] Next actions clearly defined
- [ ] Session management tools working
- [ ] Ready to proceed with confidence

---

*Use this template whenever session recovery is needed to ensure systematic and complete restoration of working state.*