#!/usr/bin/env python3
"""Demo script showing what users will see when reasoning is active."""

import sys

# Add packages to path
sys.path.insert(0, "P:/packages/reasoning")
sys.path.insert(0, "P:/.claude/hooks")

def demo_reasoning_mode_selector():
    """Show UserPromptSubmit reasoning mode selector output."""
    print("=" * 60)
    print("DEMO 1: Reasoning Mode Selector (UserPromptSubmit)")
    print("=" * 60)
    print("\nYour prompt:")
    print("  'Should I use Docker or Podman for containerization?'")
    print("\nWhat you'll see:")
    print("""
**🤖 Multi-Agent Reasoning** (confidence: 1/4)
This query will use multi agent reasoning.

[AI then processes your query with multi-agent reasoning approach]
""")
    print()


def demo_enhanced_reasoning():
    """Show Stop hook enhanced reasoning output."""
    print("=" * 60)
    print("DEMO 2: Enhanced Reasoning (Stop Hook)")
    print("=" * 60)
    print("\nOriginal AI response:")
    print("  'The microservices architecture offers several advantages...'")
    print("\nWhat you'll see:")
    print("""
**🔄 Enhanced Reasoning Applied**

Response improved through Generate → Critique → Improve loop.

Conclude: The microservices architecture offers several advantages for scaling
and deployment. Each service can be developed, deployed, and scaled independently.
This allows teams to work on different services simultaneously without stepping
on each other's toes. The downside is increased complexity in terms of service
communication, data consistency, and operational overhead...
""")
    print()


def demo_multi_agent_reasoning():
    """Show PreToolUse multi-agent reasoning output."""
    print("=" * 60)
    print("DEMO 3: Multi-Agent Reasoning (PreToolUse)")
    print("=" * 60)
    print("\nTool query:")
    print("  'Compare PostgreSQL vs MongoDB for time-series data'")
    print("\nWhat you'll see:")
    print("""
**🤖 Multi-Agent Reasoning Applied**
Ran 6 parallel agents to analyze this decision from multiple perspectives.

[Factual Agent]: PostgreSQL offers ACID compliance and relational schema, while
MongoDB provides flexible document storage with horizontal scaling...

[Emotional Agent]: PostgreSQL feels more reliable for critical data, while MongoDB
offers excitement through flexibility and rapid iteration...

[Critical Agent]: Consider that PostgreSQL's row-based storage may struggle with
high-volume time-series writes, while MongoDB's document model fits naturally...

[Optimistic Agent]: Both can work well! PostgreSQL with TimescaleDB extension gives
you the best of both worlds - relational reliability with time-series optimization...

[Creative Agent]: Have you considered hybrid approaches? Use PostgreSQL for
metadata and MongoDB for raw time-series data, or invert based on access patterns...

[Synthesis Agent]: **Recommendation**: For time-series data with ACID requirements,
start with PostgreSQL + TimescaleDB extension. This preserves relational guarantees
while optimizing for time-series workloads...

[Tool execution continues with multi-agent insights...]
""")
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print(" REASONING HOOKS - USER VISIBILITY DEMO")
    print("=" * 60 + "\n")

    demo_reasoning_mode_selector()
    demo_enhanced_reasoning()
    demo_multi_agent_reasoning()

    print("=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    print("""
You'll notice reasoning is active when you see:

1. 🤖 Multi-Agent symbol → Multiple AI agents analyzing your query
2. 🔄 Enhanced symbol → Response improved through self-reflection
3. Mode badges (Sequential, Multi-Agent, Graph, Two-Stage)

These appear automatically based on query complexity and response length.
No manual activation needed - the hooks detect when to apply reasoning.

To disable: Set environment variables (see user_visibility_demo.md)
""")


if __name__ == "__main__":
    main()
