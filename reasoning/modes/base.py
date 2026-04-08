"""
Base mode interface for reasoning modes.
"""

from abc import ABC, abstractmethod
from typing import Any

from reasoning.config import ReasoningConfig
from reasoning.models import ProcessingResult


class BaseMode(ABC):
    """Base interface for all reasoning modes."""

    def __init__(self, config: ReasoningConfig):
        """Initialize mode with configuration."""
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate mode-specific configuration. Override in subclasses."""
        pass

    @abstractmethod
    async def process(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ProcessingResult:
        """
        Process a reasoning prompt.

        Args:
            prompt: The reasoning prompt
            context: Additional context
            **kwargs: Mode-specific parameters

        Returns:
            ProcessingResult with conclusion and metadata
        """
        ...

    @abstractmethod
    def validate_input(self, prompt: str) -> bool:
        """Validate input prompt. Return True if valid."""
        ...

    def get_mode_name(self) -> str:
        """Get the name of this mode."""
        return self.__class__.__name__
