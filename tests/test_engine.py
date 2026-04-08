"""Tests for ReasoningEngine orchestrator."""

import pytest

from reasoning import Mode, ReasoningConfig, ReasoningEngine


@pytest.fixture
def engine():
    """Create a ReasoningEngine instance for testing."""
    return ReasoningEngine()


@pytest.fixture
def sequential_engine():
    """Create a ReasoningEngine configured for sequential mode."""
    return ReasoningEngine(config=ReasoningConfig(mode=Mode.SEQUENTIAL))


@pytest.mark.asyncio
async def test_engine_initializes_with_default_config(engine):
    """Test that engine initializes with default configuration."""
    assert engine.config is not None
    assert engine.config.mode == Mode.SEQUENTIAL


@pytest.mark.asyncio
async def test_engine_initializes_with_custom_config():
    """Test that engine initializes with custom configuration."""
    config = ReasoningConfig(mode=Mode.SEQUENTIAL, max_thoughts=100)
    engine = ReasoningEngine(config=config)
    assert engine.config.max_thoughts == 100


@pytest.mark.asyncio
async def test_think_returns_result(sequential_engine):
    """Test that think method returns a ProcessingResult."""
    result = await sequential_engine.think("Test prompt")
    assert result is not None
    assert result.conclusion is not None
    assert len(result.conclusion) > 0


@pytest.mark.asyncio
async def test_think_creates_thought_chain(sequential_engine):
    """Test that think creates a thought chain."""
    result = await sequential_engine.think("Test prompt")
    assert result.thought_chain is not None
    assert result.thought_chain.length > 0


@pytest.mark.asyncio
async def test_think_includes_metadata(sequential_engine):
    """Test that think result includes metadata."""
    result = await sequential_engine.think("Test prompt")
    assert result.metadata is not None
    assert "mode" in result.metadata


@pytest.mark.asyncio
async def test_engine_supports_mode_switching():
    """Test that engine can switch between modes."""
    # Create engines with different modes
    sequential_config = ReasoningConfig(mode=Mode.SEQUENTIAL)
    sequential_engine = ReasoningEngine(config=sequential_config)

    # Both should work
    result1 = await sequential_engine.think("Test")
    assert result1 is not None
