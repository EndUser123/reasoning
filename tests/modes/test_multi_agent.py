"""Tests for MultiAgentMode wrapper."""

import importlib.util

import pytest

from reasoning import ReasoningConfig, ReasoningEngine
from reasoning.models import Mode

# Check if MAS package is available
MAS_AVAILABLE = importlib.util.find_spec("mcp_server_mas_sequential_thinking") is not None


@pytest.fixture
def multi_agent_engine():
    """Create a ReasoningEngine configured for multi-agent mode."""
    return ReasoningEngine(config=ReasoningConfig(mode=Mode.MULTI_AGENT))


class TestMultiAgentMode:
    """Test MultiAgentMode integration with MAS package."""

    @pytest.mark.asyncio
    async def test_engine_initializes_with_multi_agent_mode(self, multi_agent_engine):
        """Test that engine initializes with multi-agent configuration."""
        assert multi_agent_engine.config is not None
        assert multi_agent_engine.config.mode == Mode.MULTI_AGENT

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MAS_AVAILABLE, reason="MAS package not installed (optional dependency)"
    )
    async def test_think_returns_result(self, multi_agent_engine):
        """Test that think() returns a ProcessingResult."""
        # This test requires MAS package and API keys to be configured
        result = await multi_agent_engine.think("Test prompt")

        assert result is not None
        assert isinstance(result.conclusion, str)
        assert len(result.conclusion) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MAS_AVAILABLE, reason="MAS package not installed (optional dependency)"
    )
    async def test_think_includes_agent_outputs(self, multi_agent_engine):
        """Test that result includes individual agent outputs."""
        result = await multi_agent_engine.think("Should we use Redis or Memcached?")

        assert result.agent_outputs is not None
        assert isinstance(result.agent_outputs, dict)

        # Check for expected agents (may vary based on complexity analysis)
        expected_agents = ["factual", "emotional", "critical", "optimistic", "creative", "synthesis"]
        for agent in expected_agents:
            # Not all agents may be present depending on routing decision
            if agent in result.agent_outputs:
                assert isinstance(result.agent_outputs[agent], str)
                assert len(result.agent_outputs[agent]) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MAS_AVAILABLE, reason="MAS package not installed (optional dependency)"
    )
    async def test_think_includes_metadata(self, multi_agent_engine):
        """Test that result includes processing metadata."""
        result = await multi_agent_engine.think("Analyze the trade-offs between SQL and NoSQL")

        assert result.metadata is not None
        assert "mode" in result.metadata
        assert result.metadata["mode"] == "multi_agent"

    @pytest.mark.asyncio
    async def test_think_raises_import_error_when_mas_unavailable(self, multi_agent_engine):
        """Test that think() raises ImportError when MAS package is not installed."""
        if MAS_AVAILABLE:
            pytest.skip("MAS package is installed, cannot test ImportError")

        with pytest.raises(ImportError, match="MAS package not installed"):
            await multi_agent_engine.think("Test prompt")

    @pytest.mark.asyncio
    async def test_validate_input_accepts_valid_prompt(self, multi_agent_engine):
        """Test that validate_input accepts non-empty prompts."""
        mode = multi_agent_engine._mode
        assert mode.validate_input("Valid prompt")

    @pytest.mark.asyncio
    async def test_validate_input_rejects_empty_prompt(self, multi_agent_engine):
        """Test that validate_input rejects empty prompts."""
        mode = multi_agent_engine._mode
        assert not mode.validate_input("")

    @pytest.mark.asyncio
    async def test_get_mode_name(self, multi_agent_engine):
        """Test that get_mode_name returns correct mode name."""
        mode = multi_agent_engine._mode
        assert mode.get_mode_name() == "MultiAgentMode"
