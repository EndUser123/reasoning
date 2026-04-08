"""In-memory storage backend for reasoning persistence."""


from reasoning.models import Thought, ThoughtBranch
from reasoning.storage.base import StorageBackend


class MemoryStorage(StorageBackend):
    """In-memory storage for thoughts and branches."""

    def __init__(self) -> None:
        """Initialize empty in-memory storage."""
        self._thoughts: dict[str, Thought] = {}
        self._branches: dict[str, ThoughtBranch] = {}
        self._counter: int = 0

    def _generate_id(self) -> str:
        """Generate a unique ID for stored items."""
        self._counter += 1
        return f"mem_{self._counter}"

    async def save_thought(self, thought: Thought) -> str:
        """
        Save thought and return ID.

        Args:
            thought: Thought to save

        Returns:
            Unique ID for saved thought
        """
        thought_id = self._generate_id()
        self._thoughts[thought_id] = thought
        return thought_id

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
        if thought_id not in self._thoughts:
            raise KeyError(f"Thought not found: {thought_id}")
        return self._thoughts[thought_id]

    async def save_branch(self, branch: ThoughtBranch) -> str:
        """
        Save branch and return ID.

        Args:
            branch: ThoughtBranch to save

        Returns:
            Unique ID for saved branch
        """
        branch_id = self._generate_id()
        self._branches[branch_id] = branch
        return branch_id

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
        if branch_id not in self._branches:
            raise KeyError(f"Branch not found: {branch_id}")
        return self._branches[branch_id]

    async def search(self, query: str, top_k: int = 5) -> list[Thought]:
        """
        Search for thoughts by content.

        Args:
            query: Search query string
            top_k: Maximum number of results to return

        Returns:
            List of thoughts matching query (max top_k items)
        """
        query_lower = query.lower()
        matching_thoughts = [
            thought
            for thought in self._thoughts.values()
            if query_lower in thought.content.lower()
        ]
        return matching_thoughts[:top_k]

    async def clear(self) -> None:
        """Clear all stored data."""
        self._thoughts.clear()
        self._branches.clear()
        self._counter = 0
