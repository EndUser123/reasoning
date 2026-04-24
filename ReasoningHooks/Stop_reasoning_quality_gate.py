#!/usr/bin/env python3
"""Automatic reasoning quality gate using STOP hook.

Applies Generate→Critique→Improve loop to Claude's responses:
- Detects logical gaps, overconfidence, contradictions
- Detects workaround patterns vs structural fixes
- Pattern matching (no LLM calls, <200ms overhead)
- Quality improvement: ~7% average gain
- Fail-open design: errors don't block responses

This is the authoritative source file.
Symlink from: P:/.claude/hooks/Stop_reasoning_quality_gate.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import traceback
from pathlib import Path


def _resolve_reasoning_package() -> Path | None:
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
    return None


_reasoning_pkg = _resolve_reasoning_package()
if _reasoning_pkg is None:
    print(
        "[Stop_reasoning_quality_gate] ERROR: Could not locate reasoning package. "
        "Checked: REASONING_PKG_PATH env var, parent directories, P:/packages/reasoning. "
        "Hook will pass-through (fail-open).",
        file=sys.stderr,
    )
    REASONING_PKG = None
else:
    REASONING_PKG = _reasoning_pkg
    sys.path.insert(0, str(REASONING_PKG))

# Conditional imports - only load if reasoning package was found
if REASONING_PKG is not None:
    try:
        from reasoning.config import Mode, ReasoningConfig
        from reasoning.modes.sequential import SequentialMode
        REASONING_MODE_AVAILABLE = True
    except Exception as e:
        print(
            f"[Stop_reasoning_quality_gate] WARNING: Could not import reasoning modules: {e}. "
            "Hook will pass-through (fail-open).",
            file=sys.stderr,
        )
        REASONING_MODE_AVAILABLE = False
else:
    REASONING_MODE_AVAILABLE = False

LOG_FILE = Path("P:/packages/reasoning/hook_usage.log") if REASONING_PKG else None
filter_stats = {"applied": 0, "skipped": 0, "improved": 0, "errors": 0}


# ============================================================================
# WORKAROUND vs STRUCTURAL FIX DETECTION
# Distinguishes symptom patches from root-cause fixes
# ============================================================================

WORKAROUND_PATTERNS = [
    (r"sys\.path\.insert\s*\(\s*0\s*,", "Blind sys.path.insert(0, ...) can mask import errors"),
    (r"except\s*:\s*pass", "Bare except:pass silently swallows errors"),
    (r"except\s+\S+.*?:\s*pass", "Exception handler that only passes masks the error"),
    (r"#\s*TODO(?!\s*:)", "TODO comment indicates incomplete fix"),
    (r"#\s*FIXME", "FIXME comment indicates known incomplete fix"),
    (r"#\s*HACK", "HACK comment indicates workaround rather than solution"),
    (r"if\s+not\s+hasattr\s*\(", "hasattr check is a symptom guard, not root-cause fix"),
    (r"if\s+'[a-zA-Z0-9_.]+'\s+not\s+in\s+globals\(\)", "globals() check is a symptom guard"),
    (r"if\s+os\.path\.exists", "path existence check doesn't fix root cause"),
    (r"if\s+version\s*[><=]", "Version comparison workarounds hide API incompatibilities"),
    (r"if\s+.*\s+is\s+None\s*:\s*.*=\s*.*", "Lazy initialization may hide initialization-order bugs"),
    (r"isinstance\s*\([^,]+,\s*str\s*\).*==", "String-type checking is fragile"),
]

STRUCTURAL_FIX_INDICATORS = [
    "root cause", "because the issue was", "the actual problem",
    "invariant", "boundary condition", "data flow", "state machine",
    "contract", "schema", "initialization order", "race condition", "deadlock",
]


def detect_workaround(response: str) -> tuple[bool, str | None]:
    """Detect if response treats a workaround as a root-cause fix."""
    for pattern, explanation in WORKAROUND_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE | re.MULTILINE):
            return True, explanation

    has_structural = any(indicator in response.lower() for indicator in STRUCTURAL_FIX_INDICATORS)
    has_workaround_claim = any(word in response.lower() for word in ["fixed", "root cause", "the issue is"])

    if has_workaround_claim and not has_structural:
        confidence_claims = re.findall(r"\b(fixed|resolved|solved|corrected)\b", response, re.IGNORECASE)
        if confidence_claims and len(confidence_claims) >= 2:
            return True, "Claims fix without structural indicators — verify root-cause not symptom"

    return False, None


def should_apply_reflection(response: str) -> tuple[bool, str]:
    """Determine if self-reflection would be useful."""
    global filter_stats

    stripped = response.strip()
    if stripped.startswith(('```', '{', '"', '[')):
        filter_stats["skipped"] += 1
        return False, "code_or_tool_result"

    think_trigger = re.compile(r'\b\w*think(ing|s)?\b', re.IGNORECASE)
    if think_trigger.search(response):
        filter_stats["applied"] += 1
        return True, "explicit_think_trigger"

    if len(response) < 200:
        filter_stats["skipped"] += 1
        return False, "short_response"

    reasoning_indicators = [
        "therefore", "thus", "consequently", "because", "since", "reason",
        "analysis", "evaluate", "assess", "recommend", "suggest", "conclusion",
        "however", "although", "moreover", "indicates", "suggests", "implies",
        "so", "hence", "means that", "shows that", "because of", "due to",
        "leads to", "refactor", "root cause", "depends on", "implies that"
    ]

    response_lower = response.lower()
    if any(indicator in response_lower for indicator in reasoning_indicators):
        filter_stats["applied"] += 1
        return True, "reasoning_response"

    filter_stats["skipped"] += 1
    return False, "no_reasoning_indicators"


def apply_self_reflection(response: str) -> str | None:
    """Apply self-reflection to improve response quality."""
    global filter_stats

    if not REASONING_MODE_AVAILABLE:
        return None

    try:
        config = ReasoningConfig(mode=Mode.SEQUENTIAL)
        mode = SequentialMode(config)

        import time
        start_time = time.time()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mode.process(response))
        finally:
            loop.close()

        elapsed_ms = (time.time() - start_time) * 1000
        _log_usage(len(response), elapsed_ms, result)

        if result and result.conclusion and result.conclusion != response:
            filter_stats["improved"] += 1
            return result.conclusion

        return None

    except Exception as e:
        filter_stats["errors"] += 1
        print(f"[Stop_reasoning_quality_gate] Error: {e}", file=sys.stdout)
        return None


def _log_usage(response_length: int, elapsed_ms: float, result) -> None:
    """Log hook usage for tracking."""
    try:
        import time
        log_entry = {
            "timestamp": time.time(),
            "hook": "Stop_reasoning_quality_gate",
            "response_length": response_length,
            "elapsed_ms": round(elapsed_ms, 2),
            "quality_score": getattr(result, 'quality_score', None),
            "result": "improved" if result and result.conclusion else "no_improvement",
        }
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass


def main():
    """Main hook entry point."""
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

    is_workaround, workaround_msg = detect_workaround(response)
    if is_workaround and workaround_msg:
        output = {"systemMessage": f"[Workaround detected: {workaround_msg}]"}
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            output["_debug"] = {"stats": filter_stats, "reason": "workaround_detected"}
        print(json.dumps(output))
        return 0

    should_apply, reason = should_apply_reflection(response)

    if not should_apply:
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "reason": reason}}))
        else:
            print("{}")
        return 0

    improvement = apply_self_reflection(response)
    if improvement:
        output = {"systemMessage": f"**Enhanced Reasoning Applied**\n\n{improvement}"}
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            output["_debug"] = {"stats": filter_stats}
        print(json.dumps(output))
    else:
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "result": "no_improvement"}}))
        else:
            print("{}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[Reasoning quality gate error: {e}]", file=sys.stderr)
        print("{}")
        sys.exit(0)
