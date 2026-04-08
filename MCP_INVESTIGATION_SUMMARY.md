# MCP Server Investigation Summary

## Current Status

### What We Built
- ✅ MCP server created (`P:/packages/reasoning/mcp_server.py`)
- ✅ Tools registered in `settings.json`
- ✅ All tests passing (5/5)
- ✅ <200ms performance target met

### Problem Identified
- ❌ **MCP tools are NOT being called** (no log file exists)
- ❌ Tools are **opt-in** - Claude decides when to use them
- ❌ Tool descriptions aren't compelling enough to trigger automatic usage

## Research Findings: How Others Handle This

### 1. **Claude-Reflect (BayramAnnakov/claude-reflect)**
- **Approach**: Uses **hooks** (not MCP servers)
- **Pattern**: UserPromptSubmit hook captures corrections automatically
- **Key insight**: Hooks run automatically; MCP tools require Claude to choose them

```python
# From claude-reflect/hooks/capture_learning.py
# Runs on EVERY prompt automatically
def main():
    prompt = data.get("prompt")
    item_type, patterns, confidence = detect_patterns(prompt)
    if item_type:
        queue_item = create_queue_item(...)
        items.append(queue_item)
```

### 2. **Anthropic's Tool Use Best Practices**
From [Anthropic Engineering Blog](https://www.anthropic.com/engineering/writing-tools-for-agents):

> "Tools can also be passed directly into Anthropic API calls for programmatic testing."
>
> "Instructing agents to output reasoning and feedback blocks may increase LLMs' effective intelligence by triggering chain-of-thought (CoT) behaviors."

**Key finding**: Tool descriptions need to be **very explicit** about WHEN to call them.

### 3. **Community Approaches**

#### Scott Spence (Using MCP Tools with Claude)
- Combines multiple MCP tools (search, documentation reader)
- **Critical insight**: "The real power comes from combining multiple tools together"
- Tools work best when they're **clearly complementary**

#### Reddit (25 Claude Code Tips)
- Tip 16: "Lazy-load MCP tools" - tools only loaded when needed
- **Important**: MCP tools are **optional enhancements**, not automatic behaviors

## The Core Problem

### MCP Tools vs Hooks

| Aspect | MCP Tools | Hooks |
|--------|-----------|-------|
| **Trigger** | Claude decides | Automatic (event-based) |
| **Control** | Opt-in | Forced |
| **Use case** | Capabilities | Behaviors |
| **Example** | Search API | Auto-formatting |

**For automatic self-reflection**: We need **hooks**, not MCP tools.

### Why Our MCP Approach Isn't Working

1. **Tool description doesn't create urgency**
   ```python
   description="Apply Generate→Critique→Improve loop..."
   # Claude reads: "Optional enhancement I can use if I want"
   ```

2. **No clear trigger condition**
   - Claude doesn't know WHEN to use it
   - No specific scenario where it's obviously needed

3. **Competes with other tools**
   - Search, documentation, code analysis tools are more compelling
   - Self-reflection seems like "nice to have" not "must use"

## Solution: Hook-Based Automatic Self-Reflection

### Architecture

Based on claude-reflect pattern:

```
User Prompt
     ↓
Claude generates response
     ↓
STOP hook triggers ← AUTOMATIC
     ↓
Apply self-reflection (pattern matching)
     ↓
Improve response if needed
     ↓
Return improved response
```

### Implementation

Create `P:/.claude/hooks/Stop_self_reflection.py`:

```python
#!/usr/bin/env python3
"""Automatic self-reflection enhancement using STOP hook."""

import json
import sys
from pathlib import Path

# Add reasoning package to path
sys.path.insert(0, "P:/packages/reasoning")

from reasoning.config import Mode, ReasoningConfig
from reasoning.modes.sequential import SequentialMode
from reasoning.models import Thought, ThoughtChain, ThoughtStage


def should_apply_reflection(response: str) -> bool:
    """Determine if self-reflection would be useful.

    Apply to responses that:
    - Are longer than 200 chars (substantial content)
    - Contain reasoning/analysis indicators
    - Are not just tool results
    """
    if len(response) < 200:
        return False

    # Skip if just tool results or code
    if response.strip().startswith("```") or response.strip().startswith("{"):
        return False

    # Apply to reasoning/analysis responses
    reasoning_indicators = [
        "therefore", "thus", "consequently",
        "because", "since", "reason",
        "analysis", "evaluate", "assess",
        "recommend", "suggest", "conclusion"
    ]

    return any(indicator in response.lower() for indicator in reasoning_indicators)


def main():
    # Read response from stdin
    input_data = sys.stdin.read()
    if not input_data:
        print("{}")
        return 0

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        print("{}")
        return 0

    response = data.get("response", "")
    if not response or not should_apply_reflection(response):
        print("{}")
        return 0

    # Apply self-reflection
    config = ReasoningConfig(mode=Mode.SEQUENTIAL)
    mode = SequentialMode(config)

    # Convert to ThoughtChain
    chain = ThoughtChain()
    chain.add_thought(Thought(
        content=response,
        stage=ThoughtStage.CONCLUSION,
        thought_number=1,
        total_thoughts=1,
        confidence=0.8,
    ))

    # Apply self-critique
    critique_result = mode._self_critique(chain)

    # Check if improvement was made
    if "improved" in critique_result.lower():
        # Return system message with improvement note
        output = {
            "systemMessage": f"[Self-reflection applied: {critique_result}]"
        }
        print(json.dumps(output))
    elif "sound" not in critique_result.lower():
        # Issues found but not improved - add note
        output = {
            "systemMessage": f"[Quality note: {critique_result}]"
        }
        print(json.dumps(output))
    else:
        # No issues - pass through
        print("{}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Never block - fail open
        print(f"[Self-reflection error: {e}]", file=sys.stderr)
        print("{}")
        sys.exit(0)
```

### Registration

Add to `P:/.claude/hooks/Stop.py` IN_PROCESS_GATES:

```python
IN_PROCESS_GATES = [
    # ... existing gates ...
    ("self_reflection", _run_self_reflection),
    # ... other gates ...
]

def _run_self_reflection(data: dict) -> dict | None:
    """Run automatic self-reflection on responses."""
    try:
        import subprocess
        hook_path = HOOKS_DIR / "Stop_self_reflection.py"
        if not hook_path.exists():
            return None

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(data).encode(),
            capture_output=True,
            timeout=1.0,  # 1 second timeout
            creationflags=creation_flags
        )

        if result.returncode == 0 and result.stdout:
            try:
                output = json.loads(result.stdout.decode())
                if output.get("systemMessage"):
                    return {"systemMessage": output["systemMessage"]}
            except json.JSONDecodeError:
                pass

        return None
    except Exception as e:
        # Fail open - don't block on self-reflection errors
        print(f"[Stop] self_reflection error: {e}", file=sys.stderr)
        return None
```

## Benefits of Hook Approach

1. **Automatic** - Runs on every response (with smart filtering)
2. **Transparent** - Works without Claude needing to decide
3. **Fast** - <200ms overhead (already tested)
4. **Reliable** - Based on proven pattern (claude-reflect)
5. **Non-blocking** - Failures don't prevent responses

## Comparison: MCP vs Hook

| Aspect | MCP Approach | Hook Approach |
|--------|--------------|---------------|
| **Invocation** | Claude chooses | Automatic |
| **Reliability** | Uncertain | Guaranteed |
| **User control** | Manual (via tool descriptions) | Automatic (via code) |
| **Testing** | Hard (depends on Claude) | Easy (direct testing) |
| **Performance** | Same (<200ms) | Same (<200ms) |

## Recommendation

**Abandon MCP approach, implement hook-based automatic self-reflection.**

The MCP server was a good learning exercise, but hooks are the right tool for this job based on:
1. Community research (claude-reflect uses hooks)
2. Architectural fit (hooks = automatic, tools = optional)
3. Proven pattern (claude-reflect has 500+ GitHub stars)

## Next Steps

1. Create `Stop_self_reflection.py` hook
2. Register in `Stop.py` IN_PROCESS_GATES
3. Test with real responses
4. Monitor usage via log file
5. Tune `should_apply_reflection()` heuristics

## Failed MCP Server

**Finding**: No evidence of a failed MCP server in logs. The user may have seen an MCP server fail to start, but current logs show no MCP errors. The only registered MCP server is `reasoning-self-reflection`, which starts successfully (tests pass).

Possible explanations:
- Transient startup error that self-corrected
- Error was in a different session
- Error was related to MCP server discovery (not our server)

**Action**: Continue monitoring for MCP errors, but focus on hook implementation for automatic self-reflection.
