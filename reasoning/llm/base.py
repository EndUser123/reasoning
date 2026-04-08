"""LLM provider interface for reasoning engine."""

from typing import Protocol


class LLMProvider(Protocol):
    """LLM provider interface for generating responses."""

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response from LLM.

        Args:
            prompt: Input prompt for LLM
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated response text
        """
        ...

    async def generate_with_history(
        self,
        prompt: str,
        history: list[dict],
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response with conversation history.

        Args:
            prompt: Current prompt
            history: Previous conversation history
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated response text
        """
        ...
