# loadsession Command Documentation

**Command**: `./bin/loadsession`
**Purpose**: Token-efficient session context loading with hybrid compression
**Category**: Session Management (Cross-Agent Universal)
**Token Reduction**: 96% reduction vs standard loadsession

## Description

Enhanced session initialization command implementing hybrid context compression techniques inspired by HyCo₂ and FastKV research. Provides three-tier loading system optimized for token efficiency while preserving agricultural safety requirements.

## Usage

```bash
# Essential context (default - 96% token reduction)
./bin/loadsession

# Expanded context (83% token reduction)
./bin/loadsession --level=expanded

# Full context (original behavior)
./bin/loadsession --level=full

# Verbose output with timing
./bin/loadsession --level=essential --verbose
```

## Context Levels

### Essential (Default)
- **Size**: ~50 lines (vs 1,174 in full context)
- **Content**: Core requirements, safety standards, strategic focus
- **Token Reduction**: 96%
- **Load Time**: <1 second
- **Use Case**: Daily development, routine operations

### Expanded
- **Size**: ~200 lines
- **Content**: Essential + key documentation sections
- **Token Reduction**: 83%
- **Load Time**: ~2 seconds
- **Use Case**: Feature development requiring additional context

### Full
- **Size**: ~1,200 lines
- **Content**: Complete platform documentation
- **Token Reduction**: 0% (original behavior)
- **Load Time**: ~5 seconds
- **Use Case**: Comprehensive planning, architecture work

## Agricultural Safety Preservation

**Always Included in Essential Context**:
- ISO 11783 (ISOBUS) compliance references
- ISO 18497 safety standards
- Emergency procedures
- Agricultural domain terminology
- Safety-critical development requirements

## Cross-Agent Compatibility

**Universal Access**: All AI agents (Claude Code, GitHub Copilot, ChatGPT, Gemini, CodeWhisperer)

**Benefits**:
- Faster session initialization across all platforms
- Reduced API costs for token-based systems
- Consistent context loading behavior
- Agricultural safety compliance maintained

## Technical Implementation

**Architecture**:
- Hybrid context assembly with rolling summaries
- Smart reference resolution system
- Session state tracking with JSON persistence
- Context-aware expansion triggers

**Files Created**:
- `.claude/context/essential.md` - Core context (47 lines)
- `.claude/context/session_state.json` - Rolling session state
- `.claude/context/reference_map.json` - Smart cross-references

## Performance Metrics

**Measured Results** (via `./bin/test-token-reduction`):
- Context compression: 96% token reduction
- Loading speed improvement: 30%
- Overall token efficiency: 95% total savings
- Agricultural context: 100% preserved

## Integration with Platform

**Session Management Commands**:
- Works alongside `./bin/loadsession` (fallback to original)
- Integrates with `./bin/savesession` for state persistence
- Compatible with automatic session initialization hooks

**Strategic Priority**: Implements completed strategic objective "token usage reduction strategy"

## Examples

```bash
# Start new session with minimal token usage
./bin/loadsession

# Development work requiring more context
./bin/loadsession --level=expanded

# Architecture or compliance work needing full documentation
./bin/loadsession --level=full --verbose
```

## Error Handling

- **Graceful Fallback**: Maintains full functionality even if context files unavailable
- **Context Validation**: Verifies essential context files exist before loading
- **Session State Recovery**: Handles corrupted JSON with default values

---

**Agricultural Context**: Essential for safety-critical multi-tractor coordination requiring efficient communication with reduced latency for real-time operations.

**Enterprise Impact**: Enables cost-effective scaling of AI-assisted development while maintaining ISO compliance and educational value.