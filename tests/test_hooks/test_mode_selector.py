#!/usr/bin/env python3
"""Tests for reasoning mode selector hook."""

import sys
from pathlib import Path

import pytest

# Add reasoning package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hooks.Start_reasoning_mode_selector import analyze_query


class TestQueryAnalysis:
    """Test query analysis logic."""

    def test_simple_query_routes_to_sequential(self):
        """Simple queries should use sequential mode."""
        result = analyze_query("How to implement caching?")
        assert result["mode"] == "sequential"
        assert result["confidence"] >= 1
        assert result["reasoning_required"] is True

    def test_alternative_query_routes_to_multi_agent(self):
        """Queries with alternatives should use multi-agent mode."""
        result = analyze_query("Should we use Redis or Memcached?")
        assert result["mode"] == "multi_agent"
        assert result["confidence"] >= 1

    def test_exploration_query_routes_to_graph(self):
        """What-if exploration should use graph mode."""
        result = analyze_query("What if we tried microservices?")
        assert result["mode"] == "graph"
        assert result["confidence"] >= 1

    def test_implementation_query_routes_to_two_stage(self):
        """Implementation tasks should use two-stage mode."""
        result = analyze_query("Write a function to calculate hash")
        assert result["mode"] == "two_stage"
        assert result["confidence"] >= 1

    def test_short_query_defaults_to_sequential(self):
        """Short/unclear queries should default to sequential."""
        result = analyze_query("Help me debug this")
        assert result["mode"] == "sequential"
        assert result["reasoning_required"] is False  # Too short

    def test_empty_query_defaults_to_sequential(self):
        """Empty query should default to sequential."""
        result = analyze_query("")
        assert result["mode"] == "sequential"
        assert result["confidence"] == 0
        assert result["reasoning_required"] is False


class TestHookIntegration:
    """Test hook integration with router."""

    def test_hook_exports_process_function(self):
        """Hook should export process_prompt function."""
        from hooks import Start_reasoning_mode_selector as mod
        assert hasattr(mod, "process_prompt")

    def test_process_returns_dict_with_mode(self):
        """process_prompt should return dict with mode field."""
        from hooks.Start_reasoning_mode_selector import process_prompt

        data = {
            "query": "Should we use Redis or Memcached?"
        }

        result = process_prompt(data)
        assert isinstance(result, dict)
        assert "mode" in result or "additionalContext" in result

    def test_process_handles_missing_query_gracefully(self):
        """process_prompt should handle missing query field."""
        from hooks.Start_reasoning_mode_selector import process_prompt

        data = {}  # Missing query

        # Should not crash, should return empty or default
        result = process_prompt(data)
        assert isinstance(result, dict)


class TestModeSelection:
    """Test mode selection patterns."""

    complexity_indicators = {
        'multi_agent': ['alternatives', 'compare', 'vs', 'versus', 'should we use', 'trade-off'],
        'sequential': ['how to', 'step by step', 'approach', 'implement', 'design'],
        'graph': ['explore', 'branches', 'multiple paths', 'what if', 'scenarios'],
        'two_stage': ['code', 'implement', 'write function', 'create class'],
    }

    def test_multi_agent_keywords_detected(self):
        """Multi-agent keywords should be detected."""
        for keyword in self.complexity_indicators['multi_agent']:
            query = f"Should we use Redis or {keyword}?"
            result = analyze_query(query)
            if result["confidence"] > 0:  # Only check if keyword triggered
                assert result["mode"] == "multi_agent"

    def test_sequential_keywords_detected(self):
        """Sequential keywords should be detected."""
        for keyword in self.complexity_indicators['sequential']:
            query = f"{keyword} caching system"
            result = analyze_query(query)
            if result["confidence"] > 0:
                assert result["mode"] == "sequential"

    def test_graph_keywords_detected(self):
        """Graph keywords should be detected."""
        for keyword in self.complexity_indicators['graph']:
            query = f"What if we {keyword} microservices?"
            result = analyze_query(query)
            if result["confidence"] > 0:
                assert result["mode"] == "graph"

    def test_two_stage_keywords_detected(self):
        """Two-stage keywords should be detected."""
        for keyword in self.complexity_indicators['two_stage']:
            query = f"{keyword} a hash function"
            result = analyze_query(query)
            if result["confidence"] > 0:
                assert result["mode"] == "two_stage"


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_invalid_input_returns_default(self):
        """Invalid input should return safe defaults."""
        result = analyze_query(None)
        assert result["mode"] == "sequential"
        assert result["confidence"] == 0
        assert result["reasoning_required"] is False

    def test_non_string_input_converts(self):
        """Non-string input should be converted safely."""
        result = analyze_query(123)
        assert result["mode"] == "sequential"
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
