"""
Unified Reasoning Engine

Consolidates multi-agent, cognitive, graph, and two-stage reasoning modes.
"""

__version__ = "0.1.0"

from reasoning.config import ReasoningConfig
from reasoning.engine import ReasoningEngine
from reasoning.models import Mode, Thought, ThoughtBranch, ThoughtChain, ThoughtStage

__all__ = [
    "ReasoningEngine",
    "Thought",
    "ThoughtChain",
    "ThoughtBranch",
    "ThoughtStage",
    "Mode",
    "ReasoningConfig",
]
