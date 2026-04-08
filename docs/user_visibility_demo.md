# What You'll See When Reasoning Is Active

## Visual Indicators Added

### 1. 🤖 Multi-Agent Reasoning (PreToolUse Hook)

**When it triggers**: Complex decisions in tool queries (compare, vs, alternatives, trade-offs)

**What you'll see**:
```
**🤖 Multi-Agent Reasoning Applied**
Ran 6 parallel agents to analyze this decision from multiple perspectives.

[Factual Agent]: [analysis]
[Emotional Agent]: [analysis]
[Critical Agent]: [analysis]
[Optimistic Agent]: [analysis]
[Creative Agent]: [analysis]
[Synthesis Agent]: [integrated conclusions]
```

**Example queries that trigger this**:
- "Should I use Docker or Podman for containerization?"
- "Compare Redux vs React Context for state management"
- "What are the trade-offs between PostgreSQL and MongoDB?"

---

### 2. 🔄 Enhanced Reasoning (Stop Hook)

**When it triggers**: Long responses (≥200 characters)

**What you'll see**:
```
**🔄 Enhanced Reasoning Applied**

Response improved through Generate → Critique → Improve loop.

Conclude: [improved response with better reasoning]
```

**The "Conclude:" prefix** indicates the response went through self-reflection.

---

### 3. Reasoning Mode Selector (UserPromptSubmit Hook)

**When it triggers**: All prompts ≥20 characters with complexity indicators

**What you'll see** (injected before your prompt):
```
**🤖 Multi-Agent Reasoning** (confidence: 2/4)
This query will use multi agent reasoning.
```

**Modes and their indicators**:
- 🔄 Sequential - Step-by-step analysis
- 🤖 Multi-Agent - Multiple perspectives for decisions
- 🌳 Graph - Branching exploration
- ⚡ Two-Stage - Separate reasoning and implementation

---

## Quick Reference

| Symbol | Meaning | When You'll See It |
|--------|---------|-------------------|
| 🤖 | Multi-Agent Reasoning | Complex decisions, comparisons |
| 🔄 | Enhanced Reasoning | Long responses being improved |
| 🌳 | Graph Reasoning | Exploring alternatives |
| ⚡ | Two-Stage Reasoning | Implementation tasks |

## Configuration

To enable debug logging (shows internal stats):

```bash
# Multi-agent reasoning debug
export MULTI_AGENT_DEBUG=true

# Enhanced reflection debug
export ENHANCED_REFLECTION_DEBUG=true
```

To disable specific reasoning modes:

```bash
# Disable UserPromptSubmit reasoning mode selector
export REASONING_MODE_SELECTOR_ENABLED=false

# Disable Stop hook enhanced reasoning
export ENHANCED_REFLECTION_ENABLED=false

# Disable PreToolUse multi-agent reasoning
export MULTI_AGENT_REASONING_ENABLED=false
```
