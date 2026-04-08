"""Anti-Sycophancy detection modules."""

from reasoning.anti_sycophancy.hypothesis_as_fact_detector import (
    DetectionResult,
    HypothesisFactPattern,
    detect_hypothesis_as_fact,
)

__all__ = [
    "detect_hypothesis_as_fact",
    "HypothesisFactPattern",
    "DetectionResult",
]
