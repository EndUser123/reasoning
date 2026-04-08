# MCP Server Integration

## Overview

The reasoning package now provides an **MCP server** for automatic self-reflection enhancement. This allows Claude to automatically apply Generate→Critique→Improve loop during response generation.

**Performance**: <200ms overhead (pattern matching, no LLM calls)
**Quality Improvement**: ~7% average gain (validated via A/B testing)

## Architecture

```
┌─────────────┐
│   Claude    │
│  Response   │
└──────┬──────┘
       │
       │ Calls MCP tool during generation
       ▼
┌──────────────────────────┐
│   MCP Server (stdio)      │
│   - self_reflect()        │
│   - critique_response()   │
└──────┬───────────────────┘
       │
       │ Pattern matching
       ▼
┌──────────────────────────┐
│  SequentialMode          │
│  - Critique engine       │
│  - Improvement engine    │
│  - Quality gate          │
└──────┬───────────────────┘
       │
       │ Improved response
       ▼
┌─────────────┐
│   Claude    │
│ Final Output│
└─────────────┘
```

## Installation

The MCP server is already configured in `P:/.claude/settings.json`:

```json
{
  "mcpServers": {
    "reasoning-self-reflection": {
      "command": "python",
      "args": ["P:/packages/reasoning/mcp_server.py"],
      "env": {}
    }
  }
}
```

### Manual Installation (if needed)

1. Install dependencies:
```bash
cd P:/packages/reasoning
pip install -e .
```

2. Verify MCP server runs:
```bash
python mcp_server.py
```

3. Restart Claude Code to load the MCP server

## Available Tools

### 1. `self_reflect`

**Purpose**: Apply Generate→Critique→Improve loop to improve response quality

**Usage**: Claude can call this during response generation
```python
# Claude (during generation)
response = "Therefore, X is always true."

# Calls MCP tool
improved = await self_reflect(response)

# Result: "X is typically true in most cases."
```

**What it does**:
- Detects logical gaps (conclusions without reasoning)
- Detects overconfidence (absolute claims without evidence)
- Detects contradictions (conflicting statements)
- Detects missing alternatives (unexplored options)
- Applies pattern-based improvements
- Returns improved version if quality gate fails

**Performance**: <200ms overhead

### 2. `critique_response`

**Purpose**: Analyze response for quality issues without modifying it

**Usage**: Use when you want to understand issues but not auto-fix
```python
issues = await critique_response(response)
# Returns detailed breakdown by category
```

**Returns**:
- Logical gaps count and descriptions
- Overconfidence count and descriptions
- Contradictions count and descriptions
- Missing alternatives count and descriptions

## How It Works

### Automatic Invocation

When Claude generates a response, it can choose to call the `self_reflect` tool:

1. **Claude generates draft response**
2. **Claude calls `self_reflect(response)`**
3. **MCP server receives request via stdio**
4. **SequentialMode applies critique and improvement**
5. **MCP server returns improved response**
6. **Claude uses improved version for final output**

### Pattern-Based Analysis

The self-reflection uses **pattern matching** (no LLM calls):

- **Logical gaps**: "therefore" without "because/since/evidence"
- **Overconfidence**: "always/never" without evidence or qualifiers
- **Contradictions**: "will/won't", "true/false" conflicts
- **Missing alternatives**: definitive answer without exploring options

### Quality Gate

Only improves responses that fail quality threshold:
- **< 3 issues**: Pass (return original)
- **≥ 3 issues**: Fail (apply improvements)

This prevents false positives on good responses.

## Validation

### Test Coverage

- **78 unit tests**: All pattern matching scenarios
- **16 integration tests**: End-to-end self-reflection flow
- **10 A/B validation tests**: Measured quality improvement

### A/B Test Results

```
Test Date: 2026-03-10
Test Cases: 10
Average Improvement: 7.1%
Min Improvement: 0.0%
Max Improvement: 25.0%
Pattern Matching Accuracy: >70%
```

### Running Tests

```bash
# Unit tests
cd P:/packages/reasoning
pytest tests/modes/test_sequential.py -v

# Integration tests
pytest tests/modes/test_sequential_integration.py -v

# Quality validation
pytest tests/modes/test_sequential_quality_validation.py -v
```

## Usage Examples

### Example 1: Logical Gap Detection

**Before**: "Therefore, the answer is X."

**After self_reflect**: "Based on the evidence provided, the answer is X. The reasoning is..."

### Example 2: Overconfidence Reduction

**Before**: "This will always happen."

**After self_reflect**: "This will typically happen in most cases."

### Example 3: Contradiction Resolution

**Before**: "The system will work. The system won't work."

**After self_reflect**: "The system will work under normal conditions [Note: Original had conflicting statements]"

### Example 4: Missing Alternatives

**Before**: "The best approach is X."

**After self_reflect**: "The best approach is X. However, alternatives include Y and Z, which may be better for..."

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Overhead | <200ms |
| LLM calls | 0 (pattern matching) |
| Quality gain | +7.1% average |
| Best case | +25% improvement |
| False positives | Conservative threshold (<3 issues) |

## Troubleshooting

### MCP Server Not Starting

**Symptoms**: Tools not available in Claude

**Solutions**:
1. Check MCP server runs manually:
   ```bash
   python P:/packages/reasoning/mcp_server.py
   ```

2. Check settings.json has correct path:
   ```json
   "args": ["P:/packages/reasoning/mcp_server.py"]
   ```

3. Check dependencies installed:
   ```bash
   pip install -e P:/packages/reasoning
   ```

### Tools Available But Not Working

**Symptoms**: Claude can see tools but calls fail

**Solutions**:
1. Check MCP server logs (stderr from server process)
2. Verify reasoning package imports work:
   ```python
   from reasoning import ReasoningEngine, Mode
   engine = ReasoningEngine(mode=Mode.SEQUENTIAL)
   ```

3. Test self-critique directly:
   ```python
   from reasoning.modes.sequential import SequentialMode
   mode = SequentialMode(config)
   critique = mode._critique_reasoning("Test response")
   ```

## Migration from Manual Skill Invocation

### Old Approach (Manual)

User had to type:
```
/sequential-thinking
```

Then Claude would:
1. Load skill
2. Follow skill instructions
3. Use Agent tool for mode switching
4. Manually orchestrate Generate→Critique→Improve

### New Approach (Automatic)

With MCP server:
1. **Automatic**: Claude calls `self_reflect` during generation
2. **No manual invocation**: Works transparently
3. **Faster**: <200ms vs Agent tool overhead
4. **Pattern-based**: No external LLM calls needed

## Future Enhancements

### Phase 2: Contextual Triggering

Smart invocation based on:
- Response length (longer responses = more benefit)
- Question complexity (multi-step reasoning)
- Domain patterns (technical analysis benefits most)

### Phase 3: Learning from Usage

Track which patterns are most common and:
- Tune quality gate threshold
- Improve pattern accuracy
- Add new issue categories

### Phase 4: Multi-Language Support

Extend pattern matching to:
- Code responses (syntax-aware)
- Natural language (idiom detection)
- Mixed responses (code + explanation)

## See Also

- **Quality Validation Results**: `QUALITY_VALIDATION_RESULTS.md`
- **Implementation Details**: `DESIGN.md`
- **Sequential Mode Tests**: `tests/modes/test_sequential.py`
- **Integration Tests**: `tests/modes/test_sequential_integration.py`
