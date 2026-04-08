"""
Core data models for reasoning system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class Mode(Enum):
    """Reasoning modes available."""

    MULTI_AGENT = "multi_agent"
    COGNITIVE = "cognitive"
    GRAPH = "graph"
    TWO_STAGE = "two_stage"
    SEQUENTIAL = "sequential"


class ThoughtStage(Enum):
    """Cognitive thinking stages."""

    # Sequential mode stages
    PROBLEM_DEFINITION = "problem_definition"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    CONCLUSION = "conclusion"

    # Cognitive engine mode stages (Bloom's Taxonomy)
    DEFINE = "define"
    HYPOTHESIZE = "hypothesize"
    VERIFY = "verify"


@dataclass
class QualityMetrics:
    """Quality metrics for a thought."""

    ttr_clarity: float = 0.0  # Type-Token Ratio clarity
    clause_depth: int = 0
    structural_logic: float = 0.0
    noun_breadth: float = 0.0
    semantic_relevance: float = 0.0
    concrete_actionability: float = 0.0

    def overall_score(self) -> float:
        """Calculate overall quality score (0-1)."""
        return sum([
            self.ttr_clarity,
            self.structural_logic,
            self.semantic_relevance,
            self.concrete_actionability,
        ]) / 4


@dataclass
class Thought:
    """A single thought in the reasoning process."""

    content: str
    stage: ThoughtStage
    thought_number: int
    total_thoughts: int
    confidence: float = 0.5
    assumptions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate thought data."""
        if not self.content or not self.content.strip():
            raise ValueError("Thought content cannot be empty")
        if self.thought_number < 1:
            raise ValueError("Thought number must be positive")
        if self.total_thoughts < self.thought_number:
            raise ValueError("Total thoughts must be >= thought number")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")


@dataclass
class ThoughtChain:
    """A chain of sequential thoughts."""

    thoughts: list[Thought] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_thought(self, thought: Thought) -> None:
        """Add a thought to the chain."""
        self.thoughts.append(thought)

    def get_last_thought(self) -> Thought | None:
        """Get the most recent thought."""
        return self.thoughts[-1] if self.thoughts else None

    @property
    def length(self) -> int:
        """Get the number of thoughts in the chain."""
        return len(self.thoughts)


@dataclass
class CrossReference:
    """A cross-reference between two thoughts."""

    source_thought_id: UUID
    target_thought_id: UUID
    relation_type: str  # "supports", "contradicts", "related", "expands"
    confidence: float = 0.5
    rationale: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)


@dataclass
class ThoughtBranch:
    """A branch of parallel thoughts for graph mode."""

    id: str = ""
    name: str = ""
    thoughts: list[Thought] = field(default_factory=list)
    cross_references: list[CrossReference] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Generate ID if not provided."""
        if not self.id:
            self.id = str(uuid4())

    def add_thought(self, thought: Thought) -> None:
        """Add a thought to the branch."""
        self.thoughts.append(thought)

    def add_cross_reference(
        self,
        source: Thought,
        target: Thought,
        relation_type: str,
        confidence: float = 0.5,
        rationale: str = "",
    ) -> CrossReference:
        """Add a cross-reference between two thoughts."""
        ref = CrossReference(
            source_thought_id=source.id,
            target_thought_id=target.id,
            relation_type=relation_type,
            confidence=confidence,
            rationale=rationale,
        )
        self.cross_references.append(ref)
        return ref


@dataclass
class ProcessingResult:
    """Result from reasoning engine processing."""

    conclusion: str
    thought_chain: ThoughtChain | None = None
    quality_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    # Mode-specific fields
    agent_outputs: dict[str, str] | None = None  # Multi-agent mode
    reasoning_output: str | None = None  # Two-stage mode
    coding_output: str | None = None  # Two-stage mode
    branch: ThoughtBranch | None = None  # Graph mode
