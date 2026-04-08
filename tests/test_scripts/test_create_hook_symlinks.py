#!/usr/bin/env python3
"""Tests for hook symlink creation script."""

import sys
from pathlib import Path

import pytest

# Add reasoning package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.create_hook_symlinks import (
    HOOK_MAPPINGS,
    create_copy_fallback,
    create_hook_link,
    is_windows,
)


class TestSymlinkScript:
    """Test symlink script functionality."""

    def test_hook_mappings_defined(self):
        """Hook mappings should be defined."""
        assert len(HOOK_MAPPINGS) == 3
        assert "Start_reasoning_mode_selector.py" in HOOK_MAPPINGS
        assert "PreTool_multi_agent_reasoning.py" in HOOK_MAPPINGS
        assert "Stop_reasoning_enhanced.py" in HOOK_MAPPINGS

    def test_is_windows_detects_platform(self):
        """Should detect Windows platform correctly."""
        result = is_windows()
        assert isinstance(result, bool)
        # We're on Windows in this environment
        assert result is True

    def test_copy_fallback_dry_run(self, tmp_path):
        """Dry-run mode should not create files."""
        source = tmp_path / "source.txt"
        source.write_text("test content")

        target = tmp_path / "target.txt"

        # Dry-run should not create file
        result = create_copy_fallback(source, target, force=False, dry_run=True)
        assert result is True
        assert not target.exists()

    def test_copy_fallback_creates_file(self, tmp_path):
        """Copy fallback should create file."""
        source = tmp_path / "source.txt"
        source.write_text("test content")

        target = tmp_path / "target.txt"

        # Should create file
        result = create_copy_fallback(source, target, force=False, dry_run=False)
        assert result is True
        assert target.exists()
        assert target.read_text() == "test content"

    def test_copy_fallback_respects_existing(self, tmp_path):
        """Copy fallback should respect existing files without force."""
        source = tmp_path / "source.txt"
        source.write_text("new content")

        target = tmp_path / "target.txt"
        target.write_text("existing content")

        # Should fail without force
        result = create_copy_fallback(source, target, force=False, dry_run=False)
        assert result is False
        assert target.read_text() == "existing content"

    def test_copy_fallback_overwrites_with_force(self, tmp_path):
        """Copy fallback should overwrite with force flag."""
        source = tmp_path / "source.txt"
        source.write_text("new content")

        target = tmp_path / "target.txt"
        target.write_text("existing content")

        # Should overwrite with force
        result = create_copy_fallback(source, target, force=True, dry_run=False)
        assert result is True
        assert target.read_text() == "new content"

    def test_hook_link_dry_run(self, tmp_path):
        """Hook link dry-run should not create files."""
        # Create a temporary source file
        source = tmp_path / "test_hook.py"
        source.write_text("# test hook")

        # Use a temporary directory for hooks
        import scripts.create_hook_symlinks as symlink_module
        original_claude_dir = symlink_module.CLAUDE_HOOKS_DIR
        symlink_module.CLAUDE_HOOKS_DIR = tmp_path / "hooks"

        try:
            result = create_hook_link(
                "test_hook.py",
                source,
                "",
                force=False,
                dry_run=True
            )
            assert result is True
            # No file should be created in dry-run mode
            assert not (tmp_path / "hooks" / "test_hook.py").exists()
        finally:
            symlink_module.CLAUDE_HOOKS_DIR = original_claude_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
