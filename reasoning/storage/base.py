"""Storage backend interface for reasoning persistence."""

from typing import Protocol

from reasoning.models import Thought, ThoughtBranch


class StorageBackend(Protocol):
    """Storage interface for reasoning persistence."""

    async def save_thought(self, thought: Thought) -> str:
        """
        Save thought and return ID.

        Args:
            thought: Thought to save

        Returns:
            Unique ID for saved thought
        """
        ...

    async def load_thought(self, thought_id: str) -> Thought:
        """
        Load thought by ID.

        Args:
            thought_id: Unique ID of thought to load

        Returns:
            Thought with matching ID

        Raises:
            KeyError: If thought_id not found
        """
        ...

    async def save_branch(self, branch: ThoughtBranch) -> str:
        """
        Save branch and return ID.

        Args:
            branch: ThoughtBranch to save

        Returns:
            Unique ID for saved branch
        """
        ...

    async def load_branch(self, branch_id: str) -> ThoughtBranch:
        """
        Load branch by ID.

        Args:
            branch_id: Unique ID of branch to load

        Returns:
            ThoughtBranch with matching ID

        Raises:
            KeyError: If branch_id not found
        """
        ...

    async def search(self, query: str, top_k: int = 5) -> list[Thought]:
        """
        Search for thoughts by content.

        Args:
            query: Search query string
            top_k: Maximum number of results to return

        Returns:
            List of thoughts matching query (max top_k items)
        """
        ...

    async def clear(self) -> None:
        """Clear all stored data."""
        ...
