"""Tests for hypothesis_as_fact_detector.py.

RED Phase: These tests MUST fail before implementation.
Run with: pytest tests/anti_sycophancy/test_hypothesis_as_fact_detector.py -v
"""

from reasoning.anti_sycophancy.hypothesis_as_fact_detector import (
    HypothesisFactPattern,
    detect_hypothesis_as_fact,
)


class TestBrokenJunctionDetection:
    """Tests for detecting broken-junction-style sentences."""

    def test_broken_junction_with_if(self):
        """Test that 'if X, then Y' pattern is detected."""
        text = "If the user has permission, they can access the resource."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hypothesis is True
        assert result.pattern == HypothesisFactPattern.BROKEN_JUNCTION

    def test_broken_junction_with_assuming(self):
        """Test that 'assuming X, Y' pattern is detected."""
        text = "Assuming the connection is stable, we proceed with upload."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hypothesis is True
        assert result.pattern == HypothesisFactPattern.BROKEN_JUNCTION

    def test_broken_junction_with_given(self):
        """Test that 'given X, Y' pattern is detected."""
        text = "Given the dataset is clean, we can train the model."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hypothesis is True
        assert result.pattern == HypothesisFactPattern.BROKEN_JUNCTION


class TestRuleAssertionDetection:
    """Tests for detecting rule assertions."""

    def test_rule_assertion_always(self):
        """Test that 'always X' pattern is detected."""
        text = "This function always returns an integer."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hypothesis is True
        assert result.pattern == HypothesisFactPattern.RULE_ASSERTION

    def test_rule_assertion_never(self):
        """Test that 'never X' pattern is detected."""
        text = "This method never raises exceptions."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hypothesis is True
        assert result.pattern == HypothesisFactPattern.RULE_ASSERTION

    def test_rule_assertion_every(self):
        """Test that 'every X' pattern is detected."""
        text = "Every request must include authentication."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hypothesis is True
        assert result.pattern == HypothesisFactPattern.RULE_ASSERTION


class TestHedgeFlagSetting:
    """Tests for correct has_hedge flag setting."""

    def test_hedged_variant_sets_flag_true(self):
        """Test that hedged sentences set has_hedge=True."""
        text = "The function typically returns an integer."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hedge is True

    def test_unhedged_variant_sets_flag_false(self):
        """Test that unhedged sentences set has_hedge=False."""
        text = "The function returns an integer."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hedge is False

    def test_uncertainty_markers_set_hedge_true(self):
        """Test that uncertainty markers trigger hedge detection."""
        text = "The API probably returns a 200 status code."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hedge is True

    def test_confident_statements_set_hedge_false(self):
        """Test that confident statements have has_hedge=False."""
        text = "The API returns a 200 status code on success."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hedge is False


class TestNegativeCases:
    """Tests for sentences that should NOT be flagged."""

    def test_simple_statement_without_hypothesis(self):
        """Test that simple factual statements are not flagged."""
        text = "The function returns a string."
        result = detect_hypothesis_as_fact(text)
        assert result.has_hypothesis is False
        assert result.pattern is None

    def test_genuine_question_not_flagged(self):
        """Test that questions are not flagged."""
        text = "What does this function return?"
        result = detect_hypothesis_as_fact(text)
        assert result.has_hypothesis is False
        assert result.pattern is None
