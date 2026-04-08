"""Tests for LLM provider abstraction."""

import pytest
from reasoning.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response: str = "Mock response") -> None:
        self.response = response
        self.generate_called = False
        self.generate_with_history_called = False

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate mock response."""
        self.generate_called = True
        return self.response

    async def generate_with_history(
        self,
        prompt: str,
        history: list[dict],
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate mock response with history."""
        self.generate_with_history_called = True
        return f"{self.response} (with {len(history)} messages)"


@pytest.fixture
def mock_provider():
    """Create a mock provider for testing."""
    return MockLLMProvider()


@pytest.mark.asyncio
async def test_generate_returns_response(mock_provider):
    """Test that generate returns a non-empty response."""
    response = await mock_provider.generate("Test prompt")
    assert response == "Mock response"
    assert mock_provider.generate_called is True


@pytest.mark.asyncio
async def test_generate_with_history_includes_history(mock_provider):
    """Test that generate_with_history processes history."""
    history = [{"role": "user", "content": "Previous message"}]
    response = await mock_provider.generate_with_history("Test prompt", history)
    assert "with 1 messages" in response
    assert mock_provider.generate_with_history_called is True


@pytest.mark.asyncio
async def test_generate_with_max_tokens(mock_provider):
    """Test that generate respects max_tokens parameter."""
    response = await mock_provider.generate("Test prompt", max_tokens=100)
    assert response == "Mock response"


@pytest.mark.asyncio
async def test_generate_with_temperature(mock_provider):
    """Test that generate respects temperature parameter."""
    response = await mock_provider.generate("Test prompt", temperature=0.5)
    assert response == "Mock response"
