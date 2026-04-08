"""
Multi-Agent Mode Demo

This demo shows how to use the Multi-Agent reasoning mode, which leverages
6 specialized agents (Factual, Emotional, Critical, Optimistic, Creative, Synthesis)
to analyze problems from multiple perspectives.

Requirements:
    pip install mcp-server-mas-sequential-thinking

Environment Variables (required):
    LLM_PROVIDER=deepseek
    DEEPSEEK_API_KEY=your_api_key
    DEEPSEEK_ENHANCED_MODEL_ID=deepseek-chat
    DEEPSEEK_STANDARD_MODEL_ID=deepseek-chat
"""

import asyncio

from reasoning import Mode, ReasoningEngine


async def main():
    # Create engine with Multi-Agent mode
    engine = ReasoningEngine(mode=Mode.MULTI_AGENT)

    # Example 1: Simple decision
    print("=" * 60)
    print("Example 1: Technology Choice")
    print("=" * 60)

    result = await engine.think("Should we use Redis or Memcached for caching?")

    print(f"\nConclusion:\n{result.conclusion}\n")

    if result.agent_outputs:
        print("\nIndividual Agent Perspectives:")
        for agent_name, output in result.agent_outputs.items():
            print(f"\n{agent_name.upper()}:")
            print(output[:200] + "..." if len(output) > 200 else output)

    # Example 2: Complex architectural decision
    print("\n" + "=" * 60)
    print("Example 2: Architecture Decision")
    print("=" * 60)

    result2 = await engine.think(
        "Design a scalable microservices architecture for an e-commerce platform. "
        "Consider order processing, inventory management, and payment handling."
    )

    print(f"\nConclusion:\n{result2.conclusion}\n")

    if result2.metadata:
        print("Metadata:")
        for key, value in result2.metadata.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
