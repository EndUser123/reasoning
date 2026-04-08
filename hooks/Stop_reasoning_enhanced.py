#!/usr/bin/env python3
"""Enhanced Stop hook: Reasoning quality gate with full thought chain.

Extends the basic quality gate to use the complete Generate → Critique → Improve loop:
- Creates proper 5-stage thought chain (not just single conclusion)
- Returns improved response if quality gate fails
- Maintains <200ms performance target
- Fail-open design: errors don't block responses

Registers with Stop router to inject reasoning improvements into context.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
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
from reasoning.modes.sequential import SequentialMode

# Usage logging
LOG_FILE = REASONING_PKG / "hook_usage.log"

# Performance statistics (in-memory, per-session)
filter_stats = {"applied": 0, "skipped": 0, "improved": 0, "errors": 0}


def should_apply_enhanced_reflection(response: str) -> tuple[bool, str]:
    """Determine if enhanced reflection should be applied.

    Returns:
        (should_apply, reason) tuple

    Apply to responses that:
    - Use explicit "think" trigger (case-insensitive, any length)
    - Are longer than 200 chars (substantial content)
    - Contain reasoning/analysis indicators
    - Are not just tool results or code
    """
    global filter_stats

    # Skip tool results and code
    stripped = response.strip()
    if stripped.startswith(('```', '{', '"', '[')):
        filter_stats["skipped"] += 1
        return False, "code_or_tool_result"

    # Explicit "think" trigger (highest priority, bypasses length check)
    think_trigger = __import__('re').compile(r'\b\w*think(ing|s)?\b', __import__('re').IGNORECASE)
    if think_trigger.search(response):
        filter_stats["applied"] += 1
        return True, "explicit_think_trigger"

    # Skip short responses for other checks
    if len(response) < 200:
        filter_stats["skipped"] += 1
        return False, "short_response"

    # Apply to reasoning/analysis responses (same 25 keywords as basic gate)
    reasoning_indicators = [
        # Conclusions
        "therefore", "thus", "consequently",
        # Causality
        "because", "since", "reason",
        # Analysis
        "analysis", "evaluate", "assess",
        # Recommendations
        "recommend", "suggest", "conclusion",
        # Contrast
        "however", "although", "moreover",
        # Inference
        "indicates", "suggests", "implies",
        # Conversational reasoning
        "so", "hence", "means that", "shows that",
        # Causality variants
        "because of", "due to", "leads to",
        # Technical reasoning
        "refactor", "root cause", "depends on", "implies that"
    ]

    response_lower = response.lower()
    if any(indicator in response_lower for indicator in reasoning_indicators):
        filter_stats["applied"] += 1
        return True, "reasoning_response"

    filter_stats["skipped"] += 1
    return False, "no_reasoning_indicators"


def apply_enhanced_reflection(response: str) -> str | None:
    """Apply enhanced self-reflection with full thought chain.

    Uses the complete Generate → Critique → Improve loop:
    1. Generate initial 5-stage thought chain
    2. Self-critique (analysis mode)
    3. Refine based on critique
    4. Quality gate (<1 issue = pass)
    5. Return improved response or original

    Args:
        response: The response text to enhance

    Returns:
        Improved response string if quality improved, None otherwise
    """
    try:
        config = ReasoningConfig(mode=Mode.SEQUENTIAL)
        mode = SequentialMode(config)

        # Run the full async reasoning process synchronously
        # This creates a proper 5-stage thought chain and applies self-reflection
        import time
        start_time = time.time()

        # Run async process in sync context (hooks must be synchronous)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mode.process(response))
        finally:
            loop.close()

        elapsed_ms = (time.time() - start_time) * 1000

        # Log usage with timing
        _log_usage(len(response), elapsed_ms, result)

        # Check if response was improved
        if result and result.conclusion and result.conclusion != response:
            # Response was improved through reasoning
            filter_stats["improved"] += 1
            return result.conclusion

        # No improvement or processing failed
        return None

    except Exception as e:
        # Fail open - don't block on errors
        filter_stats["errors"] += 1
        print(f"[Stop_reasoning_enhanced] Error: {e}", file=sys.stdout)
        return None


def _log_usage(response_length: int, elapsed_ms: float, result) -> None:
    """Log hook usage for tracking."""
    try:
        import time
        log_entry = {
            "timestamp": time.time(),
            "hook": "Stop_reasoning_enhanced",
            "response_length": response_length,
            "elapsed_ms": round(elapsed_ms, 2),
            "quality_score": getattr(result, 'quality_score', None),
            "result": "improved" if result and result.conclusion else "no_improvement",
        }
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Don't fail on logging errors


def main():
    """Main hook entry point."""
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
    if not response:
        print("{}")
        return 0

    # Check if we should apply enhanced reflection
    should_apply, reason = should_apply_enhanced_reflection(response)
    if not should_apply:
        # Debug mode: include stats even when skipping
        if os.environ.get("ENHANCED_REFLECTION_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "reason": reason}}))
        else:
            print("{}")
        return 0

    # Apply enhanced reflection
    improved_response = apply_enhanced_reflection(response)
    if improved_response:
        # Return system message with improved response
        output = {
            "systemMessage": f"**🔄 Enhanced Reasoning Applied**\n\nResponse improved through Generate → Critique → Improve loop.\n\n{improved_response}"
        }
        # Add stats in debug mode
        if os.environ.get("ENHANCED_REFLECTION_DEBUG") == "true":
            output["_debug"] = {"stats": filter_stats}
        print(json.dumps(output))
    else:
        # No improvement - pass through
        if os.environ.get("ENHANCED_REFLECTION_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "result": "no_improvement"}}))
        else:
            print("{}")


if __name__ == "__main__":
    main()
