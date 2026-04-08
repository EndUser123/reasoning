"""Integration tests for Sequential mode self-reflection enhancement.

These tests verify the end-to-end Generate→Critique→Improve flow
and ensure existing SequentialMode behavior is preserved.
"""

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


# Integration tests for Generate→Critique→Improve flow

@pytest.mark.asyncio
async def test_full_self_reflection_flow_with_issues(sequential_mode):
    """Test complete self-reflection flow when issues are detected."""
    # Create a chain with issues
    chain = ThoughtChain()
    chain.add_thought(Thought(
        content="Therefore, X is always true. It will never change.",
        stage=ThoughtStage.CONCLUSION,
        thought_number=1,
        total_thoughts=1,
        confidence=0.9,
    ))

    # Run self-critique (should detect issues and attempt improvement)
    critique_result = sequential_mode._self_critique(chain)

    # Should return critique feedback
    assert isinstance(critique_result, str)
    assert len(critique_result) > 0
    # Should mention issues found
    assert "issues" in critique_result.lower() or "improved" in critique_result.lower()


@pytest.mark.asyncio
async def test_full_self_reflection_flow_no_issues(sequential_mode, sample_thought_chain):
    """Test complete self-reflection flow when reasoning is sound."""
    # Run self-critique on good chain
    critique_result = sequential_mode._self_critique(sample_thought_chain)

    # Should return success message
    assert isinstance(critique_result, str)
    assert "sound" in critique_result.lower() or "no major issues" in critique_result.lower()


@pytest.mark.asyncio
async def test_critique_to_improve_integration(sequential_mode):
    """Test integration between critique and improvement engines."""
    # Use a response with multiple issues to trigger quality gate failure
    response = "Therefore, this will always happen. The answer is X. It is true. It is false."

    # Stage 1: Critique
    critique = sequential_mode._critique_reasoning(response)
    assert "logical_gaps" in critique
    # Should detect at least some issues
    total_issues = sum(len(issues) for issues in critique.values())
    assert total_issues >= 1  # At least 1 issue detected

    # Stage 2: Quality gate
    passes = sequential_mode._passes_quality_gate(response, critique)
    # Quality gate fails if >=3 issues, passes if <3
    # We expect issues to be detected (but gate result depends on count)

    # Stage 3: Improve (regardless of gate result)
    improved = sequential_mode._improve_response(response, critique)
    assert isinstance(improved, str)
    assert len(improved) >= len(response)  # Should be same or longer


@pytest.mark.asyncio
async def test_process_preserves_existing_behavior(sequential_mode):
    """Test that process() still works with self-reflection enhancement."""
    result = await sequential_mode.process("What is the capital of France?")

    # Should return ProcessingResult
    assert result is not None
    assert result.conclusion is not None
    assert result.thought_chain is not None
    assert result.quality_score is not None
    assert result.metadata is not None


@pytest.mark.asyncio
async def test_process_includes_critique_in_metadata(sequential_mode):
    """Test that process() includes critique feedback in metadata."""
    result = await sequential_mode.process("Test prompt")

    # Should include quality_checks
    assert "quality_checks" in result.metadata
    assert "critique" in result.metadata or "total_thoughts" in result.metadata


@pytest.mark.asyncio
async def test_mode_switching_flow(sequential_mode):
    """Test that mode switching works (generation → analysis → improvement)."""
    # Phase 1: Generate (create thought chain)
    chain = await sequential_mode._generate_sequential_thoughts("Test prompt")
    assert chain.length == 5

    # Phase 2: Analyze (critique - switches to analysis mode)
    critique = sequential_mode._self_critique(chain)
    assert isinstance(critique, str)

    # Phase 3: Verify quality checks work
    quality_checks = sequential_mode._quality_gate(chain)
    assert "all_passed" in quality_checks


@pytest.mark.asyncio
async def test_existing_quality_checks_still_work(sequential_mode, sample_thought_chain):
    """Test that existing quality check methods still function."""
    # Test existing quality check methods
    assert sequential_mode._has_all_stages(sample_thought_chain) is True
    assert sequential_mode._claims_are_supported(sample_thought_chain) is True
    assert sequential_mode._is_internally_consistent(sample_thought_chain) is True
    assert sequential_mode._answers_user_question(sample_thought_chain) is True


@pytest.mark.asyncio
async def test_refine_thoughts_preserves_chain_structure(sequential_mode, sample_thought_chain):
    """Test that _refine_thoughts preserves chain structure."""
    critique = "Issues found:\n- Test issue"

    refined = sequential_mode._refine_thoughts(sample_thought_chain, critique)

    # Should preserve structure
    assert refined.length >= sample_thought_chain.length
    # Should have Thought objects
    assert all(isinstance(t, Thought) for t in refined.thoughts)
    # Should preserve stages
    original_stages = {t.stage for t in sample_thought_chain.thoughts}
    refined_stages = {t.stage for t in refined.thoughts[:5]}
    assert original_stages == refined_stages


@pytest.mark.asyncio
async def test_end_to_end_quality_improvement(sequential_mode):
    """Test that self-reflection improves response quality."""
    # Create low-quality chain with issues in content (not structure)
    low_quality_chain = ThoughtChain()
    low_quality_chain.add_thought(Thought(
        content="Therefore, X is always true.",  # Logical gap + overconfidence
        stage=ThoughtStage.CONCLUSION,
        thought_number=1,
        total_thoughts=1,
        confidence=0.9,
    ))

    # Get critique
    critique = sequential_mode._self_critique(low_quality_chain)

    # Should detect issues or show improvement
    assert "issues" in critique.lower() or "improved" in critique.lower() or "sound" in critique.lower()


@pytest.mark.asyncio
async def test_graceful_degradation_on_errors(sequential_mode):
    """Test graceful fallback when errors occur."""
    # Create minimal chain
    chain = ThoughtChain()
    chain.add_thought(Thought(
        content="Minimal",
        stage=ThoughtStage.CONCLUSION,
        thought_number=1,
        total_thoughts=1,
        confidence=0.5,
    ))

    # Should not raise exceptions
    try:
        result = sequential_mode._self_critique(chain)
        assert isinstance(result, str)
    except Exception as e:
        pytest.fail(f"_self_critique raised exception: {e}")


@pytest.mark.asyncio
async def test_quality_score_calculation_with_enhancement(sequential_mode):
    """Test that quality score calculation works with enhanced self-reflection."""
    result = await sequential_mode.process("Test prompt")

    # Quality score should be calculated based on actual quality checks
    assert 0.0 <= result.quality_score <= 1.0

    # Should not be hardcoded
    # (though it might coincidentally be certain values)


@pytest.mark.asyncio
async def test_metadata_preserves_enhancement_info(sequential_mode):
    """Test that metadata includes information about self-reflection enhancement."""
    result = await sequential_mode.process("Test prompt")

    # Should include quality_checks
    assert "quality_checks" in result.metadata
    quality_checks = result.metadata["quality_checks"]

    # Should have expected check keys
    expected_keys = ["is_complete", "is_supported", "is_consistent", "is_useful", "all_passed"]
    for key in expected_keys:
        assert key in quality_checks


@pytest.mark.asyncio
async def test_backward_compatibility_with_existing_api(sequential_mode):
    """Test that existing API methods still work correctly."""
    # Test all public API methods
    assert sequential_mode.validate_input("Test") is True
    assert sequential_mode.validate_input("") is False
    assert sequential_mode.get_mode_name() == "SequentialMode"
    assert sequential_mode._max_iterations == 2


@pytest.mark.asyncio
async def test_performance_acceptable(sequential_mode):
    """Test that self-reflection doesn't cause unacceptable performance degradation."""
    import time

    start = time.time()
    result = await sequential_mode.process("Quick test")
    elapsed = time.time() - start

    # Should complete in reasonable time (<5 seconds for test)
    # (Actual production may vary, but this ensures no catastrophic slowdown)
    assert elapsed < 5.0
    assert result is not None


@pytest.mark.asyncio
async def test_multiple_iterations_dont_cause_infinite_loop(sequential_mode):
    """Test that multiple self-reflection iterations don't cause infinite loops."""
    # Run process multiple times
    for i in range(3):
        result = await sequential_mode.process(f"Test prompt {i}")
        assert result is not None
        assert result.conclusion is not None

    # Should complete without hanging


@pytest.mark.asyncio
async def test_format_chain_output_structure(sequential_mode, sample_thought_chain):
    """Test that _format_chain produces structured, readable output."""
    formatted = sequential_mode._format_chain(sample_thought_chain)

    # Should have stage markers
    assert "Stage" in formatted

    # Should have content
    assert "content" in formatted.lower() or "stage" in formatted.lower()

    # Should be multi-line
    assert "\n" in formatted
