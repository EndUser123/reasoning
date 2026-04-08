# Implementation Plan: Phase 3 - Multi-Agent Mode Integration

**Date:** 2026-03-10
**Status:** 🔄 IN PROGRESS
**Scope:** Multi-Agent Mode integration (Phase 3 from DESIGN.md)

---

## Overview

Integrate the existing mcp-server-mas-sequential-thinking package into the unified reasoning engine as MultiAgentMode. This is a wrapper/integration layer, not a reimplementation.

---

## Architecture

```
reasoning/
├── modes/
│   ├── multi_agent.py         # NEW: MultiAgentMode wrapper
│   └── ...
└── models.py                  # EXISTING: ProcessingResult.agent_outputs

External dependency (keep as-is):
├── .mcp/mcp-server-mas-sequential-thinking/
│   ├── services/server_core.py       # ThoughtProcessor (existing)
│   ├── core/session.py                # SessionMemory (existing)
│   └── processors/multi_thinking_processor.py  # Multi-thinking logic
```

---

## Data Flow

```
User Input → ReasoningEngine.think()
    ↓
MultiAgentMode.process(prompt)
    ↓
Convert to MAS format
    ↓
ThoughtProcessor.process_thought() (external)
    ↓
Multi-Thinking workflow (6 agents)
    ↓
Convert back to ProcessingResult
    ↓
ProcessingResult (conclusion + agent_outputs)
```

---

## Integration Strategy

### Keep Existing Package As-Is

**DO NOT modify** `mcp-server-mas-sequential-thinking`:
- ✅ Keep Agno v2.2.12 framework
- ✅ Keep all 6 agents (Factual, Emotional, Critical, Optimistic, Creative, Synthesis)
- ✅ Keep AI complexity analysis
- ✅ Keep message history optimization
- ✅ Keep typed state management

### Create Wrapper Layer

**File**: `reasoning/modes/multi_agent.py`

```python
class MultiAgentMode(BaseMode):
    """Multi-agent reasoning mode using MAS package integration."""

    def __init__(self, config: ReasoningConfig) -> None:
        super().__init__(config)
        # Lazy import to avoid circular dependency
        self._processor = None

    async def process(
        self,
        prompt: str,
        context: dict[str, object] | None = None,
        **kwargs: object,
    ) -> ProcessingResult:
        """Process prompt using multi-agent workflow."""
        # Lazy load MAS processor
        if self._processor is None:
            self._processor = self._create_mas_processor()

        # Convert our format to MAS format
        thought_data = self._convert_to_mas_format(prompt, context)

        # Call existing ThoughtProcessor
        mas_result = await self._processor.process_thought(thought_data)

        # Convert MAS result back to our format
        return self._convert_from_mas_format(mas_result)
```

---

## Model Mapping

### Our Models → MAS Models

**Our Input:**
```python
prompt: str
context: dict[str, object] | None
```

**MAS Input:**
```python
ThoughtData(
    thought=prompt,
    session_id=...,  # Generate or pass in context
    user_id=...,     # From context or default
    metadata=context or {}
)
```

### MAS Models → Our Output

**MAS Output:**
```python
ThoughtProcessingResult(
    synthesis_result=str,           # Final integrated answer
    agent_outputs=dict[str, str],   # Individual agent outputs
    complexity_score=float,         # AI-assessed complexity
    strategy=str,                   # Single/Double/Triple/Full
    metadata=dict
)
```

**Our Output:**
```python
ProcessingResult(
    conclusion=synthesis_result,
    thought_chain=None,              # MAS uses different structure
    agent_outputs=agent_outputs,     # ✅ Already dict[str, str]
    quality_score=complexity_score / 10,  # Normalize 0-1
    metadata={
        "mode": "multi_agent",
        "strategy": strategy,
        ...other_metadata
    }
)
```

---

## Error Handling

- **Import errors**: MAS package not installed → raise ImportError with clear message
- **API key errors**: Missing LLM_PROVIDER or API keys → raise ValueError
- **Processing errors**: MAS package failures → wrap in ProcessingResult with error metadata
- **Timeout handling**: MAS processing can take 30-60s → add timeout parameter

---

## Test Strategy

### Unit Tests
- `test_multi_agent_mode.py`: MultiAgentMode initialization, format conversion
- `test_model_conversion.py`: Our models ↔ MAS models conversion

### Integration Tests
- End-to-end: `engine.think("test")` with Mode.MULTI_AGENT returns valid result
- Agent outputs: All 6 agents present in result.agent_outputs
- Complexity analysis: Valid complexity_score in metadata

### Test Scenarios
1. **Happy path**: Valid prompt → all 6 agents execute → synthesis result
2. **Import fallback**: MAS not available → ImportError
3. **API key error**: Missing credentials → ValueError
4. **Timeout**: Long-running prompt → timeout after configured duration
5. **Context passing**: context dict passed through to MAS metadata

---

## Standards Compliance

### Python 2025+ Standards
- **Type hints**: All methods use `str`, `dict[str, object]`, `-> ProcessingResult`
- **Async**: Use `async def` for all MAS integration calls
- **Lazy imports**: Use `_lazy_import()` to avoid circular dependencies
- **Error handling**: Try-except with specific exception types

### Toolchain
- **ruff**: Linting (configured in pyproject.toml)
- **mypy**: Type checking (MAS package uses `TYPE_CHECKING` pattern)
- **pytest**: Testing with async support

---

## Ramifications

### Impact on Existing Code
- **New mode**: No breaking changes to existing modes
- **MAS package**: Keep as-is, no modifications
- **Engine**: Update mode_map in ReasoningEngine._create_mode()

### Backwards Compatibility
- **N/A**: New mode, existing modes unchanged

### Migration Path
- **Phase 8**: Update skills to use Mode.MULTI_AGENT
- **Phase 8**: Deprecate direct MAS package usage (if any)

---

## Implementation Tasks

### T1: Create MultiAgentMode Wrapper
- [x] Create `modes/multi_agent.py` with MultiAgentMode class
- [x] Implement lazy import for MAS processor
- [x] Implement process() method with format conversion
- [x] Add timeout handling
- [x] Write tests for multi-agent mode

### T2: Model Conversion Utilities
- [x] Create `_convert_to_mas_format()` method
- [x] Create `_convert_from_mas_format()` method
- [x] Handle ThoughtData mapping
- [x] Handle ProcessingResult mapping
- [x] Write tests for model conversion

### T3: Engine Integration
- [x] Update ReasoningEngine._create_mode() mode_map
- [x] Remove placeholder for Mode.MULTI_AGENT
- [x] Update __init__.py exports (if needed)
- [x] Write integration tests

### T4: Configuration & Defaults
- [x] Add MAS-specific config to ReasoningConfig
- [x] Handle LLM_PROVIDER environment variable
- [x] Handle API key validation
- [x] Document MAS mode configuration
- [x] MAS package handles its own configuration via environment variables

### T5: Documentation & Examples
- [x] Update README.md with Multi-Agent mode example
- [x] Create `examples/multi_agent_demo.py`
- [x] Document MAS package dependency
- [x] Add troubleshooting guide

---

## Pre-Mortem Analysis

**Scenario**: 6 months from now, Multi-Agent mode is not being used. Why?

### Failure Mode 1: MAS package import fails
- **Prevention**: Lazy imports with clear error messages
- **Detection**: Import tests with MAS not installed

### Failure Mode 2: API key configuration confusing
- **Prevention**: Clear error messages, documentation
- **Detection**: User feedback, support tickets

### Failure Mode 3: Performance too slow
- **Prevention**: Timeout configuration, async processing
- **Detection**: Performance tests, monitoring

### Failure Mode 4: Model conversion bugs
- **Prevention**: Comprehensive conversion tests
- **Detection**: Integration tests, round-trip verification

### Observability
- **Metrics to track**:
  - MAS processing time per strategy
  - Agent execution success rate
  - Token usage per agent
  - Error rates by failure type

- **Alerts**:
  - MAS processing timeout rate > 5%
  - Agent failure rate > 10%
  - Token usage spike (>2x baseline)

- **Diagnostic locations**:
  - Logs: MAS package logs (`~/.sequential_thinking/logs/`)
  - Metrics: ProcessingResult.metadata (strategy, complexity_score)
  - Traces: Add session_id to all log entries

---

## Success Criteria

- [ ] All tasks T1-T5 complete
- [ ] All unit tests pass (pytest)
- [ ] All integration tests pass
- [ ] ruff linting passes (no warnings)
- [ ] mypy type checking passes
- [ ] End-to-end demo works: `engine.think("test")` returns valid result with agent_outputs
- [ ] MAS package remains unmodified (verified by git diff)
- [ ] Model conversion tests pass (round-trip verification)
- [ ] Documentation updated with Multi-Agent mode examples

---

## Open Questions

1. **Session management**: Should MultiAgentMode create new session per request or reuse?
   - **Decision**: New session per request (simpler, stateless)
   - **Future**: Add session pooling if performance issue

2. **Error handling**: Should MAS errors raise exceptions or return in ProcessingResult?
   - **Decision**: Return in ProcessingResult.metadata["error"] (consistent with other modes)

3. **Timeout defaults**: What default timeout for MAS processing?
   - **Decision**: 60 seconds (configurable via ReasoningConfig)

---

**Next Steps**: Begin TDD cycle with Task T1 (MultiAgentMode Wrapper)
