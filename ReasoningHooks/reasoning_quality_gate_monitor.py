#!/usr/bin/env python3
"""
Reasoning Quality Gate Monitor

Tracks quality gate statistics and performance metrics for the
automatic reasoning quality gate. Integrates with /main and /hook-audit
for centralized visibility.

NOTE: This monitors the reasoning quality gate, NOT the /reflect skill.
- /reflect skill analyzes conversation transcripts for learning
- Reasoning quality gate improves individual response quality in real-time

Usage:
    python reasoning_quality_gate_monitor.py --stats        # Show statistics
    python reasoning_quality_gate_monitor.py --health       # Health check
    python reasoning_quality_gate_monitor.py --recent 50    # Recent entries
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

LOG_FILE = Path("P:/packages/reasoning/hook_usage.log")


def load_logs(hours: int = 24) -> List[Dict]:
    """Load logs from the specified time period.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        List of log entries
    """
    if not LOG_FILE.exists():
        return []

    cutoff_time = datetime.now().timestamp() - (hours * 3600)
    logs = []

    try:
        with LOG_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("timestamp", 0) >= cutoff_time:
                        logs.append(entry)
                except (json.JSONDecodeError, KeyError):
                    continue
    except OSError:
        return []

    return logs


def calculate_statistics(logs: List[Dict]) -> Dict:
    """Calculate quality gate statistics from logs.

    Args:
        logs: List of log entries

    Returns:
        Dictionary with statistics
    """
    if not logs:
        return {
            "total": 0,
            "passed": 0,
            "issues_found": 0,
            "pass_rate": 0.0,
            "avg_response_length": 0,
            "issue_distribution": {},
        }

    total = len(logs)
    passed = sum(1 for log in logs if log.get("result") == "passed")
    issues_found = total - passed

    # Calculate average response length
    response_lengths = [log.get("response_length", 0) for log in logs]
    avg_length = sum(response_lengths) // len(response_lengths) if response_lengths else 0

    # Issue distribution (by result type)
    result_distribution = Counter(log.get("result", "unknown") for log in logs)

    return {
        "total": total,
        "passed": passed,
        "issues_found": issues_found,
        "pass_rate": round((passed / total * 100) if total > 0 else 0, 1),
        "avg_response_length": avg_length,
        "result_distribution": dict(result_distribution),
    }


def show_statistics(logs: List[Dict]) -> None:
    """Display quality gate statistics.

    Args:
        logs: List of log entries
    """
    stats = calculate_statistics(logs)

    print("\n" + "=" * 60)
    print("Reasoning Quality Gate Statistics")
    print("=" * 60)

    if stats["total"] == 0:
        print("\nNo data available for the specified time period.")
        print("The quality gate may not be triggered yet.")
        return

    print(f"\nTotal evaluations: {stats['total']}")
    print(f"Passed: {stats['passed']} ({stats['pass_rate']}%)")
    print(f"Issues found: {stats['issues_found']} ({100 - stats['pass_rate']}%)")
    print(f"\nAverage response length: {stats['avg_response_length']} chars")

    if stats["result_distribution"]:
        print("\nResult distribution:")
        for result, count in stats["result_distribution"].items():
            percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  • {result}: {count} ({percentage:.1f}%)")

    print("\n" + "=" * 60)


def check_health(logs: List[Dict]) -> int:
    """Check health of the quality gate system.

    Args:
        logs: List of log entries

    Returns:
        Exit code (0 = healthy, 1 = warning, 2 = critical)
    """
    stats = calculate_statistics(logs)

    if stats["total"] == 0:
        print("\n⚠️  WARNING: No quality gate activity detected")
        print("\nPossible causes:")
        print("  • Hook not triggered yet (normal for new installations)")
        print("  • Responses not passing keyword filter")
        print("  • Hook not registered in Stop router")
        print("\nTo verify registration:")
        print("  grep -r 'self_reflection' P:/.claude/hooks/Stop.py")
        return 1

    # Check if quality gate is too strict (100% failure rate)
    if stats["pass_rate"] == 0 and stats["total"] >= 10:
        print("\n🚨 CRITICAL: Quality gate rejecting ALL responses")
        print(f"\n   {stats['total']} evaluations, 0 passed")
        print("\n   This may indicate:")
        print("     • Quality threshold too sensitive (<1 issue)")
        print("     • Critique patterns too aggressive")
        print("     • All responses actually have issues (unlikely)")
        print("\n   Recommendations:")
        print("     • Review recent logs for false positives")
        print("     • Consider adjusting threshold in sequential.py")
        print("     • Check critique pattern specificity")
        return 2

    # Check if quality gate is too lenient (100% pass rate)
    if stats["pass_rate"] == 100 and stats["total"] >= 10:
        print("\n⚠️  WARNING: Quality gate passing ALL responses")
        print(f"\n   {stats['total']} evaluations, {stats['passed']} passed")
        print("\n   This may indicate:")
        print("     • Quality threshold too lenient")
        print("     • Critique patterns not detecting issues")
        print("     • Responses actually perfect (possible but unlikely)")
        print("\n   Current threshold: <1 issue (fail on ANY issue)")
        print("   To make more lenient, change to: <2 or <3 issues")
        return 1

    # Healthy range
    if stats["total"] >= 5:
        print("\n✅ Quality gate operating normally")
        print(f"\n   {stats['total']} evaluations, {stats['pass_rate']}% pass rate")
        print(f"   Average response length: {stats['avg_response_length']} chars")
        return 0

    # Not enough data
    print("\nℹ️  Insufficient data for health assessment")
    print(f"\n   Only {stats['total']} evaluations in time period")
    print("   Need at least 5 for reliable health check")
    return 1


def show_recent(logs: List[Dict], limit: int = 20) -> None:
    """Show recent log entries.

    Args:
        logs: List of log entries
        limit: Number of entries to show
    """
    if not logs:
        print("\nNo recent activity")
        return

    print(f"\nRecent {min(limit, len(logs))} quality gate evaluations:\n")

    for log in logs[-limit:]:
        timestamp = datetime.fromtimestamp(log.get("timestamp", 0))
        result = log.get("result", "unknown")
        length = log.get("response_length", 0)
        status = "✓" if result == "passed" else "⚠"

        print(f"{status} {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {result:12} | {length:4} chars")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Self-Reflection Quality Gate Monitor"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show quality gate statistics"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check quality gate health"
    )
    parser.add_argument(
        "--recent",
        type=int,
        metavar="N",
        help="Show N recent entries"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        metavar="H",
        help="Hours to look back (default: 24)"
    )

    args = parser.parse_args()

    # Load logs
    logs = load_logs(hours=args.hours)

    # Default action: show stats
    if not (args.stats or args.health or args.recent):
        args.stats = True

    # Execute requested action
    if args.health:
        exit_code = check_health(logs)
        sys.exit(exit_code)
    elif args.recent:
        show_recent(logs, limit=args.recent)
    else:
        show_statistics(logs)


if __name__ == "__main__":
    main()
