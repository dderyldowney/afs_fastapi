# Phase Work Session Template

## 🚀 Session Start Checklist

- [ ] Resume from last point: `./bin/resume-from list` → `./bin/resume-from <id>`
- [ ] Review session strategy: [SESSION_MANAGEMENT_STRATEGY.md](../SESSION_MANAGEMENT_STRATEGY.md)
- [ ] Identify work unit (< 30 min target)

## 📋 Current Work Unit

**Target:** [Describe what will be accomplished]
**Estimated Time:** [< 30 minutes]

## 🔄 Progress Checkpoints

### Checkpoint 1: [Description]
- **Task:** [What was completed]
- **Command:** `./bin/checkpoint "[description]"`
- **Status:** [ ] Complete

### Checkpoint 2: [Description]
- **Task:** [What was completed]
- **Command:** `./bin/checkpoint "[description]"`
- **Status:** [ ] Complete

### Checkpoint 3: [Description]
- **Task:** [What was completed]
- **Command:** `./bin/checkpoint "[description]"`
- **Status:** [ ] Complete

## 🚦 Natural Breakpoints

- [ ] After file creation: `./bin/checkpoint "Created [filename]"`
- [ ] After test completion: `./bin/checkpoint "Completed [test suite]"`
- [ ] After error fixes: `./bin/checkpoint "Fixed [error category]"`
- [ ] Before major refactoring: `./bin/pause-here "Natural breakpoint" "[next action]"`

## 🛑 Session End Protocol

### Planned Completion
```bash
./bin/checkpoint "Completed [work unit description]"
./bin/savesession "End of session - [summary]"
```

### Forced Interruption
```bash
./bin/pause-here "[reason]" "[next action]"
./bin/savesession "Session interrupted - ready for continuation"
```

## 📝 Notes

- [Add any important notes or decisions made during session]
- [Document any architectural choices or reasoning]
- [Note any issues encountered and solutions]

## ➡️ Next Session

**Priority:** [What should be tackled next]
**Context:** [Any important context for next session]
**Resume Point:** [Latest checkpoint/pause point ID]