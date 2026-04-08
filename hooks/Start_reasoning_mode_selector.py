#!/usr/bin/env python3
"""Start hook: Reasoning mode selector.

Analyzes user queries to determine optimal reasoning mode:
- Sequential: Step-by-step analysis
- Multi-Agent: Multiple perspectives for complex decisions
- Graph: Branching exploration of alternatives
- Two-Stage: Separate reasoning and implementation phases

Registers with UserPromptSubmit router to inject selected mode into context.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


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



def analyze_query(query: str | None) -> dict[str, Any]:
    """Analyze query to determine optimal reasoning mode.

    Args:
        query: User query string (may be None or non-string)

    Returns:
        Dictionary with:
        - mode: Selected reasoning mode ('sequential', 'multi_agent', 'graph', 'two_stage')
        - confidence: Number of matching keywords (0-N)
        - reasoning_required: Whether complex reasoning is needed
    """
    # Default safe values
    if not query or not isinstance(query, str):
        return {
            "mode": "sequential",
            "confidence": 0,
            "reasoning_required": False
        }

    # Complexity indicators for each mode
    # Using regex patterns with word boundaries for flexible matching
    complexity_indicators = {
        'multi_agent': [
            r'\balternatives\b', r'\bcompare\b', r'\bvs\b', r'\bversus\b',
            r'should we use', r'trade-off', r'better option', r'decision between',
            r'\bor\b', r'\bprefer\b'
        ],
        'sequential': [
            r'how to', r'step by step', r'\bapproach\b', r'\bexplain\b',
            r'\bunderstand\b', r'\bdescribe\b', r'\boverview\b', r'\bsummary\b'
        ],
        'graph': [
            r'\bexplore\b', r'\bbranches\b', r'multiple paths', r'what if',
            r'\bscenarios\b', r'consider options', r'alternatives for', r'\bbranch\b'
        ],
        'two_stage': [
            r'write\s+\w*\s*function', r'create class', r'implement a', r'code to',
            r'develop a', r'build a', r'create\s+\w*\s*function'
        ]
    }

    # Score each mode by keyword matches (using regex with word boundaries)
    query_lower = query.lower()
    scores = {}

    for mode, patterns in complexity_indicators.items():
        score = sum(1 for pattern in patterns if re.search(pattern, query_lower))
        scores[mode] = score

    # Select highest-scoring mode, default to sequential
    if scores and max(scores.values()) > 0:
        best_mode = max(scores, key=scores.get)
        confidence = scores[best_mode]
    else:
        best_mode = "sequential"
        confidence = 0

    # Determine if reasoning is required
    # Very short queries or low confidence don't need special reasoning
    reasoning_required = (
        len(query) > 20 and  # Has minimal substance
        confidence > 0  # Has clear complexity indicators
    )

    return {
        "mode": best_mode,
        "confidence": confidence,
        "reasoning_required": reasoning_required
    }


def process_prompt(data: dict) -> dict:
    """Process prompt and inject reasoning mode into context.

    Args:
        data: Dictionary with 'query' field (user's prompt)

    Returns:
        Dictionary with 'additionalContext' to inject selected mode

    Example:
        >>> data = {"query": "Should we use Redis or Memcached?"}
        >>> result = process_prompt(data)
        >>> assert result["additionalContext"].startswith("Reasoning mode: multi_agent")
    """
    try:
        query = data.get("query", "")
        result = analyze_query(query)

        # Confidence threshold: skip low-confidence selections
        confidence_threshold = 2
        if result["confidence"] < confidence_threshold:
            return {}  # Skip injection, fail silent

        # Inject reasoning mode into context
        mode_name = result["mode"]
        confidence = result["confidence"]

        # Map mode names to tags
        # Note: [GRA] is used for graph mode to avoid collision with [COG]
        # which is reserved for cognitive frameworks (cognitive_enhancers.py)
        mode_tags = {
            "sequential": "[SEQ]",
            "multi_agent": "[MAS]",
            "graph": "[GRA]",  # Graph Reasoning Alternative (avoid [COG] collision)
            "two_stage": "[2ST]"
        }
        tag = mode_tags.get(mode_name, "[SEQ]")

        context = (
            f"Reasoning mode: {mode_name}\n"
            f"Confidence: {confidence}/4\n"
            f"Using {mode_name} reasoning approach for this query.\n\n"
            f"**TAG EMISSION REQUIRED**: Begin your response with '{tag}' tag "
            f"to indicate the active reasoning mode. This provides visibility into "
            f"which reasoning approach is being used."
        )

        return {
            "additionalContext": context,
            "tokens": len(context.split())
        }

    except Exception as e:
        # Fail open - don't break on errors
        print(f"[Start_reasoning_mode_selector] Error: {e}", file=sys.stdout)
        return {}


if __name__ == "__main__":
    # For manual testing
    import sys

    test_input = json.loads(sys.stdin.read())
    result = process_prompt(test_input)
    print(json.dumps(result))
