# Implementation Plan: Reasoning Hook Integration with Symlinks

**Date:** 2026-03-11
**Status:** 📋 PLANNED
**Scope:** Integrate reasoning system hooks using symlink pattern

---

## Overview

Deploy 3 reasoning system enhancements as hooks in the reasoning package, with symlinks in .claude/hooks/ for router integration.

---

## Architecture

```
P:/packages/reasoning/
├── hooks/
│   ├── Start_reasoning_mode_selector.py      # NEW: Mode selection logic
│   ├── Stop_reasoning_enhanced.py            # NEW: Enhanced quality gate
│   └── PreTool_multi_agent_reasoning.py      # NEW: Multi-agent reasoning
└── tests/
    └── test_hooks/                             # NEW: Hook tests

P:/.claude/hooks/
├── Start_reasoning_mode_selector.py -> ../../packages/reasoning/hooks/Start_reasoning_mode_selector.py
├── Stop_reasoning_enhanced.py -> ../../packages/reasoning/hooks/Stop_reasoning_enhanced.py
└── PreTool_multi_agent_reasoning.py -> ../../packages/reasoning/hooks/PreTool_multi_agent_reasoning.py
```

---

## Data Flow

```
User Prompt → Start Reasoning Mode Selector Hook
    ↓
Selects reasoning mode (sequential/multi-agent/graph/cognitive/two-stage)
    ↓
Stores selected mode in context

[... tool use ...]

    ↓
PreTool Multi-Agent Hook
    ↓
For complex decisions → Multi-agent reasoning
    ↓

Response Complete → Enhanced Reasoning Quality Gate
    ↓
Applies full reasoning process (not just critique)
    ↓
Returns improved response or allows original
```

---

## Error Handling

- **Windows symlink fallback**: If symlink creation fails, copy files instead
- **Hook failure mode**: Fail-open (errors don't block responses)
- **Graceful degradation**: If reasoning package unavailable, hooks return empty/pass-through

---

## Test Strategy

1. **Unit tests** for each hook (test mode selection, quality gate, multi-agent)
2. **Integration tests** for symlink creation and router registration
3. **End-to-end tests** for full reasoning flow

---

## Standards Compliance

**Python 2025+ standards:**
- Type hints on all functions
- ruff linting compliance
- mypy type checking
- pytest for testing
- Fail-open error handling

---

## Ramifications

**Breaks:** Nothing (new hooks, additive changes)

**Edge cases:**
- Windows symlink permissions may require admin
- Router integration may need testing
- Multi-agent mode requires LLM API keys (optional dependency)

**Migration:** None (this is new functionality)

---

## Implementation Tasks

### Task 1: Create Reasoning Mode Selector Hook
**File:** `P:/packages/reasoning/hooks/Start_reasoning_mode_selector.py`

**Requirements:**
- Analyzes query for complexity indicators
- Routes to appropriate reasoning mode (sequential, multi-agent, graph, two-stage)
- Returns selected mode as additionalContext
- Fail-open on errors

**Test cases:**
- Simple query → sequential mode
- Complex decision → multi-agent mode
- What-if exploration → graph mode
- Implementation task → two-stage mode

---

### Task 2: Create Enhanced Quality Gate Hook
**File:** `P:/packages/reasoning/hooks/Stop_reasoning_enhanced.py`

**Requirements:**
- Extends existing quality gate to use full reasoning process
- Creates proper thought chain (not just single conclusion)
- Returns improved response if quality gate fails
- Maintains <200ms performance target

**Test cases:**
- Response with logical gaps → improved version returned
- Good response → None returned (allow through)
- Hook error → graceful degradation

---

### Task 3: Create Multi-Agent Reasoning Hook
**File:** `P:/packages/reasoning/hooks/PreTool_multi_agent_reasoning.py`

**Requirements:**
- Detects complex decisions requiring multiple perspectives
- Runs multi-agent reasoning for complex queries
- Returns agent outputs as additionalContext
- Falls back to empty output if LLM unavailable

**Test cases:**
- Simple query → skipped (empty output)
- Complex architecture decision → multi-agent analysis
- LLM API unavailable → graceful fallback

---

### Task 4: Create Symlink Integration Script
**File:** `P:/packages/reasoning/scripts/create_hook_symlinks.py`

**Requirements:**
- Creates symlinks from .claude/hooks/ to package hooks
- Falls back to file copy on Windows if symlinks fail
- Registers hooks in appropriate routers
- Creates tests directory structure

**Test cases:**
- Symlink creation succeeds
- Symlink fallback to copy works
- Hook registration in routers
- Cleanup removes symlinks/copies

---

### Task 5: Router Integration
**Files:** `P:/.claude/hooks/Start.py`, `P:/.claude/hooks/Stop.py`, `P:/.claude/hooks/PreToolUse_router.py` (or settings.json)

**Requirements:**
- Register hooks in appropriate routers
- Add to IN_PROCESS_GATES lists
- Configure execution order/priorities
- Document integration in CLAUDE.md

**Test cases:**
- Hooks execute in correct order
- Mode selector runs before tool use
- Quality gate runs after response
- Multi-agent hook runs pre-tool-use

---

## Pre-Mortem Analysis

**Failure Mode 1:** Windows symlinks fail due to permissions
- **Root cause:** Admin rights required for symbolic links
- **Probability:** Medium (Windows UAC)
- **Prevention:** Implement fallback to file copy
- **Test:** Run on Windows without admin, verify copy works

**Failure Mode 2:** Router integration breaks existing hooks
- **Root cause:** Incorrect priority or execution order
- **Probability:** Low (hooks are additive)
- **Prevention:** Use late priority (execute after existing hooks)
- **Test:** Run existing hook test suite, verify no regressions

**Failure Mode 3:** Multi-agent mode times out
- **Root cause:** LLM API slow or unavailable
- **Probability:** Medium (external dependency)
- **Prevention:** 5-second timeout, graceful fallback
- **Test:** Mock LLM timeout, verify fallback works

---

## Observability

**Metrics to track:**
- Hook execution frequency (which modes are selected)
- Quality improvement rate (responses enhanced vs. passed through)
- Multi-agent usage (how often complex decisions trigger)
- Symlink vs. copy usage (Windows compatibility)

**Log locations:**
- `P:/packages/reasoning/hook_usage.log` (existing)
- `P:/.claude/state/logs/reasoning_hooks.log` (new)
- Router debug output via `ROUTER_DEBUG=true`

**Alert thresholds:**
- Hook execution >500ms (performance degradation)
- Multi-agent timeout rate >10% (LLM API issues)
- Symlink fallback usage >50% (Windows permission problems)

---

## Success Criteria

- [ ] All 3 hook files created in reasoning package
- [ ] Symlinks created in .claude/hooks/
- [ ] Hooks registered in routers/settings.json
- [ ] All tests passing (unit + integration)
- [ ] Documentation updated (CLAUDE.md, README)
- [ ] Performance targets met (<200ms for quality gate)
