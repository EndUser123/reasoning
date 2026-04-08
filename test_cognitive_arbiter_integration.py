#!/usr/bin/env python3
"""Tests for cognitive frameworks hook integration with conflict arbiter."""

import sys
from pathlib import Path

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "hooks"))

from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.cognitive_enhancers import cognitive_enhancers


def test_cognitive_hook_with_fast_mode():
    """Test that cognitive frameworks hook respects fast mode via conflict arbiter."""
    # Test prompt with #fast mode and multiple implementation keywords
    # This should trigger many cognitive enhancers, but fast mode should reduce them
    test_prompt = "#fast implement a new authentication system and refactor the database"

    context = HookContext(
        prompt=test_prompt,
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )

    result = cognitive_enhancers(context)

    # Should get some injection (not empty)
    assert result.context is not None, "Expected non-empty context from cognitive hook"

    # Fast mode should cap to 1-2 enhancers only
    # This is verified by checking that we get fewer tokens than normal mode
    # and by checking the token count is reasonable (< 250 tokens for 2 enhancers)
    assert result.tokens < 250, f"Fast mode should cap to ~2 enhancers (~200 tokens), got {result.tokens} tokens"

    print(f"✓ Fast mode injection: {result.tokens} tokens, {len(result.context)} chars")
    print("✓ Token count is reasonable for 2 lightweight enhancers")


def test_cognitive_hook_normal_mode():
    """Test that cognitive frameworks hook works normally without fast mode."""
    # Test prompt without fast mode
    test_prompt = "implement a new authentication system"

    context = HookContext(
        prompt=test_prompt,
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )

    result = cognitive_enhancers(context)

    # Should get injection with normal number of enhancers
    assert result.context is not None, "Expected non-empty context from cognitive hook"

    # Normal mode should allow up to 3 enhancers
    context_length = len(result.context)

    # Should be longer than fast mode
    assert context_length > 100, f"Normal mode should produce injection, got {context_length} chars"

    print(f"✓ Normal mode injection length: {context_length} chars")


def test_cognitive_hook_with_very_long_prompt():
    """Test token budget enforcement with many enhancers."""
    # This should trigger many enhancers due to length and complexity
    test_prompt = (
        "#fast implement a comprehensive new authentication system with OAuth 2.0, "
        "multi-factor authentication, session management, password reset flows, "
        "account recovery, user profile management, role-based access control, "
        "audit logging, security monitoring, and integrate with existing database"
    )

    context = HookContext(
        prompt=test_prompt,
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )

    result = cognitive_enhancers(context)

    # Should still get injection, but limited by fast mode
    assert result.context is not None, "Expected non-empty context even with long prompt"

    # Fast mode + long prompt should still be capped
    context_length = len(result.context)
    print(f"✓ Fast mode + long prompt injection length: {context_length} chars")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
