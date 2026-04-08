#!/usr/bin/env python3
"""Tests for conflict arbiter module."""

import sys
from dataclasses import dataclass
from pathlib import Path

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "hooks"))

from UserPromptSubmit_modules.conflict_arbiter import (
    _LIGHTWEIGHT_ENHANCERS,
    resolve_conflict,
)


@dataclass(frozen=True)
class MockEnhancer:
    """Mock enhancer for testing."""

    name: str
    injection: str
    topics: list[str]


def test_fast_mode_gating():
    """Test that fast mode reduces cognitive enhancers to lightweight ones only."""
    # Create 5 mock enhancers (2 lightweight, 3 others)
    enhancers = [
        MockEnhancer("assumption_surfacing", "injection1", ["implementation"]),
        MockEnhancer("outcome_anchoring", "injection2", ["implementation"]),
        MockEnhancer("inversion_prompting", "injection3", ["implementation"]),
        MockEnhancer("chestertons_fence", "injection4", ["implementation"]),
        MockEnhancer("calibrated_confidence", "injection5", ["diagnostic"]),
    ]

    result = resolve_conflict(
        enhancers=enhancers,
        mode_selection="sequential",
        reasoning_confidence=2,
        prompt_mode="fast",
        token_limit=500,
    )

    # Should keep only lightweight enhancers (assumption_surfacing, outcome_anchoring)
    assert len(result.enhancers) == 2, f"Expected 2 enhancers, got {len(result.enhancers)}"
    assert result.enhancers[0].name in _LIGHTWEIGHT_ENHANCERS
    assert result.enhancers[1].name in _LIGHTWEIGHT_ENHANCERS
    assert "Fast mode" in result.rationale


def test_high_confidence_override():
    """Test that high-confidence reasoning mode overrides cognitive selections."""
    # Create 5 mock enhancers
    enhancers = [
        MockEnhancer(f"enhancer_{i}", f"injection{i}", ["implementation"])
        for i in range(5)
    ]

    result = resolve_conflict(
        enhancers=enhancers,
        mode_selection="multi_agent",
        reasoning_confidence=3,  # High confidence
        prompt_mode=None,
        token_limit=500,
    )

    # Should reduce to 2 enhancers due to high-confidence reasoning mode
    assert len(result.enhancers) == 2, f"Expected 2 enhancers, got {len(result.enhancers)}"
    assert "High-confidence reasoning mode" in result.rationale
    assert result.mode_selection == "multi_agent"


def test_token_budget_enforcement():
    """Test that token budget cap reduces enhancers when needed."""
    # Create 10 mock enhancers (would exceed 500 token limit)
    enhancers = [
        MockEnhancer(f"enhancer_{i}", f"injection{i}", ["implementation"])
        for i in range(10)
    ]

    result = resolve_conflict(
        enhancers=enhancers,
        mode_selection="sequential",  # Adds ~50 tokens
        reasoning_confidence=2,
        prompt_mode=None,
        token_limit=300,  # Low limit to trigger cap
    )

    # 10 enhancers * 100 = 1000 tokens, + 50 for mode = 1050
    # Limit 300 - 50 = 250, /100 = 2.5 → 2 enhancers max
    assert len(result.enhancers) <= 2, f"Expected ≤2 enhancers, got {len(result.enhancers)}"
    assert "Token budget cap" in result.rationale
    assert result.token_budget_applied is True


def test_no_conflicts():
    """Test that no conflicts are detected when selections are compatible."""
    enhancers = [
        MockEnhancer("assumption_surfacing", "injection1", ["implementation"]),
        MockEnhancer("outcome_anchoring", "injection2", ["implementation"]),
    ]

    result = resolve_conflict(
        enhancers=enhancers,
        mode_selection="sequential",
        reasoning_confidence=2,
        prompt_mode=None,
        token_limit=500,
    )

    # Should keep all enhancers
    assert len(result.enhancers) == 2
    assert result.mode_selection == "sequential"
    assert result.rationale == "No conflicts detected"
    assert result.token_budget_applied is False


def test_empty_enhancers():
    """Test that empty enhancer list is handled correctly."""
    result = resolve_conflict(
        enhancers=[],
        mode_selection="sequential",
        reasoning_confidence=2,
        prompt_mode=None,
        token_limit=500,
    )

    assert len(result.enhancers) == 0
    assert result.mode_selection == "sequential"
    assert result.rationale == "No conflicts detected"


def test_no_mode_selection():
    """Test that absence of mode selection is handled correctly."""
    enhancers = [
        MockEnhancer("assumption_surfacing", "injection1", ["implementation"]),
    ]

    result = resolve_conflict(
        enhancers=enhancers,
        mode_selection=None,
        reasoning_confidence=0,
        prompt_mode=None,
        token_limit=500,
    )

    assert len(result.enhancers) == 1
    assert result.mode_selection is None
    assert result.rationale == "No conflicts detected"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
