#!/usr/bin/env python3
"""Analyze reasoning profile auto-injection quality for hook-audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REASONING_LOG = HOOKS_DIR / "logs" / "reasoning_profiles.jsonl"
QUALITY_LOG = HOOKS_DIR / "logs" / "behavioral_quality_gate.log"


def _parse_iso(ts: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        return None


def analyze(days: int) -> int:
    cutoff = datetime.now() - timedelta(days=days)

    profile_counts: Counter[str] = Counter()
    trigger_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    injected = 0
    skipped = 0

    if REASONING_LOG.exists():
        with open(REASONING_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue

                dt = _parse_iso(str(entry.get("timestamp", "")))
                if dt is None or dt < cutoff:
                    continue

                profile = str(entry.get("profile", "unknown"))
                trigger = str(entry.get("trigger", "unknown"))
                reason = str(entry.get("reason", "unknown"))
                did_inject = bool(entry.get("injected", False))

                profile_counts[profile] += 1
                trigger_counts[trigger] += 1
                reason_counts[reason] += 1
                if did_inject:
                    injected += 1
                else:
                    skipped += 1

    recommendation_quality_issues = 0
    if QUALITY_LOG.exists():
        with open(QUALITY_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|", 2)
                if len(parts) < 3:
                    continue
                dt = _parse_iso(parts[0])
                if dt is None or dt < cutoff:
                    continue
                finding_type = parts[1].strip()
                if finding_type == "recommendation_quality":
                    recommendation_quality_issues += 1

    total_events = injected + skipped
    inject_rate = (injected / total_events * 100.0) if total_events > 0 else 0.0

    print(f"Reasoning Profile Analysis (last {days} days)")
    print("-" * 60)
    print(f"Events: {total_events}")
    print(f"Injected: {injected}")
    print(f"Skipped: {skipped}")
    print(f"Injection rate: {inject_rate:.1f}%")
    print(f"Recommendation-quality blocks: {recommendation_quality_issues}")

    if profile_counts:
        print("\nBy profile:")
        for profile, count in profile_counts.most_common():
            print(f"  - {profile}: {count}")

    if trigger_counts:
        print("\nBy trigger:")
        for trigger, count in trigger_counts.most_common():
            print(f"  - {trigger}: {count}")

    if reason_counts:
        print("\nTop routing reasons:")
        for reason, count in reason_counts.most_common(8):
            print(f"  - {reason}: {count}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze reasoning profile injections")
    parser.add_argument("--days", type=int, default=7, help="Analysis period in days")
    args = parser.parse_args()
    return analyze(args.days)


if __name__ == "__main__":
    raise SystemExit(main())
