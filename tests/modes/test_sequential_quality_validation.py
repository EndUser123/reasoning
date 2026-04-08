"""A/B quality validation tests for Sequential mode self-reflection enhancement.

These tests measure actual quality improvement by comparing responses
with and without self-reflection enhancement.

This validates or disproves the 20-60% improvement claim.
"""


import pytest

from reasoning.config import ReasoningConfig
from reasoning.models import Mode
from reasoning.modes.sequential import SequentialMode


@pytest.fixture
def config():
    """Create a test configuration."""
    return ReasoningConfig(mode=Mode.SEQUENTIAL)


@pytest.fixture
def sequential_mode(config):
    """Create a SequentialMode instance for testing."""
    return SequentialMode(config)


def count_quality_issues(text: str) -> dict[str, int]:
    """Count quality issues in text using manual analysis.

    Args:
        text: The text to analyze

    Returns:
        Dictionary with issue counts
    """
    import re

    issues = {
        "logical_gaps": 0,
        "overconfidence": 0,
        "contradictions": 0,
        "missing_alternatives": 0,
    }

    # Count logical gaps
    if re.search(r'therefore|thus|consequently', text, re.I):
        if not re.search(r'because|since|reason|evidence', text, re.I):
            issues["logical_gaps"] += 1

    # Count overconfidence
    if re.search(r'\balways\b|\bnever\b|\bcertainly\b', text, re.I):
        if not re.search(r'evidence|data|study|research', text, re.I):
            issues["overconfidence"] += 1

    # Count contradictions
    sentences = text.split('.')
    for i, sent1 in enumerate(sentences):
        for sent2 in sentences[i+1:]:
            # Simple contradiction check
            if re.search(r'\bwill\b', sent1, re.I) and re.search(r"\bwon't\b", sent2, re.I):
                issues["contradictions"] += 1
            if re.search(r'\btrue\b', sent1, re.I) and re.search(r'\bfalse\b', sent2, re.I):
                issues["contradictions"] += 1

    # Count missing alternatives
    if re.search(r'the answer is|the solution is|the best', text, re.I):
        if not re.search(r'alternatively|however|another option', text, re.I):
            issues["missing_alternatives"] += 1

    return issues


def calculate_quality_score(issues: dict[str, int]) -> float:
    """Calculate quality score from issue counts.

    Args:
        issues: Dictionary with issue counts

    Returns:
        Quality score (0.0 to 1.0, higher is better)
    """
    total_issues = sum(issues.values())

    if total_issues == 0:
        return 1.0

    # Score decreases with more issues
    # 0 issues = 1.0, 1 issue = 0.9, 2 issues = 0.8, etc.
    score = max(0.0, 1.0 - (total_issues * 0.1))
    return score


# A/B validation tests

@pytest.mark.asyncio
async def test_quality_comparison_conclusion_without_reasoning(sequential_mode):
    """Test quality improvement for conclusions without reasoning."""
    # Test response with logical gaps
    test_response = "Therefore, the answer is Paris. It is the capital."

    # Without self-reflection (baseline)
    baseline_issues = count_quality_issues(test_response)
    baseline_score = calculate_quality_score(baseline_issues)

    # With self-reflection (enhanced)
    critique = sequential_mode._critique_reasoning(test_response)
    enhanced_response = sequential_mode._improve_response(test_response, critique)
    enhanced_issues = count_quality_issues(enhanced_response)
    enhanced_score = calculate_quality_score(enhanced_issues)

    # Enhanced should be same or better
    assert enhanced_score >= baseline_score

    # Log results for analysis
    print(f"\nBaseline: {baseline_score:.2f} (issues: {baseline_issues})")
    print(f"Enhanced: {enhanced_score:.2f} (issues: {enhanced_issues})")
    print(f"Improvement: {((enhanced_score - baseline_score) / max(baseline_score, 0.01)) * 100:.1f}%")


@pytest.mark.asyncio
async def test_quality_comparison_overconfident_claims(sequential_mode):
    """Test quality improvement for overconfident claims."""
    test_response = "This will always happen. It is certain."

    baseline_issues = count_quality_issues(test_response)
    baseline_score = calculate_quality_score(baseline_issues)

    critique = sequential_mode._critique_reasoning(test_response)
    enhanced_response = sequential_mode._improve_response(test_response, critique)
    enhanced_issues = count_quality_issues(enhanced_response)
    enhanced_score = calculate_quality_score(enhanced_issues)

    assert enhanced_score >= baseline_score

    print(f"\nBaseline: {baseline_score:.2f} (issues: {baseline_issues})")
    print(f"Enhanced: {enhanced_score:.2f} (issues: {enhanced_issues})")
    print(f"Improvement: {((enhanced_score - baseline_score) / max(baseline_score, 0.01)) * 100:.1f}%")


@pytest.mark.asyncio
async def test_quality_comparison_contradictions(sequential_mode):
    """Test quality improvement for contradictions."""
    test_response = "It will work. It won't work."

    baseline_issues = count_quality_issues(test_response)
    baseline_score = calculate_quality_score(baseline_issues)

    critique = sequential_mode._critique_reasoning(test_response)
    enhanced_response = sequential_mode._improve_response(test_response, critique)
    enhanced_issues = count_quality_issues(enhanced_response)
    enhanced_score = calculate_quality_score(enhanced_issues)

    assert enhanced_score >= baseline_score

    print(f"\nBaseline: {baseline_score:.2f} (issues: {baseline_issues})")
    print(f"Enhanced: {enhanced_score:.2f} (issues: {enhanced_issues})")
    print(f"Improvement: {((enhanced_score - baseline_score) / max(baseline_score, 0.01)) * 100:.1f}%")


@pytest.mark.asyncio
async def test_quality_comparison_missing_alternatives(sequential_mode):
    """Test quality improvement for missing alternatives."""
    test_response = "The answer is X. This is the best solution."

    baseline_issues = count_quality_issues(test_response)
    baseline_score = calculate_quality_score(baseline_issues)

    critique = sequential_mode._critique_reasoning(test_response)
    enhanced_response = sequential_mode._improve_response(test_response, critique)
    enhanced_issues = count_quality_issues(enhanced_response)
    enhanced_score = calculate_quality_score(enhanced_issues)

    assert enhanced_score >= baseline_score

    print(f"\nBaseline: {baseline_score:.2f} (issues: {baseline_issues})")
    print(f"Enhanced: {enhanced_score:.2f} (issues: {enhanced_issues})")
    print(f"Improvement: {((enhanced_score - baseline_score) / max(baseline_score, 0.01)) * 100:.1f}%")


@pytest.mark.asyncio
async def test_quality_comparison_multiple_issue_types(sequential_mode):
    """Test quality improvement with multiple issue types."""
    test_response = "Therefore, this will always happen. The answer is X."

    baseline_issues = count_quality_issues(test_response)
    baseline_score = calculate_quality_score(baseline_issues)

    critique = sequential_mode._critique_reasoning(test_response)
    enhanced_response = sequential_mode._improve_response(test_response, critique)
    enhanced_issues = count_quality_issues(enhanced_response)
    enhanced_score = calculate_quality_score(enhanced_issues)

    assert enhanced_score >= baseline_score

    print(f"\nBaseline: {baseline_score:.2f} (issues: {baseline_issues})")
    print(f"Enhanced: {enhanced_score:.2f} (issues: {enhanced_issues})")
    print(f"Improvement: {((enhanced_score - baseline_score) / max(baseline_score, 0.01)) * 100:.1f}%")


@pytest.mark.asyncio
async def test_quality_aggregation_across_test_cases(sequential_mode):
    """Aggregate quality improvements across multiple test cases."""
    test_cases = [
        "Therefore, the answer is Paris.",
        "This will always happen.",
        "It will work. It won't work.",
        "The solution is X.",
        "Therefore, this is certainly true.",
    ]

    baseline_scores = []
    enhanced_scores = []

    for test_response in test_cases:
        # Baseline
        baseline_issues = count_quality_issues(test_response)
        baseline_score = calculate_quality_score(baseline_issues)
        baseline_scores.append(baseline_score)

        # Enhanced
        critique = sequential_mode._critique_reasoning(test_response)
        enhanced_response = sequential_mode._improve_response(test_response, critique)
        enhanced_issues = count_quality_issues(enhanced_response)
        enhanced_score = calculate_quality_score(enhanced_issues)
        enhanced_scores.append(enhanced_score)

    # Calculate average improvement
    avg_baseline = sum(baseline_scores) / len(baseline_scores)
    avg_enhanced = sum(enhanced_scores) / len(enhanced_scores)
    avg_improvement = ((avg_enhanced - avg_baseline) / max(avg_baseline, 0.01)) * 100

    print("\n=== Quality Validation Results ===")
    print(f"Test cases: {len(test_cases)}")
    print(f"Average baseline score: {avg_baseline:.2f}")
    print(f"Average enhanced score: {avg_enhanced:.2f}")
    print(f"Average improvement: {avg_improvement:.1f}%")

    # Validate claim: Is improvement between 20-60%?
    if avg_improvement >= 20:
        print(f"✓ Claim validated: {avg_improvement:.1f}% improvement >= 20%")
    else:
        print(f"⚠ Claim not validated: {avg_improvement:.1f}% improvement < 20%")
        print("  Recommendation: Adjust documentation to reflect actual improvement")

    # Enhanced should not be worse than baseline
    assert avg_enhanced >= avg_baseline


@pytest.mark.asyncio
async def test_end_to_end_quality_validation(sequential_mode):
    """Test quality improvement through full process() method."""
    # This test validates quality through the actual SequentialMode.process() method

    result = await sequential_mode.process("What is the capital of France?")

    # Should include quality checks
    assert "quality_checks" in result.metadata
    quality_checks = result.metadata["quality_checks"]

    # Should have quality score
    assert result.quality_score is not None
    assert 0.0 <= result.quality_score <= 1.0

    # Log quality metrics
    print("\n=== End-to-End Quality Metrics ===")
    print(f"Quality score: {result.quality_score:.2f}")
    print(f"Quality checks: {quality_checks}")
    print(f"Total thoughts: {result.metadata['total_thoughts']}")


@pytest.mark.asyncio
async def test_pattern_matching_effectiveness(sequential_mode):
    """Test effectiveness of pattern matching for issue detection."""
    test_cases = [
        ("Therefore, X.", ["logical_gaps"]),
        ("This will always happen.", ["overconfidence"]),
        ("It is true. It is false.", ["contradictions"]),
        ("The answer is X.", ["missing_alternatives"]),
        ("Therefore, this will always occur.", ["logical_gaps", "overconfidence"]),
    ]

    detection_accuracy = {
        "correct_detections": 0,
        "total_detections": 0,
    }

    for test_response, expected_issue_types in test_cases:
        critique = sequential_mode._critique_reasoning(test_response)

        for issue_type in expected_issue_types:
            detection_accuracy["total_detections"] += 1
            if len(critique[issue_type]) > 0:
                detection_accuracy["correct_detections"] += 1

    accuracy = (detection_accuracy["correct_detections"] / detection_accuracy["total_detections"]) * 100

    print("\n=== Pattern Matching Effectiveness ===")
    print(f"Detections: {detection_accuracy['correct_detections']}/{detection_accuracy['total_detections']}")
    print(f"Accuracy: {accuracy:.1f}%")

    # Should have reasonable accuracy (>70%)
    assert accuracy > 70


@pytest.mark.asyncio
async def test_quality_regression_prevention(sequential_mode):
    """Test that enhancement doesn't make good responses worse."""
    # Test cases that are already good
    good_responses = [
        "Based on historical evidence, Paris is likely the capital of France.",
        "Studies suggest this typically occurs. However, alternative explanations exist.",
        "Therefore, we can conclude X is probable, based on the evidence presented.",
    ]

    for good_response in good_responses:
        baseline_issues = count_quality_issues(good_response)
        baseline_score = calculate_quality_score(baseline_issues)

        critique = sequential_mode._critique_reasoning(good_response)
        enhanced_response = sequential_mode._improve_response(good_response, critique)
        enhanced_issues = count_quality_issues(enhanced_response)
        enhanced_score = calculate_quality_score(enhanced_issues)

        # Good responses should not be made worse
        assert enhanced_score >= baseline_score, \
            f"Good response was made worse: {baseline_score:.2f} → {enhanced_score:.2f}"


# Documentation validation test

@pytest.mark.asyncio
async def test_validate_quality_improvement_claim(sequential_mode):
    """
    Validate or disprove the 20-60% quality improvement claim.

    This test aggregates all quality validation tests to produce
    a final report on whether the claim holds.

    Results should be documented in README.md.
    """
    # Run comprehensive validation
    test_cases = [
        "Therefore, X.",
        "This will always happen.",
        "It is true. It is false.",
        "The answer is X.",
        "Therefore, this will certainly occur.",
        "The solution is X.",
        "This never happens.",
        "Therefore, the answer is Y.",
        "It will work. It won't succeed.",
        "The best approach is Z.",
    ]

    improvements = []

    for test_response in test_cases:
        baseline_issues = count_quality_issues(test_response)
        baseline_score = calculate_quality_score(baseline_issues)

        critique = sequential_mode._critique_reasoning(test_response)
        enhanced_response = sequential_mode._improve_response(test_response, critique)
        enhanced_issues = count_quality_issues(enhanced_response)
        enhanced_score = calculate_quality_score(enhanced_issues)

        if baseline_score > 0:
            improvement = ((enhanced_score - baseline_score) / baseline_score) * 100
            improvements.append(improvement)

    avg_improvement = sum(improvements) / len(improvements)
    min_improvement = min(improvements)
    max_improvement = max(improvements)

    print(f"\n{'='*60}")
    print("QUALITY IMPROVEMENT VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Test cases: {len(test_cases)}")
    print(f"Average improvement: {avg_improvement:.1f}%")
    print(f"Min improvement: {min_improvement:.1f}%")
    print(f"Max improvement: {max_improvement:.1f}%")
    print(f"{'='*60}")

    # Validate claim
    if 20 <= avg_improvement <= 60:
        print(f"✓ CLAIM VALIDATED: {avg_improvement:.1f}% is within 20-60% range")
        print("  Documentation claim is ACCURATE")
    elif avg_improvement < 20:
        print(f"⚠ CLAIM NOT VALIDATED: {avg_improvement:.1f}% is below 20% minimum")
        print("  RECOMMENDATION: Update documentation to reflect actual improvement")
    else:
        print(f"✓ CLAIM EXCEEDED: {avg_improvement:.1f}% exceeds 60% maximum")
        print("  Documentation claim is CONSERVATIVE")

    print("\nACTION REQUIRED:")
    print("1. Document these results in README.md")
    print(f"2. Update claim if needed: 'Self-reflection improves quality by ~{avg_improvement:.0f}%'")
    print(f"{'='*60}")

    # Write results to file for documentation
    results_path = "P:/packages/reasoning/QUALITY_VALIDATION_RESULTS.md"
    with open(results_path, 'w') as f:
        f.write("# Quality Validation Results\n\n")
        f.write("## Test Summary\n\n")
        f.write("- **Test Date**: 2026-03-10\n")
        f.write(f"- **Test Cases**: {len(test_cases)}\n")
        f.write(f"- **Average Improvement**: {avg_improvement:.1f}%\n")
        f.write(f"- **Min Improvement**: {min_improvement:.1f}%\n")
        f.write(f"- **Max Improvement**: {max_improvement:.1f}%\n\n")
        f.write("## Claim Validation\n\n")
        if 20 <= avg_improvement <= 60:
            f.write(f"✓ **CLAIM VALIDATED**: {avg_improvement:.1f}% is within 20-60% range\n\n")
            f.write("The documented claim 'Self-reflection improves reasoning quality by 20-60%' is **accurate**.\n")
        elif avg_improvement < 20:
            f.write(f"⚠ **CLAIM NOT VALIDATED**: {avg_improvement:.1f}% is below 20% minimum\n\n")
            f.write(f"**Recommendation**: Update documentation to claim '~{avg_improvement:.0f}% improvement'\n")
        else:
            f.write(f"✓ **CLAIM EXCEEDED**: {avg_improvement:.1f}% exceeds 60% maximum\n\n")
            f.write("The documented claim is **conservative**.\n")
        f.write("\n## Test Results\n\n")
        f.write("| Test Case | Baseline Score | Enhanced Score | Improvement |\n")
        f.write("|-----------|----------------|----------------|-------------|\n")
        for i, (test_response, improvement) in enumerate(zip(test_cases, improvements)):
            baseline_issues = count_quality_issues(test_response)
            baseline_score = calculate_quality_score(baseline_issues)
            critique = sequential_mode._critique_reasoning(test_response)
            enhanced_response = sequential_mode._improve_response(test_response, critique)
            enhanced_issues = count_quality_issues(enhanced_response)
            enhanced_score = calculate_quality_score(enhanced_issues)
            f.write(f"| {i+1}. {test_response[:50]} | {baseline_score:.2f} | {enhanced_score:.2f} | {improvement:.1f}% |\n")

    print(f"\nResults saved to: {results_path}")
    print("Include this file in README.md documentation")
