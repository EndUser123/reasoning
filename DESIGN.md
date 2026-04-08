# Unified Reasoning Package - Design Document

**Date:** 2026-03-10
**Status:** Phase 2 (Design) - In Progress
**Version:** 1.0

---

## Overview

**Package:** `packages/reasoning/` (Python 3.14)
**Purpose:** Unified reasoning engine consolidating 9 MCP packages into 1 cohesive system
**Philosophy:** Lean, stdlib-first, modular, extensible

---

## Architecture

### Core Components

```
packages/reasoning/
├── reasoning/
│   ├── __init__.py
│   ├── engine.py              # ReasoningEngine - main orchestrator
│   ├── modes/
│   │   ├── __init__.py
│   │   ├── base.py            # BaseMode interface
│   │   ├── multi_agent.py     # MultiAgentMode (6 agents)
│   │   ├── cognitive.py       # CognitiveEngineMode (Bloom's 6-stage)
│   │   ├── graph.py           # GraphMode (branches, cross-refs)
│   │   ├── two_stage.py       # TwoStageMode (reasoning → coding)
│   │   └── sequential.py      # SequentialMode (basic 5-stage)
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py            # Storage interface
│   │   ├── memory.py          # In-memory storage
│   │   └── file.py            # File-based storage (thread-safe)
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py            # LLM provider interface
│   │   ├── claude.py          # Claude API
│   │   ├── deepseek.py        # DeepSeek API
│   │   └── router.py          # LLM routing logic
│   ├── models/
│   │   ├── __init__.py
│   │   ├── thought.py         # Thought, ThoughtChain, ThoughtBranch
│   │   ├── state.py           # ProcessingState, QualityMetrics
│   │   └── config.py          # ReasoningConfig
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── complexity.py      # Complexity analysis
│   │   ├── quality.py         # Quality scoring
│   │   └── contradiction.py    # NLI contradiction detection
│   └── utils/
│       ├── __init__.py
│       ├── logging.py         # Logging setup
│       └── validation.py      # Input validation
├── tests/
│   ├── test_engine.py
│   ├── test_modes/
│   ├── test_storage/
│   └── test_llm/
├── examples/
│   ├── multi_agent_demo.py
│   ├── cognitive_demo.py
│   ├── graph_demo.py
│   └── two_stage_demo.py
├── pyproject.toml
├── README.md
└── DESIGN.md (this file)
```

---

## Core API Design

### ReasoningEngine (Main Orchestrator)

```python
from reasoning import ReasoningEngine, ReasoningConfig
from reasoning.modes import Mode

# Configure engine
config = ReasoningConfig(
    mode=Mode.MULTI_AGENT,
    llm_provider="claude",
    storage_backend="file",
    max_thoughts=50,
    quality_threshold=0.5,
)

# Initialize engine
engine = ReasoningEngine(config)

# Process thoughts
result = engine.think(
    prompt="Design a caching system for API responses",
    context={"requirements": ["< 200ms", "99.9% uptime"]}
)

# Access results
print(f"Final answer: {result.conclusion}")
print(f"Thoughts: {len(result.thought_chain)}")
print(f"Quality: {result.quality_score}")
```

### Mode Switching

```python
from reasoning.modes import Mode

# Multi-agent mode (6 specialized agents)
engine = ReasoningEngine(mode=Mode.MULTI_AGENT)

# Cognitive engine mode (Bloom's 6-stage + NLI + MCTS)
engine = ReasoningEngine(mode=Mode.COGNITIVE)

# Graph mode (branches, cross-refs)
engine = ReasoningEngine(mode=Mode.GRAPH)

# Two-stage mode (reasoning → coding)
engine = ReasoningEngine(mode=Mode.TWO_STAGE)

# Sequential mode (basic 5-stage)
engine = ReasoningEngine(mode=Mode.SEQUENTIAL)
```

---

## Mode Designs

### Mode 1: Multi-Agent Mode

**Source:** mcp-server-mas-sequential-thinking

**Features:**
- 6 specialized agents: Factual, Emotional, Critical, Optimistic, Creative, Synthesis
- AI-driven complexity analysis
- Parallel processing (asyncio.gather)
- Message history optimization (40-60% token reduction)
- Typed state management

**API:**

```python
from reasoning.modes import MultiAgentMode

mode = MultiAgentMode(
    agents=["factual", "emotional", "critical", "optimistic", "creative", "synthesis"],
    parallel_processing=True,
    message_history_limits={
        "factual": 5,
        "emotional": 0,
        "critical": 3,
        "optimistic": 3,
        "creative": 8,
        "synthesis": 10,
    }
)

result = mode.process(
    thought="Should we use Redis or Memcached for caching?",
    complexity="high"
)

# Access individual agent outputs
print(result.agent_outputs["factual"])  # Objective facts
print(result.agent_outputs["critical"]) # Risk assessment
print(result.agent_outputs["synthesis"]) # Integrated recommendation
```

**Implementation:**
- Keep existing Agno framework if it works
- Otherwise reimplement agents using our LLM abstraction layer

### Mode 2: Cognitive Engine Mode

**Source:** cuba-thinking (extract core algorithms)

**Features:**
- 6-stage Bloom's Taxonomy (DEFINE → RESEARCH → ANALYZE → HYPOTHESIZE → VERIFY → SYNTHESIZE)
- NLI contradiction detection (DeBERTa-v3-xsmall or API-based)
- MCTS forced backtracking
- Anti-hallucination checks (9 checks)
- Bias detection (5 types)
- Quality metrics (6D: TTR clarity, clause depth, structural logic, noun breadth, semantic relevance, concrete actionability)

**API:**

```python
from reasoning.modes import CognitiveEngineMode
from reasoning.models import ThoughtStage

mode = CognitiveEngineMode(
    stages=[
        ThoughtStage.DEFINE,
        ThoughtStage.RESEARCH,
        ThoughtStage.ANALYZE,
        ThoughtStage.HYPOTHESIZE,
        ThoughtStage.VERIFY,
        ThoughtStage.SYNTHESIZE,
    ],
    enable_nli_contradiction=True,
    enable_mcts_backtracking=True,
    enable_anti_hallucination=True,
)

result = mode.process(
    thought="DEFINE: We need to optimize database queries",
    stage=ThoughtStage.DEFINE,
    confidence=0.7,
    assumptions=["database is PostgreSQL", "queries are read-heavy"]
)

# Quality feedback
if result.quality_score < 0.5:
    print(f"Low quality: {result.quality_feedback}")
    # MCTS backtracking triggered automatically
```

**Implementation - Phase 1 (Core):**
- Implement 6-stage state machine
- Implement basic quality metrics (6D)
- Implement assumption tracking
- Implement confidence calibration

**Implementation - Phase 2 (Advanced - Optional):**
- Add NLI contradiction detection (API-based)
- Add MCTS backtracking algorithm
- Add bias detection
- Add CoVe (Chain-of-Verification)

### Mode 3: Graph Mode

**Source:** branch-thinking-mcp (extract graph algorithms)

**Features:**
- Branch management (create, focus, navigate)
- Cross-references between thoughts (typed, scored)
- Semantic search (API-based embeddings or keyword matching for v1)
- Basic graph algorithms (stdlib: collections, networkx)
- Visualization (optional, can add later)

**API:**

```python
from reasoning.modes import GraphMode

mode = GraphMode()

# Create branches
architecture_branch = mode.create_branch("architecture alternatives")
performance_branch = mode.create_branch("performance analysis")

# Add thoughts to branches
mode.add_thought(architecture_branch, "Option 1: Redis cluster")
mode.add_thought(architecture_branch, "Option 2: Memcached pool")

# Cross-reference
mode.add_cross_reference(
    source Thought=thought_1,
    target_thought=thought_2,
    relation_type="supports",
    confidence=0.9,
    rationale="Redis distribution supports horizontal scaling"
)

# Semantic search
related = mode.semantic_search("caching strategy", top_k=5)

# Visualization
mode.visualize(format="mermaid")  # Optional, can add later
```

**Implementation:**
- Use `collections.defaultdict` and `networkx` for graph structure
- Semantic search: Use OpenAI/DeepSeek embeddings API or skip for v1
- Visualization: Optional, can add mermaid generation later

### Mode 4: Two-Stage Mode

**Source:** mcp-reasoning-coding

**Features:**
- Configurable reasoning stage (DeepSeek R1, GPT-4, etc.)
- Configurable coding/response stage (Claude, GPT-4, etc.)
- Multi-provider support (simplified to Claude + DeepSeek)
- Conversation history tracking
- Response polling (async)

**API:**

```python
from reasoning.modes import TwoStageMode
from reasoning.llm import ClaudeProvider, DeepSeekProvider

mode = TwoStageMode(
    reasoning_provider=DeepSeekProvider(model="deepseek-reasoner"),
    coding_provider=ClaudeProvider(model="claude-3.5-sonnet"),
)

result = mode.process(
    prompt="Implement a Redis caching layer for API responses",
)

# Access stages
print(f"Reasoning: {result.reasoning_output}")
print(f"Code: {result.coding_output}")
```

**Implementation:**
- Implement LLM provider abstraction (Claude, DeepSeek)
- Implement async polling mechanism
- Implement conversation history tracking

---

## Storage Abstraction

### Interface

```python
from reasoning.storage import StorageBackend

class StorageBackend(Protocol):
    """Storage interface for reasoning persistence."""

    async def save_thought(self, thought: Thought) -> str:
        """Save thought and return ID."""
        ...

    async def load_thought(self, thought_id: str) -> Thought:
        """Load thought by ID."""
        ...

    async def save_branch(self, branch: ThoughtBranch) -> str:
        """Save branch and return ID."""
        ...

    async def load_branch(self, branch_id: str) -> ThoughtBranch:
        """Load branch by ID."""
        ...

    async def search(self, query: str, top_k: int = 5) -> list[Thought]:
        """Search for thoughts."""
        ...
```

### Implementations

**Memory Storage (default for tests):**
```python
from reasoning.storage import MemoryStorage

storage = MemoryStorage()
```

**File Storage (thread-safe, production):**
```python
from reasoning.storage import FileStorage

storage = FileStorage(
    base_path="~/.reasoning/storage",
    thread_safe=True,
)
```

---

## LLM Provider Abstraction

### Interface

```python
from reasoning.llm import LLMProvider

class LLMProvider(Protocol):
    """LLM provider interface."""

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate response from LLM."""
        ...

    async def generate_with_history(
        self,
        prompt: str,
        history: list[dict],
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate response with conversation history."""
        ...
```

### Implementations

**Claude Provider:**
```python
from reasoning.llm import ClaudeProvider

provider = ClaudeProvider(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-3.5-sonnet",
)
```

**DeepSeek Provider:**
```python
from reasoning.llm import DeepSeekProvider

provider = DeepSeekProvider(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    model="deepseek-reasoner",
)
```

---

## Data Models

### Thought

```python
from reasoning.models import Thought, ThoughtStage

thought = Thought(
    content="We should use Redis for distributed caching",
    stage=ThoughtStage.SYNTHESIS,
    thought_number=5,
    confidence=0.85,
    assumptions=["Network latency is acceptable"],
    metadata={"branch_id": "arch-001"},
)
```

### ThoughtChain

```python
from reasoning.models import ThoughtChain

chain = ThoughtChain(
    thoughts=[thought1, thought2, thought3],
    metadata={"mode": "cognitive", "total_steps": 10},
)
```

### ThoughtBranch

```python
from reasoning.models import ThoughtBranch

branch = ThoughtBranch(
    id="arch-001",
    name="architecture alternatives",
    thoughts=[thought1, thought2],
    cross_references=[ref1, ref2],
)
```

---

## Configuration

### ReasoningConfig

```python
from reasoning import ReasoningConfig, Mode

config = ReasoningConfig(
    mode=Mode.COGNITIVE,
    llm_provider="claude",
    storage_backend="file",
    storage_path="~/.reasoning/storage",
    max_thoughts=50,
    quality_threshold=0.5,
    enable_logging=True,
    log_level="INFO",
)
```

---

## Implementation Phases

### Phase 1: Core Engine (Week 1-2)
- [ ] Implement ReasoningEngine orchestrator
- [ ] Implement mode switching logic
- [ ] Implement base mode interface
- [ ] Implement storage abstraction (memory + file)
- [ ] Implement LLM provider abstraction (Claude + DeepSeek)
- [ ] Implement core data models (Thought, ThoughtChain, ThoughtBranch)
- [ ] Write basic tests

### Phase 2: Sequential Mode (Week 2-3)
- [ ] Implement SequentialMode (basic 5-stage)
- [ ] Implement thought tracking
- [ ] Implement progress monitoring
- [ ] Write tests

### Phase 3: Multi-Agent Mode (Week 3-4)
- [ ] Keep existing mcp-server-mas-sequential-thinking as-is
- [ ] Create integration layer
- [ ] Write integration tests

### Phase 4: Cognitive Engine Mode - Core (Week 4-5)
- [ ] Implement 6-stage Bloom's state machine
- [ ] Implement basic quality metrics (6D)
- [ ] Implement assumption tracking
- [ ] Implement confidence calibration
- [ ] Write tests

### Phase 5: Graph Mode (Week 5-6)
- [ ] Implement graph structure (stdlib/networkx)
- [ ] Implement branch management
- [ ] Implement cross-references
- [ ] Implement basic semantic search (keyword or API)
- [ ] Write tests

### Phase 6: Two-Stage Mode (Week 6-7)
- [ ] Implement two-stage orchestrator
- [ ] Implement LLM routing (reasoning → coding)
- [ ] Implement async polling
- [ ] Write tests

### Phase 7: Advanced Features (Optional, Week 7-8)
- [ ] Add NLI contradiction detection (API-based)
- [ ] Add MCTS backtracking algorithm
- [ ] Add graph visualization (mermaid)
- [ ] Add bias detection
- [ ] Write integration tests

### Phase 8: Integration & Cleanup (Week 8-9)
- [ ] Update skills to use new package
- [ ] Remove duplicate MCP packages
- [ ] Write migration guide
- [ ] Update documentation
- [ ] Performance benchmarking
- [ ] Git commit

---

## Dependencies

### MUST (Stdlib)
- `collections` - Graph structures, defaultdict
- `dataclasses` - Type-safe models
- `json` - Serialization
- `threading` - Thread safety
- `asyncio` - Async processing
- `pathlib` - File paths
- `enum` - Enums (Stage, Mode)

### SHOULD (Minimal External)
- `pydantic` - Data validation
- `networkx` - Graph algorithms (optional, can use stdlib)
- API keys for LLM providers (already have)

### MAY (Optional Enhancements)
- `openai` - Embeddings API for semantic search
- `anthropic` - Claude API (already using)
- `transformers` - Local NLI model (optional, heavy)

---

## Open Questions

1. **Agno framework** - Keep mcp-server-mas-sequential-thinking as-is or reimplement?
2. **Semantic search** - Use OpenAI embeddings API or keyword matching for v1?
3. **NLI contradiction** - Use API or skip for v1?
4. **Graph visualization** - Include mermaid generation or skip for v1?
5. **MCTS complexity** - Full MCTS or simplified backtracking?

---

**Next Steps:**
1. User review and approval
2. Begin Phase 1 (Core Engine)
3. Create pyproject.toml
4. Implement basic structure
5. Write first tests

**Task Tracking:** #1624
**Status:** Phase 2 (Design) - ✅ COMPLETE
