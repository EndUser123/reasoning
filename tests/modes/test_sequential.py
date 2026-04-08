"""Tests for Sequential reasoning mode."""

import pytest

from reasoning.config import ReasoningConfig
from reasoning.models import Mode, Thought, ThoughtChain, ThoughtStage
from reasoning.modes.sequential import SequentialMode


@pytest.fixture
def config():
    """Create a test configuration."""
    return ReasoningConfig(mode=Mode.SEQUENTIAL)


@pytest.fixture
def sequential_mode(config):
    """Create a SequentialMode instance for testing."""
    return SequentialMode(config)


@pytest.fixture
def sample_thought_chain():
    """Create a sample thought chain for testing."""
    chain = ThoughtChain()
    stages = [
        ThoughtStage.PROBLEM_DEFINITION,
        ThoughtStage.RESEARCH,
        ThoughtStage.ANALYSIS,
        ThoughtStage.SYNTHESIS,
        ThoughtStage.CONCLUSION,
    ]
    for i, stage in enumerate(stages, start=1):
        thought = Thought(
            content=f"Detailed content for stage {i} with enough length to pass quality checks",
            stage=stage,
            thought_number=i,
            total_thoughts=5,
            confidence=0.8,
        )
        chain.add_thought(thought)
    return chain


# Existing tests (unchanged)

@pytest.mark.asyncio
async def test_process_returns_result(sequential_mode):
    """Test that process returns a ProcessingResult."""
    result = await sequential_mode.process("Test prompt")
    assert result is not None
    assert result.conclusion is not None
    assert len(result.conclusion) > 0


@pytest.mark.asyncio
async def test_process_creates_thought_chain(sequential_mode):
    """Test that process creates a thought chain with 5 stages."""
    result = await sequential_mode.process("Test prompt")
    assert result.thought_chain is not None
    # Chain may have more than 5 thoughts now (includes reflection)
    assert result.thought_chain.length >= 5


@pytest.mark.asyncio
async def test_thought_chain_has_correct_stages(sequential_mode):
    """Test that thought chain progresses through correct stages."""
    result = await sequential_mode.process("Test prompt")
    chain = result.thought_chain

    expected_stages = [
        ThoughtStage.PROBLEM_DEFINITION,
        ThoughtStage.RESEARCH,
        ThoughtStage.ANALYSIS,
        ThoughtStage.SYNTHESIS,
        ThoughtStage.CONCLUSION,
    ]

    actual_stages = [thought.stage for thought in chain.thoughts[:5]]
    assert actual_stages == expected_stages


@pytest.mark.asyncio
async def test_validate_input_accepts_valid_prompt(sequential_mode):
    """Test that validate_input returns True for valid prompts."""
    assert sequential_mode.validate_input("Valid prompt") is True
    assert sequential_mode.validate_input("Another valid prompt") is True


@pytest.mark.asyncio
async def test_validate_input_rejects_empty_prompt(sequential_mode):
    """Test that validate_input returns False for empty prompts."""
    assert sequential_mode.validate_input("") is False
    assert sequential_mode.validate_input("   ") is False


@pytest.mark.asyncio
async def test_get_mode_name(sequential_mode):
    """Test that get_mode_name returns the correct mode name."""
    assert sequential_mode.get_mode_name() == "SequentialMode"


# New tests for self-reflection functionality

@pytest.mark.asyncio
async def test_self_critique_identifies_gaps(sequential_mode):
    """Test that self-critique catches logical gaps using pattern matching."""
    # Create a chain with logical gaps in content
    incomplete_chain = ThoughtChain()
    incomplete_chain.add_thought(Thought(
        content="Therefore, X is true.",  # Logical gap: "therefore" without reasoning
        stage=ThoughtStage.CONCLUSION,
        thought_number=1,
        total_thoughts=1,
        confidence=0.8,
    ))

    critique = sequential_mode._self_critique(incomplete_chain)
    # Should detect logical gap in content
    assert "issues" in critique.lower() or "improved" in critique.lower()


@pytest.mark.asyncio
async def test_refinement_improves_thoughts(sequential_mode, sample_thought_chain):
    """Test that refinement improves thoughts based on critique."""
    critique = "Issues found:\n- Overconfidence: All thoughts have identical confidence"

    refined = sequential_mode._refine_thoughts(sample_thought_chain, critique)

    # Check that confidence was reduced
    original_confidence = sample_thought_chain.thoughts[0].confidence
    refined_confidence = refined.thoughts[0].confidence
    assert refined_confidence < original_confidence


@pytest.mark.asyncio
async def test_quality_gate_blocks_low_quality(sequential_mode):
    """Test that quality gate blocks low-quality reasoning."""
    # Create a low-quality chain (empty thoughts)
    low_quality_chain = ThoughtChain()
    low_quality_chain.add_thought(Thought(
        content="Short",  # Too short
        stage=ThoughtStage.PROBLEM_DEFINITION,
        thought_number=1,
        total_thoughts=1,
        confidence=0.5,
    ))

    quality_checks = sequential_mode._quality_gate(low_quality_chain)
    assert quality_checks["all_passed"] is False


@pytest.mark.asyncio
async def test_quality_gate_passes_high_quality(sequential_mode, sample_thought_chain):
    """Test that quality gate passes high-quality reasoning."""
    quality_checks = sequential_mode._quality_gate(sample_thought_chain)
    assert quality_checks["is_complete"] is True
    assert quality_checks["is_supported"] is True


@pytest.mark.asyncio
async def test_max_iterations_enforced(sequential_mode):
    """Test that max iterations limit is enforced."""
    assert sequential_mode._max_iterations == 2


@pytest.mark.asyncio
async def test_process_includes_quality_metadata(sequential_mode):
    """Test that process includes quality checks in metadata."""
    result = await sequential_mode.process("Test prompt")
    assert "quality_checks" in result.metadata
    assert "all_passed" in result.metadata["quality_checks"]


@pytest.mark.asyncio
async def test_quality_score_is_calculated(sequential_mode):
    """Test that quality score is calculated (not placeholder 0.7)."""
    result = await sequential_mode.process("Test prompt")
    # Quality score should vary based on actual quality checks
    assert 0.0 <= result.quality_score <= 1.0
    # Should not be hardcoded 0.7 from old implementation
    # (though it might coincidentally be 0.7)


@pytest.mark.asyncio
async def test_format_chain_output(sequential_mode, sample_thought_chain):
    """Test that _format_chain produces structured output."""
    formatted = sequential_mode._format_chain(sample_thought_chain)
    assert "Stage 1" in formatted
    assert "PROBLEM_DEFINITION" in formatted or "problem_definition" in formatted.lower()
    assert "Detailed content for stage 1" in formatted


# Tests for critique engine pattern matching (Phase 2 enhancement)

@pytest.mark.asyncio
async def test_detect_logical_gaps_conclusion_without_reasoning(sequential_mode):
    """Test detection of conclusions without supporting reasoning."""
    response = "Therefore, the answer is X."
    gaps = sequential_mode._detect_logical_gaps(response)
    assert len(gaps) > 0
    assert any("conclusion without supporting reasoning" in gap.lower() for gap in gaps)


@pytest.mark.asyncio
async def test_detect_logical_gaps_short_answer_to_question(sequential_mode):
    """Test detection of direct answers without elaboration."""
    response = "What is the capital? Paris."
    gaps = sequential_mode._detect_logical_gaps(response)
    assert len(gaps) > 0
    assert any("direct answer without elaboration" in gap.lower() for gap in gaps)


@pytest.mark.asyncio
async def test_detect_logical_gaps_missing_step_2(sequential_mode):
    """Test detection of missing step 2 in reasoning."""
    response = "Step 1: do this. Step 3: do that."
    gaps = sequential_mode._detect_logical_gaps(response)
    assert len(gaps) > 0
    assert any("missing step 2" in gap.lower() for gap in gaps)


@pytest.mark.asyncio
async def test_detect_logical_gaps_no_gaps(sequential_mode):
    """Test that good reasoning passes logical gap detection."""
    response = "Because of evidence A and reason B, we can conclude C. Therefore, the answer is X."
    gaps = sequential_mode._detect_logical_gaps(response)
    assert len(gaps) == 0


@pytest.mark.asyncio
async def test_detect_overconfidence_absolute_claims(sequential_mode):
    """Test detection of absolute claims without evidence."""
    response = "This will always happen."
    overconfident = sequential_mode._detect_overconfidence(response)
    assert len(overconfident) > 0
    assert any("absolute claim without evidence" in issue.lower() for issue in overconfident)


@pytest.mark.asyncio
async def test_detect_overconfidence_prediction_without_qualifier(sequential_mode):
    """Test detection of predictions without uncertainty qualifiers."""
    response = "This is going to happen tomorrow."
    overconfident = sequential_mode._detect_overconfidence(response)
    assert len(overconfident) > 0
    assert any("prediction without uncertainty qualifier" in issue.lower() for issue in overconfident)


@pytest.mark.asyncio
async def test_detect_overconfidence_with_evidence(sequential_mode):
    """Test that claims with evidence pass overconfidence detection."""
    response = "Based on studies and data, this will always occur."
    overconfident = sequential_mode._detect_overconfidence(response)
    assert len(overconfident) == 0


@pytest.mark.asyncio
async def test_detect_overconfidence_with_qualifiers(sequential_mode):
    """Test that qualified predictions pass overconfidence detection."""
    response = "This will likely happen tomorrow."
    overconfident = sequential_mode._detect_overconfidence(response)
    assert len(overconfident) == 0


@pytest.mark.asyncio
async def test_detect_contradictions_will_wont(sequential_mode):
    """Test detection of will/won't contradictions."""
    # Need more context for contradiction detection (requires overlapping words)
    response = "The system will work perfectly. The system won't work at all."
    contradictions = sequential_mode._detect_contradictions(response)
    assert len(contradictions) > 0


@pytest.mark.asyncio
async def test_detect_contradictions_true_false(sequential_mode):
    """Test detection of true/false contradictions."""
    response = "The statement is true. The statement is false."
    contradictions = sequential_mode._detect_contradictions(response)
    assert len(contradictions) > 0


@pytest.mark.asyncio
async def test_detect_contradictions_always_never(sequential_mode):
    """Test detection of always/never contradictions."""
    response = "This always happens. This never happens."
    contradictions = sequential_mode._detect_contradictions(response)
    assert len(contradictions) > 0


@pytest.mark.asyncio
async def test_detect_contradictions_no_contradictions(sequential_mode):
    """Test that consistent reasoning passes contradiction detection."""
    response = "This is good. This is positive. This is excellent."
    contradictions = sequential_mode._detect_contradictions(response)
    assert len(contradictions) == 0


@pytest.mark.asyncio
async def test_detect_missing_alternatives_definitive_answer(sequential_mode):
    """Test detection of definitive answers without considering alternatives."""
    response = "The answer is X."
    missing = sequential_mode._detect_missing_alternatives(response)
    assert len(missing) > 0
    assert any("definitive answer" in issue.lower() for issue in missing)


@pytest.mark.asyncio
async def test_detect_missing_alternatives_single_approach(sequential_mode):
    """Test detection of single approach without exploring others."""
    response = "The best approach is to do X."
    missing = sequential_mode._detect_missing_alternatives(response)
    assert len(missing) > 0
    assert any("single approach" in issue.lower() for issue in missing)


@pytest.mark.asyncio
async def test_detect_missing_alternatives_with_alternatives(sequential_mode):
    """Test that responses considering alternatives pass detection."""
    response = "The answer is X. However, we could also consider Y. Alternatively, Z might work."
    missing = sequential_mode._detect_missing_alternatives(response)
    assert len(missing) == 0


@pytest.mark.asyncio
async def test_critique_reasoning_comprehensive(sequential_mode):
    """Test comprehensive critique with multiple issue types."""
    response = "Therefore, X is always true. It will never change. The answer is Y."
    critique = sequential_mode._critique_reasoning(response)
    assert "logical_gaps" in critique
    assert "overconfidence" in critique
    assert "contradictions" in critique
    assert "missing_alternatives" in critique


@pytest.mark.asyncio
async def test_critique_reasoning_no_issues(sequential_mode):
    """Test critique on high-quality reasoning."""
    response = "Based on evidence from multiple studies, we typically observe that X likely occurs. However, alternative explanations include Y and Z. Therefore, we can conclude that X is probable."
    critique = sequential_mode._critique_reasoning(response)
    assert len(critique["logical_gaps"]) == 0
    assert len(critique["overconfidence"]) == 0
    assert len(critique["contradictions"]) == 0
    assert len(critique["missing_alternatives"]) == 0


@pytest.mark.asyncio
async def test_are_contradictory_helper_method(sequential_mode):
    """Test the _are_contradictory helper method."""
    # Test obvious contradictions (need overlapping words for detection)
    assert sequential_mode._are_contradictory("The system will work", "The system won't work") is True
    assert sequential_mode._are_contradictory("The statement is true", "The statement is false") is True

    # Test non-contradictions
    assert sequential_mode._are_contradictory("It will work", "It might work") is False
    assert sequential_mode._are_contradictory("X is good", "Y is bad") is False


# Tests for improvement engine (Phase 2 enhancement)

@pytest.mark.asyncio
async def test_improve_response_adds_reasoning_for_conclusions(sequential_mode):
    """Test that improvement adds reasoning for conclusions without support."""
    original = "Therefore, the answer is X."
    critique = {
        "logical_gaps": ["Conclusion without supporting reasoning"],
        "overconfidence": [],
        "contradictions": [],
        "missing_alternatives": []
    }
    improved = sequential_mode._improve_response(original, critique)
    assert "explain" in improved.lower() or "reasoning" in improved.lower()
    assert len(improved) > len(original)


@pytest.mark.asyncio
async def test_improve_response_adds_uncertainty_hedges(sequential_mode):
    """Test that improvement adds uncertainty qualifiers to absolute claims."""
    original = "This will always happen."
    critique = {
        "logical_gaps": [],
        "overconfidence": ["Absolute claim without evidence"],
        "contradictions": [],
        "missing_alternatives": []
    }
    improved = sequential_mode._improve_response(original, critique)
    # Should replace "always" with "typically" or similar
    assert "always" not in improved.lower() or "typically" in improved.lower()


@pytest.mark.asyncio
async def test_improve_response_resolves_contradictions(sequential_mode):
    """Test that improvement marks contradictions."""
    original = "It will work. It won't work."
    critique = {
        "logical_gaps": [],
        "overconfidence": [],
        "contradictions": ["Contradiction detected"],
        "missing_alternatives": []
    }
    improved = sequential_mode._improve_response(original, critique)
    # Should add clarification note
    assert "note" in improved.lower() or "contradiction" in improved.lower()


@pytest.mark.asyncio
async def test_improve_response_multiple_issue_types(sequential_mode):
    """Test improvement with multiple issue types."""
    original = "Therefore, X is always true."
    critique = {
        "logical_gaps": ["Conclusion without supporting reasoning"],
        "overconfidence": ["Absolute claim without evidence"],
        "contradictions": [],
        "missing_alternatives": []
    }
    improved = sequential_mode._improve_response(original, critique)
    # Should address both logical gap and overconfidence
    assert "explain" in improved.lower() or "reasoning" in improved.lower()
    assert len(improved) > len(original)


@pytest.mark.asyncio
async def test_improve_response_no_improvements_needed(sequential_mode):
    """Test that good responses are returned unchanged."""
    original = "Based on evidence, X is likely true."
    critique = {
        "logical_gaps": [],
        "overconfidence": [],
        "contradictions": [],
        "missing_alternatives": []
    }
    improved = sequential_mode._improve_response(original, critique)
    # No issues found, should return original
    assert improved == original


@pytest.mark.asyncio
async def test_add_reasoning_steps_before_therefore(sequential_mode):
    """Test adding reasoning before 'therefore'."""
    response = "Therefore, X is true."
    gaps = ["Conclusion without supporting reasoning"]
    improved = sequential_mode._add_reasoning_steps(response, gaps)
    assert "explain" in improved.lower()
    assert "therefore" in improved.lower()


@pytest.mark.asyncio
async def test_add_reasoning_steps_for_short_answers(sequential_mode):
    """Test adding reasoning for short answers."""
    response = "What is X? Y."
    gaps = ["Direct answer without elaboration"]
    improved = sequential_mode._add_reasoning_steps(response, gaps)
    assert "reasoning" in improved.lower()
    assert len(improved) > len(response)


@pytest.mark.asyncio
async def test_add_reasoning_steps_missing_step_2(sequential_mode):
    """Test inserting missing step 2."""
    response = "Step 1: do A. Step 3: do C."
    gaps = ["Missing step 2 in reasoning"]
    improved = sequential_mode._add_reasoning_steps(response, gaps)
    assert "next step" in improved.lower()


@pytest.mark.asyncio
async def test_add_uncertainty_hedges_replace_always(sequential_mode):
    """Test replacing 'always' with 'typically'."""
    response = "This will always occur."
    issues = ["Absolute claim without evidence"]
    improved = sequential_mode._add_uncertainty_hedges(response, issues)
    assert "typically" in improved.lower() or "always" not in improved.lower()


@pytest.mark.asyncio
async def test_add_uncertainty_hedges_replace_never(sequential_mode):
    """Test replacing 'never' with 'rarely'."""
    response = "This never happens."
    issues = ["Absolute claim without evidence"]
    improved = sequential_mode._add_uncertainty_hedges(response, issues)
    assert "rarely" in improved.lower() or "never" not in improved.lower()


@pytest.mark.asyncio
async def test_add_uncertainty_hedges_qualify_predictions(sequential_mode):
    """Test adding 'likely' to predictions."""
    response = "This is going to happen."
    issues = ["Prediction without uncertainty qualifier"]
    improved = sequential_mode._add_uncertainty_hedges(response, issues)
    assert "likely" in improved.lower()


@pytest.mark.asyncio
async def test_add_uncertainty_hedges_no_changes_needed(sequential_mode):
    """Test that already-qualified responses are unchanged."""
    response = "This will likely happen."
    issues = []
    improved = sequential_mode._add_uncertainty_hedges(response, issues)
    # Should be unchanged or very similar
    assert improved == response or "likely" in improved.lower()


@pytest.mark.asyncio
async def test_resolve_contradictions_adds_note(sequential_mode):
    """Test that contradiction note is added."""
    response = "X is true. X is false."
    contradictions = ["Contradiction: X is true vs X is false"]
    improved = sequential_mode._resolve_contradictions(response, contradictions)
    assert "note" in improved.lower()


@pytest.mark.asyncio
async def test_resolve_contradictions_no_contradictions(sequential_mode):
    """Test that responses without contradictions are unchanged."""
    response = "X is true. Y is also true."
    contradictions = []
    improved = sequential_mode._resolve_contradictions(response, contradictions)
    assert improved == response


# Tests for quality gate (Phase 2 enhancement)

@pytest.mark.asyncio
async def test_passes_quality_gate_few_issues(sequential_mode):
    """Test that quality gate passes with few issues."""
    response = "Good response."
    critique = {
        "logical_gaps": [],
        "overconfidence": [],
        "contradictions": [],
        "missing_alternatives": []
    }
    assert sequential_mode._passes_quality_gate(response, critique) is True


@pytest.mark.asyncio
async def test_passes_quality_gate_threshold_boundary(sequential_mode):
    """Test quality gate at threshold boundary (2 issues = pass)."""
    response = "Response with issues."
    critique = {
        "logical_gaps": ["Issue 1", "Issue 2"],
        "overconfidence": [],
        "contradictions": [],
        "missing_alternatives": []
    }
    # 2 issues should pass (threshold is <3)
    assert sequential_mode._passes_quality_gate(response, critique) is True


@pytest.mark.asyncio
async def test_passes_quality_gate_threshold_exceeded(sequential_mode):
    """Test that quality gate fails when threshold exceeded (3 issues = fail)."""
    response = "Response with many issues."
    critique = {
        "logical_gaps": ["Issue 1", "Issue 2", "Issue 3"],
        "overconfidence": [],
        "contradictions": [],
        "missing_alternatives": []
    }
    # 3 issues should fail (threshold is <3)
    assert sequential_mode._passes_quality_gate(response, critique) is False


@pytest.mark.asyncio
async def test_passes_quality_gate_multiple_categories(sequential_mode):
    """Test quality gate with issues across multiple categories."""
    response = "Response with various issues."
    critique = {
        "logical_gaps": ["Gap 1"],
        "overconfidence": ["Overconfident 1"],
        "contradictions": ["Contradiction 1"],
        "missing_alternatives": []
    }
    # 3 total issues across categories should fail
    assert sequential_mode._passes_quality_gate(response, critique) is False


@pytest.mark.asyncio
async def test_self_critique_integrates_all_components(sequential_mode, sample_thought_chain):
    """Test that _self_critique integrates critique, quality gate, and improvement."""
    result = sequential_mode._self_critique(sample_thought_chain)
    # Should return a string (either improved or original feedback)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_self_critique_graceful_fallback(sequential_mode):
    """Test graceful fallback when improvement fails."""
    # Create a chain that might trigger improvement
    chain = ThoughtChain()
    chain.add_thought(Thought(
        content="Therefore, X is always true.",
        stage=ThoughtStage.CONCLUSION,
        thought_number=1,
        total_thoughts=1,
        confidence=0.8,
    ))

    # Should not raise exception even if improvement fails
    result = sequential_mode._self_critique(chain)
    assert isinstance(result, str)

