# 📋 Session Management Strategy for Agricultural Robotics Development

## 🎯 Overview

This document defines the comprehensive session management strategy for the AFS FastAPI agricultural robotics platform. It addresses the critical need for frequent savepoints during long-running phase work to handle session limits, token limits, and autocompaction limits.

## 🛠️ Core Tools

### 📍 Checkpoint Management Scripts

#### `./bin/checkpoint "description"`
**Purpose:** Create atomic savepoints with git commit and session documentation
**When to use:** After completing meaningful work units
**Example:** `./bin/checkpoint "Completed message prioritization framework"`

**What it does:**
- Stages all changes with `git add -A`
- Creates descriptive commit with timestamp
- Saves checkpoint metadata to `.claude/checkpoints.json`
- Updates session summary
- Provides resume instructions

#### `./bin/pause-here "reason" ["next_action"]`
**Purpose:** Create documented pause points with full context preservation
**When to use:** At session limits or natural breakpoints
**Example:** `./bin/pause-here "Session limit approaching" "Continue with network congestion detection"`

**What it does:**
- Stages current work (even incomplete)
- Creates WIP commit if changes exist
- Saves detailed pause context
- Records next action for seamless resumption
- Creates detailed context file in `.claude/pause_context_[id].md`

#### `./bin/resume-from <point_id>`
**Purpose:** Resume work from specific checkpoints or pause points
**When to use:** Starting new session or continuing after interruption
**Example:** `./bin/resume-from pause_3`

**What it does:**
- Displays saved context and next actions
- Shows git status and commit alignment
- Provides current phase status
- Guides resumption process

## 🚦 Session Management Workflow

### 🔄 **Standard Phase Work Cycle**

1. **Start Session**
   ```bash
   ./bin/resume-from list  # See available resume points
   ./bin/resume-from <last_point>  # Resume from last work
   ```

2. **Begin Work Unit**
   - Choose atomic work unit (single file, test suite, feature component)
   - Estimate completion time (aim for < 30 minutes per unit)

3. **Work with Savepoints**
   ```bash
   # After creating new file
   ./bin/checkpoint "Created message_prioritization.py structure"

   # After writing tests
   ./bin/checkpoint "Added test suite for message priority levels"

   # After fixing compilation errors
   ./bin/checkpoint "Fixed type annotations and imports"
   ```

4. **Natural Breakpoints**
   ```bash
   # Before major refactoring
   ./bin/pause-here "Natural breakpoint" "Begin QoS level implementation"

   # When approaching session limits
   ./bin/pause-here "Session limit approaching" "Continue with adaptive throttling"
   ```

### 🚧 **Critical Control Points**

**ALWAYS STOP AND ASK** at these points:
- ✋ After completing file creation but before implementation
- ✋ After writing tests but before running them
- ✋ After fixing one category of errors but before the next
- ✋ After completing one phase step before starting the next
- ✋ When approaching 15-20 exchanges in conversation
- ✋ Before major architectural changes

## 📊 Phase Work Strategy

### 🎯 **Phase Step Breakdown**

Each phase step should be broken into these atomic units:

1. **Planning & Design** (checkpoint after)
   - Architecture decisions
   - Interface definitions
   - Test strategy

2. **Test Creation** (checkpoint after)
   - Unit tests
   - Integration tests
   - Test data setup

3. **Implementation** (checkpoint after each file)
   - Core functionality
   - Type annotations
   - Documentation

4. **Integration** (checkpoint after)
   - Module integration
   - Error handling
   - Performance optimization

5. **Validation** (checkpoint after)
   - Test execution
   - Code review
   - Documentation update

### 📍 **Checkpoint Frequency Guidelines**

- **Every 15-20 minutes** of focused work
- **After each new file creation**
- **After each test suite completion**
- **Before and after error fixing sessions**
- **After each phase step completion**
- **When changing focus areas**

## 🔄 **Session Handoff Protocol**

### 📤 **Ending Session (Human)**
```bash
# Option 1: Natural completion
./bin/checkpoint "Completed network congestion detection implementation"

# Option 2: Forced pause
./bin/pause-here "Session limit reached" "Continue with adaptive bandwidth management"

# Always save session state
./bin/savesession "End of session - ready for continuation"
```

### 📥 **Starting Session (AI)**
```bash
# Check available resume points
./bin/resume-from list

# Resume from last point
./bin/resume-from <last_point_id>

# Check current status (using todo status)
./bin/todo-status
```

## 🎨 **AI Workflow Integration**

### 🤖 **AI Responsibilities**

1. **Proactive Checkpoint Suggestions**
   - Suggest savepoints every 15-20 minutes
   - Identify natural breakpoints
   - Ask permission before major work units

2. **Context Preservation**
   - Always checkpoint before switching topics
   - Document reasoning for implementation choices
   - Maintain phase step progress tracking

3. **Communication Protocol**
   - State current work unit at start of each major task
   - Ask "Should I checkpoint here?" at logical breaks
   - Respond immediately to "pause" or "checkpoint" commands

### 🙋 **Human Control Signals**

- **"checkpoint"** - Create immediate savepoint
- **"pause"** - Stop and create pause point
- **"continue"** - Proceed with current work
- **"switch"** - Change focus (auto-checkpoint first)
- **"status"** - Show current progress and next steps

## 📁 **File Organization**

### 📊 **Checkpoint Data Structure**
```
.claude/
├── checkpoints.json          # All checkpoint metadata
├── pause_points.json         # All pause point metadata
├── pause_context_[id].md     # Detailed context for each pause
├── current_phase.json        # Current phase information
└── session_history/          # Historical session data
```

### 📝 **Session Documentation**
```
docs/
├── SESSION_MANAGEMENT_STRATEGY.md  # This document
└── session_templates/              # Templates for common scenarios
```

## 🧪 **Testing Strategy**

### ✅ **Checkpoint System Validation**

1. **Basic Functionality**
   ```bash
   ./bin/checkpoint "Test checkpoint creation"
   ./bin/pause-here "Test pause point" "Test resume action"
   ./bin/resume-from list
   ```

2. **Git Integration**
   - Verify commits are created correctly
   - Check git hash tracking
   - Validate staging behavior

3. **Context Preservation**
   - Test with various work states
   - Verify metadata persistence
   - Check cross-session continuity

## 🚀 **Advanced Features**

### 📈 **Progress Tracking**
- Automatic phase step progress updates
- Time tracking per checkpoint
- Work velocity metrics

### 🔄 **Session Analytics**
- Checkpoint frequency analysis
- Session duration tracking
- Productivity metrics

### 🎯 **Smart Resumption**
- Context-aware next action suggestions
- Dependency checking
- Work prioritization

## 📞 **Emergency Procedures**

### 🚨 **Session Failure Recovery**
1. Check last git commit: `git log -1`
2. List available resume points: `./bin/resume-from list`
3. Resume from latest: `./bin/resume-from <latest_id>`
4. Check current status: `./bin/todo-status`

### 🔧 **Corrupted State Recovery**
1. Restore from git: `git reset --hard <last_good_commit>`
2. Rebuild checkpoint data from git log
3. Resume from closest known state
4. Re-establish todo context

## 📚 **Best Practices**

### ✅ **Do's**
- Create checkpoints every 15-20 minutes
- Use descriptive checkpoint messages
- Always include next actions in pause points
- Ask for permission before major work units
- Maintain consistent session documentation

### ❌ **Don'ts**
- Don't work >30 minutes without checkpointing
- Don't start major work near session limits
- Don't skip context documentation
- Don't commit broken/incomplete work without WIP marking
- Don't ignore natural breakpoints

## 🎯 **Success Metrics**

- **< 5% work lost** due to session limits
- **< 2 minutes** resumption time
- **100% context preservation** across sessions
- **Seamless handoffs** between human and AI
- **Predictable progress** through phase steps

---

*This strategy ensures robust session management for complex agricultural robotics development with minimal context loss and maximum productivity.*