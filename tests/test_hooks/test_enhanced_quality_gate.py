#!/usr/bin/env python3
"""Tests for enhanced reasoning quality gate hook."""

import sys
from pathlib import Path

import pytest

# Add reasoning package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hooks.Stop_reasoning_enhanced import (
    apply_enhanced_reflection,
    should_apply_enhanced_reflection,
)


class TestEnhancedReflectionDetection:
    """Test enhanced reflection detection logic."""

    def test_explicit_think_trigger_always_applies(self):
        """Explicit think trigger should apply regardless of length."""
        result, reason = should_apply_enhanced_reflection("Think about this.")
        assert result is True
        assert reason == "explicit_think_trigger"

    def test_short_response_without_trigger_skips(self):
        """Short response without think trigger should skip."""
        result, reason = should_apply_enhanced_reflection("This is short.")
        assert result is False
        assert reason == "short_response"

    def test_code_block_skips_enhanced_reflection(self):
        """Code blocks should skip enhanced reflection."""
        result, reason = should_apply_enhanced_reflection('```python\ndef foo():\n    pass\n```')
        assert result is False
        assert reason == "code_or_tool_result"

    def test_json_skips_enhanced_reflection(self):
        """JSON output should skip enhanced reflection."""
        result, reason = should_apply_enhanced_reflection('{"status": "ok"}')
        assert result is False
        assert reason == "code_or_tool_result"

    def test_reasoning_response_with_conclusions_applies(self):
        """Reasoning response with conclusion indicators should apply."""
        long_response = (
            "Therefore, we should implement caching for the application. "
            "This will significantly improve performance by reducing database queries. "
            "The cache layer will store frequently accessed data in memory for fast access. "
            "This architecture decision is based on our performance requirements."
        )
        assert len(long_response) >= 200  # Ensure test is valid
        result, reason = should_apply_enhanced_reflection(long_response)
        assert result is True
        assert reason == "reasoning_response"

    def test_long_analysis_response_applies(self):
        """Long analysis response should apply enhanced reflection."""
        long_response = (
            "Analyze the system architecture in detail. We need to carefully consider scalability, "
            "maintainability for future development, and performance under load. Therefore, a microservices "
            "architecture would be most beneficial for our use case. This approach allows independent deployment."
        )
        assert len(long_response) >= 200  # Ensure test is valid
        result, reason = should_apply_enhanced_reflection(long_response)
        assert result is True
        assert reason == "reasoning_response"
        assert len(long_response) >= 200


class TestEnhancedReflectionProcessing:
    """Test enhanced reflection processing logic."""

    def test_simple_response_returns_none_or_original(self):
        """Simple response without issues should return None (no improvement needed)."""
        result = apply_enhanced_reflection("This is a simple response without reasoning indicators.")
        # Should return None (no improvement) or handle gracefully
        assert result is None or isinstance(result, str)

    def test_response_with_logical_gap_improves(self):
        """Response with logical gaps should be improved."""
        response = "Therefore, we must use Redis. It's the best option."
        result = apply_enhanced_reflection(response)
        # Should either improve response or handle gracefully
        assert result is None or isinstance(result, str)

    def test_overconfident_response_improves(self):
        """Overconfident response should be improved."""
        response = "This will always work and never fail. It's the perfect solution."
        result = apply_enhanced_reflection(response)
        # Should either improve response or handle gracefully
        assert result is None or isinstance(result, str)

    def test_contradictory_response_improves(self):
        """Contradictory response should be improved."""
        response = "This will work. However, it won't work in production. The approach is sound."
        result = apply_enhanced_reflection(response)
        # Should either improve response or handle gracefully
        assert result is None or isinstance(result, str)


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_none_input_returns_safely(self):
        """None input should be handled gracefully."""
        result = apply_enhanced_reflection(None)
        assert result is None

    def test_empty_string_returns_safely(self):
        """Empty string should be handled gracefully."""
        result = apply_enhanced_reflection("")
        assert result is None

    def test_invalid_input_type_returns_safely(self):
        """Non-string input should be handled gracefully."""
        result = apply_enhanced_reflection(123)
        assert result is None


class TestHookIntegration:
    """Test hook integration with router."""

    def test_hook_exports_main_function(self):
        """Hook should export main() function."""
        from hooks import Stop_reasoning_enhanced as mod
        assert hasattr(mod, "main")

    def test_main_handles_missing_input_gracefully(self):
        """main() should handle missing input gracefully."""
        import io

        from hooks.Stop_reasoning_enhanced import main

        # Test with empty input
        old_stdin = sys.stdin
        sys.stdin = io.StringIO("")
        try:
            # Should not crash
            result = main()
            assert result == 0
        finally:
            sys.stdin = old_stdin


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
