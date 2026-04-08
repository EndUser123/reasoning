"""Multi-agent reasoning mode using MAS package integration."""

from typing import TYPE_CHECKING

from reasoning.config import ReasoningConfig
from reasoning.models import ProcessingResult
from reasoning.modes.base import BaseMode

if TYPE_CHECKING:
    pass


class MultiAgentMode(BaseMode):
    """Multi-agent reasoning mode using MAS package integration.

    This mode wraps the existing mcp-server-mas-sequential-thinking package
    to provide 6-agent parallel processing (Factual, Emotional, Critical,
    Optimistic, Creative, Synthesis).

    The MAS package is kept as-is; this is a thin integration layer.
    """

    def __init__(self, config: ReasoningConfig) -> None:
        """Initialize multi-agent mode with configuration."""
        super().__init__(config)
        self._processor: object | None = None  # Lazy-loaded MAS processor

    def validate_input(self, prompt: str) -> bool:
        """Validate input prompt. Return True if valid."""
        return bool(prompt and prompt.strip())

    async def process(
        self,
        prompt: str,
        context: dict[str, object] | None = None,
        **kwargs: object,
    ) -> ProcessingResult:
        """
        Process a reasoning prompt using multi-agent workflow.

        Args:
            prompt: The reasoning prompt
            context: Additional context (passed to MAS as metadata)
            **kwargs: Mode-specific parameters (e.g., timeout)

        Returns:
            ProcessingResult with conclusion and agent_outputs from all 6 agents

        Raises:
            ImportError: If MAS package is not installed
            ValueError: If MAS configuration is invalid (missing API keys)
        """
        if not self.validate_input(prompt):
            raise ValueError("Invalid prompt: must be non-empty")

        # Lazy load MAS processor
        if self._processor is None:
            self._processor = self._create_mas_processor()

        # Convert to MAS format
        thought_data = self._convert_to_mas_format(prompt, context)

        # Call MAS processor
        mas_result = await self._call_mas_processor(thought_data)

        # Convert back to our format
        return self._convert_from_mas_format(mas_result)

    def _create_mas_processor(self) -> object:
        """Create MAS processor instance.

        Returns:
            MultiThinkingSequentialProcessor instance

        Raises:
            ImportError: If MAS package is not installed
            ValueError: If MAS configuration is invalid
        """
        try:
            from mcp_server_mas_sequential_thinking.processors.multi_thinking_processor import (  # type: ignore[import-not-found]
                MultiThinkingSequentialProcessor,
            )

            return MultiThinkingSequentialProcessor()

        except ImportError as e:
            raise ImportError(
                "MAS package not installed. "
                "Install from: packages/.mcp/mcp-server-mas-sequential-thinking\n"
                f"Error: {e}"
            ) from e

    def _convert_to_mas_format(self, prompt: str, context: dict[str, object] | None) -> object:
        """Convert our prompt format to MAS ThoughtData format.

        Args:
            prompt: Our prompt string
            context: Optional context dict

        Returns:
            ThoughtData instance for MAS package
        """
        from mcp_server_mas_sequential_thinking.core.models import (
            ThoughtData,  # type: ignore[import-not-found]
        )

        return ThoughtData(
            thought=prompt,
            thoughtNumber=1,
            totalThoughts=1,
            nextThoughtNeeded=False,
            isRevision=False,
            branchFromThought=None,
            branchId=None,
            needsMoreThoughts=False,
        )

    async def _call_mas_processor(self, thought_data: object) -> object:
        """Call MAS processor and return result.

        Args:
            thought_data: ThoughtData instance

        Returns:
            MultiThinkingProcessingResult instance
        """
        if self._processor is None:
            raise RuntimeError("MAS processor not initialized")

        # Call process_with_multi_thinking with forced full exploration
        result = await self._processor.process_with_multi_thinking(  # type: ignore[attr-defined]
            thought_data=thought_data,
            forced_strategy_name="full_exploration",  # Use all 6 agents
            complexity_metrics=None,
        )

        return result

    def _convert_from_mas_format(self, mas_result: object) -> ProcessingResult:
        """Convert MAS result to our ProcessingResult format.

        Args:
            mas_result: MultiThinkingProcessingResult instance

        Returns:
            ProcessingResult with agent_outputs
        """
        # Extract fields from MAS result
        raw_content = getattr(mas_result, "content", "")
        strategy_used = getattr(mas_result, "strategy_used", "unknown")
        complexity_score = getattr(mas_result, "complexity_score", 0.0)
        individual_results = getattr(mas_result, "individual_results", {})

        # Normalize complexity_score to 0-1 range (assuming MAS uses 0-10)
        quality_score = min(complexity_score / 10.0, 1.0)

        # Prepend reasoning tag for visibility
        content = f"[MAS]\n\n{raw_content}"

        return ProcessingResult(
            conclusion=content,
            thought_chain=None,  # MAS uses different structure
            quality_score=quality_score,
            agent_outputs=individual_results,  # dict[str, str] from each agent
            metadata={
                "mode": "multi_agent",
                "strategy": strategy_used,
                "complexity_score": complexity_score,
            },
        )
