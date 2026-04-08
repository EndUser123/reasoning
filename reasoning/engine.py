"""Main orchestrator for reasoning engine."""

from reasoning.config import ReasoningConfig
from reasoning.models import Mode, ProcessingResult
from reasoning.modes.base import BaseMode
from reasoning.modes.cognitive import CognitiveMode
from reasoning.modes.graph import GraphMode
from reasoning.modes.multi_agent import MultiAgentMode
from reasoning.modes.sequential import SequentialMode
from reasoning.modes.two_stage import TwoStageMode


class ReasoningEngine:
    """Main orchestrator for reasoning modes."""

    def __init__(self, config: ReasoningConfig | None = None) -> None:
        """
        Initialize reasoning engine with configuration.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or ReasoningConfig()
        self._mode = self._create_mode()

    def _create_mode(self) -> BaseMode:
        """Create mode instance based on configuration."""
        mode_map = {
            Mode.SEQUENTIAL: SequentialMode,
            Mode.MULTI_AGENT: MultiAgentMode,  # Integrated (Phase 4)
            Mode.COGNITIVE: CognitiveMode,  # Placeholder (Phase 5)
            Mode.GRAPH: GraphMode,  # Placeholder (Phase 6)
            Mode.TWO_STAGE: TwoStageMode,  # Placeholder (Phase 7)
        }

        mode_class = mode_map.get(self.config.mode, SequentialMode)
        return mode_class(self.config)  # type: ignore[abstract]

    async def think(
        self,
        prompt: str,
        context: dict[str, object] | None = None,
        **kwargs: object,
    ) -> ProcessingResult:
        """
        Process a reasoning prompt using the configured mode.

        Args:
            prompt: The reasoning prompt
            context: Additional context
            **kwargs: Mode-specific parameters

        Returns:
            ProcessingResult with conclusion and metadata
        """
        return await self._mode.process(prompt, context, **kwargs)
