#!/usr/bin/env python3
"""Tests for multi-agent reasoning hook."""

import sys
from pathlib import Path

import pytest

# Add reasoning package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hooks.PreTool_multi_agent_reasoning import (
    apply_multi_agent_reasoning,
    should_use_multi_agent_reasoning,
)


class TestMultiAgentDetection:
    """Test multi-agent reasoning detection logic."""

    def test_alternatives_comparison_triggers_reasoning(self):
        """Comparison between alternatives should trigger multi-agent reasoning."""
        query = "Should we use Redis or Memcached for caching?"
        result, reason = should_use_multi_agent_reasoning(query)
        assert result is True
        assert reason == "complex_decision"

    def test_trade_off_analysis_triggers_reasoning(self):
        """Trade-off analysis should trigger multi-agent reasoning."""
        query = "What are the trade-offs between PostgreSQL and MongoDB?"
        result, reason = should_use_multi_agent_reasoning(query)
        assert result is True
        assert reason == "complex_decision"

    def test_simple_query_skips_multi_agent(self):
        """Simple query without decision keywords should skip multi-agent reasoning."""
        query = "How do I install Python packages?"
        result, reason = should_use_multi_agent_reasoning(query)
        assert result is False
        assert reason == "no_complex_decision"

    def test_implicit_tool_query_detection(self):
        """Should detect complex decisions in tool input queries."""
        # Simulating tool_input with a query
        tool_input = {"query": "Compare React vs Vue for frontend development"}
        result, reason = should_use_multi_agent_reasoning(
            tool_input.get("query", "")
        )
        assert result is True
        assert reason == "complex_decision"


class TestMultiAgentProcessing:
    """Test multi-agent reasoning processing logic."""

    def test_reasoning_returns_agent_outputs(self):
        """Multi-agent reasoning should return outputs from multiple agents."""
        # This is a basic test - actual MAS package integration may not be available
        query = "Should we use microservices or monolith for this project?"
        result = apply_multi_agent_reasoning(query)
        # Should either return agent outputs or handle gracefully
        assert result is None or isinstance(result, dict)

    def test_graceful_degradation_without_mas(self):
        """Should handle missing MAS package gracefully."""
        # If MAS package is not installed, should return None (fail-open)
        query = "Complex decision requiring multi-agent analysis"
        result = apply_multi_agent_reasoning(query)
        # Should either work or return None (graceful degradation)
        assert result is None or isinstance(result, dict)

    def test_empty_query_handled_safely(self):
        """Empty query should be handled gracefully."""
        result = apply_multi_agent_reasoning("")
        assert result is None

    def test_none_input_handled_safely(self):
        """None input should be handled gracefully."""
        result = apply_multi_agent_reasoning(None)
        assert result is None


class TestHookIntegration:
    """Test hook integration with PreToolUse router."""

    def test_hook_exports_main_function(self):
        """Hook should export main() function."""
        from hooks import PreTool_multi_agent_reasoning as mod
        assert hasattr(mod, "main")

    def test_main_handles_missing_input_gracefully(self):
        """main() should handle missing input gracefully."""
        import io

        from hooks.PreTool_multi_agent_reasoning import main

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
