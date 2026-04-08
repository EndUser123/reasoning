"""Tests for MemoryStorage backend."""

import pytest

from reasoning.models import Thought, ThoughtBranch, ThoughtStage
from reasoning.storage.memory import MemoryStorage


@pytest.fixture
def storage():
    """Create a fresh MemoryStorage instance for each test."""
    return MemoryStorage()


@pytest.fixture
def sample_thought():
    """Create a sample thought for testing."""
    return Thought(
        content="Test thought content",
        stage=ThoughtStage.ANALYSIS,
        thought_number=1,
        total_thoughts=5,
        confidence=0.8,
    )


@pytest.mark.asyncio
async def test_save_thought_returns_id(storage, sample_thought):
    """Test that saving a thought returns a valid ID."""
    thought_id = await storage.save_thought(sample_thought)
    assert thought_id is not None
    assert isinstance(thought_id, str)
    assert len(thought_id) > 0


@pytest.mark.asyncio
async def test_save_and_load_thought(storage, sample_thought):
    """Test that a saved thought can be loaded and has the same content."""
    thought_id = await storage.save_thought(sample_thought)
    loaded_thought = await storage.load_thought(thought_id)

    assert loaded_thought.content == sample_thought.content
    assert loaded_thought.stage == sample_thought.stage
    assert loaded_thought.thought_number == sample_thought.thought_number
    assert loaded_thought.confidence == sample_thought.confidence


@pytest.mark.asyncio
async def test_load_nonexistent_thought_raises_error(storage):
    """Test that loading a non-existent thought raises KeyError."""
    with pytest.raises(KeyError, match="Thought not found"):
        await storage.load_thought("nonexistent-id")


@pytest.mark.asyncio
async def test_save_branch_returns_id(storage):
    """Test that saving a branch returns a valid ID."""
    branch = ThoughtBranch(id="test-branch", name="Test Branch")
    branch_id = await storage.save_branch(branch)
    assert branch_id is not None
    assert isinstance(branch_id, str)
    assert len(branch_id) > 0


@pytest.mark.asyncio
async def test_save_and_load_branch(storage, sample_thought):
    """Test that a saved branch can be loaded and has the same content."""
    branch = ThoughtBranch(id="test-branch", name="Test Branch")
    branch.add_thought(sample_thought)

    branch_id = await storage.save_branch(branch)
    loaded_branch = await storage.load_branch(branch_id)

    assert loaded_branch.id == branch.id
    assert loaded_branch.name == branch.name
    assert len(loaded_branch.thoughts) == len(branch.thoughts)
    assert loaded_branch.thoughts[0].content == sample_thought.content


@pytest.mark.asyncio
async def test_load_nonexistent_branch_raises_error(storage):
    """Test that loading a non-existent branch raises KeyError."""
    with pytest.raises(KeyError, match="Branch not found"):
        await storage.load_branch("nonexistent-id")


@pytest.mark.asyncio
async def test_search_finds_matching_thoughts(storage, sample_thought):
    """Test that search finds thoughts with matching content."""
    await storage.save_thought(sample_thought)

    results = await storage.search("Test")
    assert len(results) >= 1
    assert any(thought.content == sample_thought.content for thought in results)


@pytest.mark.asyncio
async def test_search_returns_empty_for_no_matches(storage):
    """Test that search returns empty list when no thoughts match."""
    results = await storage.search("nonexistent content")
    assert results == []


@pytest.mark.asyncio
async def test_clear_storage(storage, sample_thought):
    """Test that clear removes all stored data."""
    await storage.save_thought(sample_thought)
    await storage.clear()

    results = await storage.search("Test")
    assert results == []
