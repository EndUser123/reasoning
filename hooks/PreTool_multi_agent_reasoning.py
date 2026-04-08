#!/usr/bin/env python3
"""PreTool hook: Multi-agent reasoning for complex decisions.

Analyzes tool use context to detect complex decision-making scenarios:
- Comparisons between alternatives (Redis vs Memcached)
- Trade-off analysis (PostgreSQL vs MongoDB)
- Option evaluation (microservices or monolith)

When detected, runs multi-agent reasoning using 6 parallel perspectives:
- Factual: Objective analysis
- Emotional: User experience considerations
- Critical: Potential issues and risks
- Optimistic: Best-case scenarios
- Creative: Alternative approaches
- Synthesis: Integrated recommendation

Registers with PreToolUse router to inject multi-agent insights into context.

Performance target: <500ms for multi-agent processing
Fail-open design: errors don't block tool execution
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path


def _resolve_reasoning_package() -> Path:
    """Find the reasoning package regardless of hook install location."""
    env_path = os.environ.get("REASONING_PKG_PATH", "").strip()
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([
        Path(__file__).resolve().parent.parent,
        Path("P:/packages/reasoning"),
    ])

    for candidate in candidates:
        if (candidate / "reasoning" / "config.py").exists():
            return candidate

    raise RuntimeError("Could not locate reasoning package")


# Add reasoning package to path
REASONING_PKG = _resolve_reasoning_package()
sys.path.insert(0, str(REASONING_PKG))

from reasoning.config import Mode, ReasoningConfig
from reasoning.modes.multi_agent import MultiAgentMode

# Usage logging
LOG_FILE = REASONING_PKG / "hook_usage.log"

# Performance statistics (in-memory, per-session)
filter_stats = {"applied": 0, "skipped": 0, "errors": 0}

DEFAULT_TIMEOUT_MS = 400


def _env_enabled(name: str, default: bool = True) -> bool:
    """Parse a conventional boolean environment flag."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _timeout_seconds() -> float:
    """Resolve multi-agent timeout budget from environment."""
    raw_value = os.environ.get("MULTI_AGENT_TIMEOUT_MS", str(DEFAULT_TIMEOUT_MS)).strip()
    try:
        timeout_ms = max(1, int(raw_value))
    except ValueError:
        timeout_ms = DEFAULT_TIMEOUT_MS
    return timeout_ms / 1000.0


def should_use_multi_agent_reasoning(tool_input_query: str) -> tuple[bool, str]:
    """Determine if multi-agent reasoning should be applied.

    Args:
        tool_input_query: Query text from tool input (may be empty string)

    Returns:
        (should_apply, reason) tuple

    Apply to queries that:
    - Compare alternatives (X vs Y, X or Y)
    - Analyze trade-offs
    - Evaluate options
    - Make architectural decisions
    """
    global filter_stats

    # Skip empty or non-string queries
    if not tool_input_query or not isinstance(tool_input_query, str):
        filter_stats["skipped"] += 1
        return False, "no_query"

    # Complex decision indicators
    decision_indicators = [
        # Alternatives comparison
        r"\bvs\b", r"\bversus\b", r"\bor\b", r'\balternatives?\b',
        # Comparison language
        r'\bcompare\b', r'\bbetter\b', r'\bprefer\b', r'\boption\b',
        # Decision-making
        r'should we use', r'trade-off', r'best option', r'decision between',
        # Architecture choices
        r'\bmicroservices?\b.*\bmonolith\b', r'\bpostgresql\b.*\bmongodb\b',
        r'\bredis\b.*\bmemcached\b', r'\breact\b.*\bvue\b',
    ]

    query_lower = tool_input_query.lower()

    # Check for decision indicators using regex
    for pattern in decision_indicators:
        if re.search(pattern, query_lower):
            filter_stats["applied"] += 1
            return True, "complex_decision"

    filter_stats["skipped"] += 1
    return False, "no_complex_decision"


def apply_multi_agent_reasoning(query: str) -> dict[str, str] | None:
    """Apply multi-agent reasoning to extract multiple perspectives.

    Uses MultiAgentMode to run 6 parallel agents:
    - Factual, Emotional, Critical, Optimistic, Creative, Synthesis

    Args:
        query: The query text to analyze

    Returns:
        Dictionary with agent outputs (agent_name: output) if successful,
        None if reasoning fails or no outputs available
    """
    try:
        if not query or not isinstance(query, str):
            return None

        config = ReasoningConfig(mode=Mode.MULTI_AGENT)
        mode = MultiAgentMode(config)

        # Run the full async reasoning process synchronously
        start_time = time.time()

        # Run async process in sync context (hooks must be synchronous)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                asyncio.wait_for(mode.process(query), timeout=_timeout_seconds())
            )
        finally:
            loop.close()

        elapsed_ms = (time.time() - start_time) * 1000

        # Log usage with timing
        _log_usage(len(query), elapsed_ms, result)

        # Extract agent outputs if available
        if result and result.agent_outputs:
            filter_stats["applied"] += 1
            return result.agent_outputs

        # No agent outputs generated
        return None

    except TimeoutError:
        filter_stats["skipped"] += 1
        print(
            "[PreTool_multi_agent_reasoning] Timed out, skipping multi-agent reasoning",
            file=sys.stdout,
        )
        return None
    except ImportError:
        # MAS package not installed - fail open
        filter_stats["errors"] += 1
        print(
            "[PreTool_multi_agent_reasoning] MAS package not available, skipping multi-agent reasoning",
            file=sys.stdout,
        )
        return None
    except Exception as e:
        # Fail open - don't block on errors
        filter_stats["errors"] += 1
        print(f"[PreTool_multi_agent_reasoning] Error: {e}", file=sys.stdout)
        return None


def _log_usage(query_length: int, elapsed_ms: float, result) -> None:
    """Log hook usage for tracking."""
    try:
        import time

        log_entry = {
            "timestamp": time.time(),
            "hook": "PreTool_multi_agent_reasoning",
            "query_length": query_length,
            "elapsed_ms": round(elapsed_ms, 2),
            "quality_score": getattr(result, "quality_score", None),
            "result": "agent_outputs" if result and result.agent_outputs else "no_outputs",
        }
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Don't fail on logging errors


def format_agent_outputs(agent_outputs: dict[str, str]) -> str:
    """Format agent outputs for context injection.

    Args:
        agent_outputs: Dictionary of agent_name: output

    Returns:
        Formatted string with all agent perspectives
    """
    if not agent_outputs:
        return ""

    lines = ["## Multi-Agent Analysis"]
    for agent_name, output in agent_outputs.items():
        lines.append(f"\n### {agent_name}")
        lines.append(output)

    return "\n".join(lines)


def main():
    """Main hook entry point."""
    # Read input from stdin
    input_data = sys.stdin.read()
    if not input_data:
        print("{}")
        return 0

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        print("{}")
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if not _env_enabled("MULTI_AGENT_ENABLED", default=True):
        if os.environ.get("MULTI_AGENT_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "reason": "disabled_by_env"}}))
        else:
            print("{}")
        return 0

    # Extract query from tool_input (varies by tool)
    # Common query fields: query, prompt, question
    query = (
        tool_input.get("query") or
        tool_input.get("prompt") or
        tool_input.get("question") or
        tool_input.get("message") or
        ""
    )

    # Check if we should apply multi-agent reasoning
    should_apply, reason = should_use_multi_agent_reasoning(query)
    if not should_apply:
        # Debug mode: include stats even when skipping
        if os.environ.get("MULTI_AGENT_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "reason": reason}}))
        else:
            print("{}")
        return 0

    # Apply multi-agent reasoning
    agent_outputs = apply_multi_agent_reasoning(query)
    if agent_outputs:
        # Format outputs for context injection
        formatted_output = format_agent_outputs(agent_outputs)

        # Add user-facing header
        user_header = (
            f"**🤖 Multi-Agent Reasoning Applied**\n"
            f"Ran 6 parallel agents to analyze this decision from multiple perspectives.\n\n"
            f"{formatted_output}"
        )

        # Return as additionalContext
        output = {
            "additionalContext": user_header
        }
        # Add stats in debug mode
        if os.environ.get("MULTI_AGENT_DEBUG") == "true":
            output["_debug"] = {"stats": filter_stats}
        print(json.dumps(output))
    else:
        # No agent outputs - pass through
        if os.environ.get("MULTI_AGENT_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "result": "no_outputs"}}))
        else:
            print("{}")

    return 0


if __name__ == "__main__":
    main()
