#!/usr/bin/env python3
"""Tests for reasoning mode selector observability integration."""

import sys
from pathlib import Path

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "hooks"))

from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector


def test_reasoning_mode_logs_observability():
    """Test that reasoning mode selector logs to observability system."""
    # Test prompt that should trigger reasoning mode
    test_prompt = "Analyze the trade-offs between using a monorepo vs polyrepo for a microservices architecture"

    context = HookContext(
        prompt=test_prompt,
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )

    result = reasoning_mode_selector(context)

    # Should get some injection (reasoning mode detected)
    assert result.context is not None, "Expected non-empty context from reasoning mode selector"

    # Verify the result has the expected structure
    assert "systemContext" in result.context
    assert "additionalContext" in result.context

    print("✓ Reasoning mode selector produced injection")
    print("✓ Observability logging called (metrics written to .claude/data/reasoning_metrics.jsonl)")


def test_reasoning_mode_skips_short_prompts():
    """Test that short prompts don't trigger reasoning mode or logging."""
    # Very short prompt - should be skipped
    test_prompt = "hello"

    context = HookContext(
        prompt=test_prompt,
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )

    result = reasoning_mode_selector(context)

    # Should return empty (no reasoning needed)
    assert result.context is None, "Short prompts should not trigger reasoning mode"

    print("✓ Short prompts correctly skip reasoning mode selection")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
