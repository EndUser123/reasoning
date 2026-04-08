#!/usr/bin/env python3
"""Tests for observability module - metrics logging and fail-safe behavior."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "hooks"))

from UserPromptSubmit_modules.observability import (
    get_metrics_summary,
    log_cognitive_selection,
    log_reasoning_mode,
)

# Test metrics file path (isolated from production data)
TEST_METRICS_FILE = Path(__file__).resolve().parent / ".test_data" / "test_metrics.jsonl"


@pytest.fixture(autouse=True)
def isolate_test_metrics(tmp_path, monkeypatch):
    """Isolate test metrics from production data."""
    # Override METRICS_FILE to use temp directory
    test_file = tmp_path / "test_metrics.jsonl"

    # Patch the module-level METRICS_FILE constant
    import UserPromptSubmit_modules.observability as obs_module

    monkeypatch.setattr(obs_module, "METRICS_FILE", test_file)
    monkeypatch.setattr(obs_module, "METRICS_DIR", tmp_path)

    yield test_file

    # Cleanup handled by tmp_path fixture


class TestCognitiveSelectionLogging:
    """Test cognitive framework selection logging."""

    def test_log_cognitive_selection_creates_file(self, isolate_test_metrics):
        """Test that logging creates the metrics file and directory."""
        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

        enhancers = [
            Enhancer(
                name="assumption_surfacing",
                injection="Test injection",
                topics=["implementation"],
            )
        ]
        intent = {"implementation": True}
        tokens = 100
        rationale = "Test rationale"

        log_cognitive_selection(enhancers, intent, tokens, rationale)

        assert isolate_test_metrics.exists()
        assert isolate_test_metrics.stat().st_size > 0

    def test_log_cognitive_selection_format(self, isolate_test_metrics):
        """Test that logged events have correct JSON structure."""
        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

        enhancers = [
            Enhancer(
                name="outcome_anchoring",
                injection="Test injection",
                topics=["implementation"],
            )
        ]
        intent = {"implementation": True, "diagnostic": False}
        tokens = 150
        rationale = "implementation intent detected"

        log_cognitive_selection(enhancers, intent, tokens, rationale)

        # Read and parse the logged line
        with open(isolate_test_metrics, encoding="utf-8") as f:
            line = f.readline().strip()
            event = json.loads(line)

        # Verify structure
        assert "timestamp" in event
        assert event["enhancers"] == ["outcome_anchoring"]
        assert event["enhancer_count"] == 1
        assert event["intent"] == intent
        assert event["tokens"] == tokens
        assert event["rationale"] == rationale

    def test_log_cognitive_selection_appends(self, isolate_test_metrics):
        """Test that multiple events are appended (not overwritten)."""
        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

        # Log first event
        enhancers1 = [
            Enhancer(name="assumption_surfacing", injection="Test", topics=["implementation"])
        ]
        log_cognitive_selection(enhancers1, {"implementation": True}, 100, "rationale 1")

        # Log second event
        enhancers2 = [
            Enhancer(name="outcome_anchoring", injection="Test", topics=["implementation"])
        ]
        log_cognitive_selection(enhancers2, {"implementation": True}, 150, "rationale 2")

        # Verify both events exist
        with open(isolate_test_metrics, encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 2

        event1 = json.loads(lines[0].strip())
        event2 = json.loads(lines[1].strip())

        assert event1["rationale"] == "rationale 1"
        assert event2["rationale"] == "rationale 2"

    def test_log_cognitive_selection_multiple_enhancers(self, isolate_test_metrics):
        """Test logging multiple cognitive enhancers."""
        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

        enhancers = [
            Enhancer(
                name="assumption_surfacing",
                injection="Test 1",
                topics=["implementation"],
            ),
            Enhancer(
                name="outcome_anchoring",
                injection="Test 2",
                topics=["implementation"],
            ),
            Enhancer(
                name="inversion_prompting",
                injection="Test 3",
                topics=["implementation"],
            ),
        ]
        intent = {"implementation": True}
        tokens = 300
        rationale = "implementation intent detected"

        log_cognitive_selection(enhancers, intent, tokens, rationale)

        with open(isolate_test_metrics, encoding="utf-8") as f:
            event = json.loads(f.readline().strip())

        assert event["enhancer_count"] == 3
        assert set(event["enhancers"]) == {
            "assumption_surfacing",
            "outcome_anchoring",
            "inversion_prompting",
        }


class TestReasoningModeLogging:
    """Test reasoning mode selection logging."""

    def test_log_reasoning_mode_creates_file(self, isolate_test_metrics):
        """Test that logging creates the metrics file."""
        log_reasoning_mode(
            mode="sequential",
            confidence=3,
            fallback=False,
            tokens=200,
        )

        assert isolate_test_metrics.exists()
        assert isolate_test_metrics.stat().st_size > 0

    def test_log_reasoning_mode_format(self, isolate_test_metrics):
        """Test that logged events have correct JSON structure."""
        log_reasoning_mode(
            mode="devils_advocate",
            confidence=4,
            fallback=False,
            tokens=250,
        )

        # Read and parse the logged line
        with open(isolate_test_metrics, encoding="utf-8") as f:
            line = f.readline().strip()
            event = json.loads(line)

        # Verify structure
        assert "timestamp" in event
        assert event["mode"] == "devils_advocate"
        assert event["confidence"] == 4
        assert event["fallback"] is False
        assert event["tokens"] == 250

    def test_log_reasoning_mode_fallback(self, isolate_test_metrics):
        """Test logging fallback selections."""
        log_reasoning_mode(
            mode="sequential",
            confidence=1,
            fallback=True,
            tokens=200,
        )

        with open(isolate_test_metrics, encoding="utf-8") as f:
            event = json.loads(f.readline().strip())

        assert event["fallback"] is True
        assert event["confidence"] == 1


class TestFailsafeBehavior:
    """Test fail-safe error handling."""

    def test_log_cognitive_selection_handles_permission_error(
        self, isolate_test_metrics, capsys
    ):
        """Test that permission errors are caught and reported, not raised."""
        import platform

        # Skip on Windows - chmod doesn't work the same way
        if platform.system() == "Windows":
            pytest.skip("chmod read-only test not reliable on Windows")

        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

        # Make the directory read-only to simulate permission error
        isolate_test_metrics.parent.chmod(0o444)

        enhancers = [
            Enhancer(
                name="assumption_surfacing",
                injection="Test",
                topics=["implementation"],
            )
        ]

        # Should not raise exception
        log_cognitive_selection(enhancers, {"implementation": True}, 100, "test")

        # Restore permissions for cleanup
        isolate_test_metrics.parent.chmod(0o755)

        # Check that error was printed to stdout
        captured = capsys.readouterr()
        assert "[OBSERVABILITY]" in captured.out
        assert "Failed to log cognitive selection" in captured.out

    def test_log_reasoning_mode_handles_invalid_path(self, capsys, monkeypatch):
        """Test that invalid paths are handled gracefully."""

        # Patch METRICS_FILE with an invalid path
        invalid_path = Path("/nonexistent/path/that/cannot/be/created/metrics.jsonl")

        # Simulate a scenario where directory creation fails
        with patch.object(Path, "mkdir", side_effect=PermissionError("Access denied")):
            # Should not raise exception
            log_reasoning_mode(
                mode="sequential",
                confidence=2,
                fallback=False,
                tokens=200,
            )

        # Check that error was printed
        captured = capsys.readouterr()
        assert "[OBSERVABILITY]" in captured.out
        assert "Failed to log reasoning mode" in captured.out

    def test_failsafe_does_not_break_hook_execution(self):
        """Test that logging failures never prevent hook from completing."""
        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

        # This test verifies that even if observability fails,
        # the cognitive_enhancers hook still works

        enhancers = [
            Enhancer(
                name="assumption_surfacing",
                injection="Test",
                topics=["implementation"],
            )
        ]

        # Call logging - even if it fails internally, it should not raise
        try:
            log_cognitive_selection(enhancers, {"implementation": True}, 100, "test")
        except Exception as e:
            pytest.fail(f"log_cognitive_selection raised exception: {e}")

        # If we reach here, fail-safe worked


class TestMetricsSummary:
    """Test metrics summary generation."""

    def test_get_metrics_summary_empty_file(self, isolate_test_metrics):
        """Test summary when file exists but is empty."""
        # Create empty metrics file to distinguish from "doesn't exist"
        isolate_test_metrics.parent.mkdir(parents=True, exist_ok=True)
        isolate_test_metrics.write_text("", encoding="utf-8")

        summary = get_metrics_summary()

        # Empty file should return 0 events, not error
        assert "error" not in summary
        assert summary["total_events"] == 0
        assert summary["cognitive_events"] == 0
        assert summary["reasoning_events"] == 0

    def test_get_metrics_summary_cognitive_events(self, isolate_test_metrics):
        """Test summary with cognitive events."""
        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

        # Log some cognitive events
        enhancers1 = [
            Enhancer(
                name="assumption_surfacing",
                injection="Test",
                topics=["implementation"],
            )
        ]
        log_cognitive_selection(enhancers1, {"implementation": True}, 100, "test 1")

        enhancers2 = [
            Enhancer(
                name="calibrated_confidence",
                injection="Test",
                topics=["diagnostic"],
            )
        ]
        log_cognitive_selection(enhancers2, {"diagnostic": True}, 150, "test 2")

        summary = get_metrics_summary()

        assert summary["total_events"] == 2
        assert summary["cognitive_events"] == 2
        assert summary["reasoning_events"] == 0

        # Check cognitive statistics
        assert "cognitive" in summary
        cogn_stats = summary["cognitive"]
        assert cogn_stats["total_tokens"] == 250
        assert cogn_stats["avg_tokens"] == 125

        # Check most common enhancers
        most_common = cogn_stats["most_common_enhancers"]
        assert len(most_common) == 2
        enhancer_names = [name for name, _ in most_common]
        assert "assumption_surfacing" in enhancer_names
        assert "calibrated_confidence" in enhancer_names

    def test_get_metrics_summary_reasoning_events(self, isolate_test_metrics):
        """Test summary with reasoning events."""
        # Log some reasoning events
        log_reasoning_mode("sequential", confidence=3, fallback=False, tokens=200)
        log_reasoning_mode("devils_advocate", confidence=4, fallback=False, tokens=250)
        log_reasoning_mode("sequential", confidence=1, fallback=True, tokens=200)

        summary = get_metrics_summary()

        assert summary["total_events"] == 3
        assert summary["cognitive_events"] == 0
        assert summary["reasoning_events"] == 3

        # Check reasoning statistics
        assert "reasoning" in summary
        reason_stats = summary["reasoning"]

        # Mode distribution
        mode_dist = reason_stats["mode_distribution"]
        assert mode_dist["sequential"] == 2
        assert mode_dist["devils_advocate"] == 1

        # Confidence distribution
        conf_dist = reason_stats["confidence_distribution"]
        assert conf_dist["3"] == 1
        assert conf_dist["4"] == 1
        assert conf_dist["1"] == 1

        # Fallback rate (1 out of 3)
        assert reason_stats["fallback_rate"] == 1 / 3

    def test_get_metrics_summary_mixed_events(self, isolate_test_metrics):
        """Test summary with both cognitive and reasoning events."""
        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

        # Log cognitive event
        enhancers = [
            Enhancer(
                name="assumption_surfacing",
                injection="Test",
                topics=["implementation"],
            )
        ]
        log_cognitive_selection(enhancers, {"implementation": True}, 100, "test")

        # Log reasoning event
        log_reasoning_mode("sequential", confidence=3, fallback=False, tokens=200)

        summary = get_metrics_summary()

        assert summary["total_events"] == 2
        assert summary["cognitive_events"] == 1
        assert summary["reasoning_events"] == 1
        assert "cognitive" in summary
        assert "reasoning" in summary

    def test_get_metrics_summary_nonexistent_file(self, monkeypatch, tmp_path):
        """Test summary when metrics file doesn't exist."""
        import UserPromptSubmit_modules.observability as obs_module

        # Point to a non-existent file
        nonexistent = tmp_path / "nonexistent" / "metrics.jsonl"
        monkeypatch.setattr(obs_module, "METRICS_FILE", nonexistent)

        summary = get_metrics_summary()

        assert "error" in summary
        assert "not found" in summary["error"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
