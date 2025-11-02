# 🚨 RED-GREEN-REFACTOR ABSOLUTE ENFORCEMENT
## Zero Exceptions Policy for Agricultural Robotics Platform

> **CRITICAL**: This document establishes absolute, non-negotiable enforcement of Red-Green-Refactor methodology for ALL code contributors - human and AI agents.

---

## 🎯 ABSOLUTE REQUIREMENTS

### **RED PHASE - MANDATORY FAILING TEST**
```bash
# STEP 1: MUST write failing test FIRST
pytest tests/unit/component/test_new_feature.py::test_specific_behavior -v
# REQUIRED OUTPUT: FAILED with meaningful assertion error
```

**❌ FORBIDDEN RED PHASE VIOLATIONS**:
- Writing ANY implementation code before test exists
- Using `pass` or placeholder code to make tests pass
- Tests that fail due to missing imports/modules (insufficient)
- Tests without agricultural context and safety considerations

### **GREEN PHASE - MINIMAL PASSING IMPLEMENTATION**
```bash
# STEP 2: Write MINIMAL code to pass test
pytest tests/unit/component/test_new_feature.py::test_specific_behavior -v
# REQUIRED OUTPUT: PASSED with real working code
```

**❌ FORBIDDEN GREEN PHASE VIOLATIONS**:
- Over-engineering beyond test requirements
- Adding features not covered by current test
- Skipping tests with temporary `@pytest.mark.skip`
- Implementing without running test to verify GREEN status

### **REFACTOR PHASE - QUALITY ENHANCEMENT**
```bash
# STEP 3: Improve code while maintaining tests
pytest tests/unit/component/ -v  # All tests must remain PASSED
ruff check afs_fastapi/component/ --select=ALL  # Zero warnings
pyright afs_fastapi/component/ --strict  # Complete type safety
```

**❌ FORBIDDEN REFACTOR PHASE VIOLATIONS**:
- Breaking existing tests during refactoring
- Changing behavior without updating tests first
- Refactoring without quality tool validation
- Skipping refactor phase entirely

---

## 🔒 ENFORCEMENT MECHANISMS

### **Pre-Commit Hook Validation**
```bash
# .claude/hooks/tdd_enforcement.py BLOCKS these violations:
python .claude/hooks/tdd_enforcement.py
```

**BLOCKED ACTIONS**:
- ❌ Commits with implementation files lacking test files
- ❌ Commits modifying code without recent test activity
- ❌ Critical agricultural components without safety tests
- ❌ Code changes that break existing test coverage

### **AI Agent Compliance Monitoring**
```python
class AIAgentTDDValidator:
    """
    Monitors ALL AI agent activities for TDD compliance.

    ZERO TOLERANCE for Red-Green-Refactor violations.
    """

    FORBIDDEN_AI_PATTERNS = [
        "implement.*without.*test",      # Implementation before tests
        "skip.*test.*for.*now",         # Deferred testing
        "TODO.*add.*test.*later",       # Postponed test creation
        "pass.*#.*placeholder",         # Fake GREEN phase
    ]
```

---

## 🚨 VIOLATION CONSEQUENCES

### **Immediate Blocking Actions**
- **Commit Rejection**: Pre-commit hooks BLOCK non-TDD code
- **Build Failure**: CI/CD pipeline FAILS on TDD violations
- **Code Review Block**: PRs REJECTED without TDD compliance
- **Agent Override**: AI assistants MUST restart with RED phase

### **Agricultural Safety Rationale**
```
SAFETY-CRITICAL JUSTIFICATION:
╔══════════════════════════════════════════════════╗
║ Agricultural equipment coordination failures      ║
║ can result in:                                   ║
║                                                  ║
║ • Equipment collisions                           ║
║ • Crop damage                                    ║
║ • Operator safety incidents                      ║
║ • Multi-million dollar harvest losses            ║
║                                                  ║
║ RED-GREEN-REFACTOR prevents these failures       ║
║ through verified reliability                     ║
╚══════════════════════════════════════════════════╝
```

---

## 📋 COMPLIANCE CHECKLIST

### **Before ANY Code Development**
- [ ] **RED**: Failing test written with agricultural context
- [ ] **RED**: Test covers safety requirements for component
- [ ] **RED**: Performance constraints validated for equipment
- [ ] **RED**: Test run confirms FAILED status with meaningful error

### **During Implementation**
- [ ] **GREEN**: Minimal code satisfies test requirements exactly
- [ ] **GREEN**: No additional functionality beyond test scope
- [ ] **GREEN**: Test run confirms PASSED status
- [ ] **GREEN**: All existing tests continue passing

### **After Implementation**
- [ ] **REFACTOR**: Code quality improved without behavior change
- [ ] **REFACTOR**: All tests remain PASSED after changes
- [ ] **REFACTOR**: Quality tools show zero warnings
- [ ] **REFACTOR**: Documentation updated for changes

---

## 🎯 SUCCESS EXAMPLES

### **✅ CORRECT RED-GREEN-REFACTOR Pattern**
```python
# RED PHASE: Write failing test
def test_tractor_emergency_stop_coordination(self):
    """Test emergency stop propagation across multi-tractor fleet."""
    coordinator = FleetCoordinator()
    coordinator.add_tractor("T001", position=(0, 0))
    coordinator.add_tractor("T002", position=(100, 0))

    # Trigger emergency stop on one tractor
    coordinator.emergency_stop("T001")

    # All tractors must stop within 500ms (ISO 18497)
    assert coordinator.get_tractor("T002").status == "emergency_stopped"
    assert coordinator.get_stop_propagation_time() < 0.5

# GREEN PHASE: Minimal implementation
class FleetCoordinator:
    def emergency_stop(self, tractor_id: str) -> None:
        for tractor in self.tractors:
            tractor.status = "emergency_stopped"

# REFACTOR PHASE: Enhance quality
class FleetCoordinator:
    def emergency_stop(self, tractor_id: str) -> None:
        """Propagate emergency stop with verified timing."""
        start_time = time.time()
        for tractor in self.tractors:
            tractor.emergency_stop()
        self._propagation_time = time.time() - start_time
```

---

## 🚀 IMMEDIATE ACTIONS REQUIRED

### **For ALL Contributors**
1. **Review this document** before ANY development activity
2. **Bookmark RED-GREEN-REFACTOR checklist** for reference
3. **Practice TDD cycle** with sample agricultural component
4. **Verify pre-commit hooks** are installed and active

### **For AI Agents**
1. **Load TDD requirements** at session start
2. **Validate RED phase** before ANY implementation
3. **Confirm GREEN status** with real working tests
4. **Complete REFACTOR cycle** for all code changes

---

## 🏆 ABSOLUTE COMMITMENT

**This platform commits to ZERO EXCEPTIONS for Red-Green-Refactor methodology.**

Every line of code in AFS FastAPI represents agricultural equipment safety and reliability. The Red-Green-Refactor cycle is our guarantee that this code is worthy of controlling multi-million dollar agricultural operations.

**NO SHORTCUTS. NO EXCEPTIONS. NO COMPROMISES.**

---

**Document Version**: 1.0
**Effective**: Immediately
**Enforcement Level**: ABSOLUTE
**Compliance Required**: 100%