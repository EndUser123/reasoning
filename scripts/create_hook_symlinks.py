#!/usr/bin/env python3
"""Create symlinks from P:/.claude/hooks/ to package reasoning hooks.

This script integrates the reasoning package hooks into Claude Code's hook system
by creating symbolic links (or copies as fallback on Windows) from the project hooks directory
to the package hooks.

Usage:
    python scripts/create_hook_symlinks.py [--dry-run] [--force]

Options:
    --dry-run    Show what would be done without making changes
    --force      Overwrite existing hooks/symlinks

Platform support:
    - Unix: Creates symbolic links
    - Windows: Creates file symlinks when available, or copies as fallback
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
PACKAGE_HOOKS_DIR = SCRIPT_DIR / "hooks"
CLAUDE_HOOKS_DIR = Path("P:/.claude/hooks")


# Hook mappings: target name -> (source file, target subdirectory)
HOOK_MAPPINGS = {
    # Start hooks
    "Start_reasoning_mode_selector.py": (
        PACKAGE_HOOKS_DIR / "Start_reasoning_mode_selector.py",
        "",  # Root level
    ),
    # PreTool hooks
    "PreTool_multi_agent_reasoning.py": (
        PACKAGE_HOOKS_DIR / "PreTool_multi_agent_reasoning.py",
        "",  # Root level
    ),
    # Stop hooks
    "Stop_reasoning_enhanced.py": (
        PACKAGE_HOOKS_DIR / "Stop_reasoning_enhanced.py",
        "",  # Root level
    ),
}


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


def create_symlink_windows(
    source: Path, target: Path, force: bool = False, dry_run: bool = False
) -> bool:
    """Create a file symlink on Windows.

    Args:
        source: Path to the source file (in package)
        target: Path where symlink should be created
        force: Overwrite existing target
        dry_run: Show what would be done without making changes

    Returns:
        True if successful, False otherwise
    """
    import subprocess

    if target.exists() and not force:
        print(f"  ⚠️  Target exists: {target} (use --force to overwrite)")
        return False

    if dry_run:
        print(f"  [DRY-RUN] Would create file symlink: {target} -> {source}")
        return True

    try:
        # Remove existing target if force is enabled
        if target.exists():
            if target.is_dir():
                target.rmdir()
            else:
                target.unlink()

        abs_source = source.resolve()
        abs_target = target

        # Ensure parent directory exists
        abs_target.parent.mkdir(parents=True, exist_ok=True)

        # Create file symlink
        subprocess.run(
            [
                "cmd",
                "/c",
                "mklink",
                str(abs_target),
                str(abs_source),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"  ✅ Created file symlink: {target}")
        return True

    except subprocess.CalledProcessError as e:
        # mklink failed, likely due to permissions or developer mode being disabled
        stderr = e.stderr.strip() if e.stderr else str(e)
        print(f"  ⚠️  Symlink creation failed: {stderr}")
        print("  📋 Falling back to copy...")
        return create_copy_fallback(source, target, force, dry_run)

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def create_symlink_unix(
    source: Path, target: Path, force: bool = False, dry_run: bool = False
) -> bool:
    """Create a symbolic link on Unix.

    Args:
        source: Path to the source file (in package)
        target: Path where symlink should be created
        force: Overwrite existing target
        dry_run: Show what would be done without making changes

    Returns:
        True if successful, False otherwise
    """
    if target.exists() and not force:
        print(f"  ⚠️  Target exists: {target} (use --force to overwrite)")
        return False

    if dry_run:
        print(f"  [DRY-RUN] Would create symlink: {target} -> {source}")
        return True

    try:
        # Remove existing target if force is enabled
        if target.exists():
            if target.is_dir():
                target.rmdir()
            else:
                target.unlink()

        # Ensure parent directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Create symlink
        target.symlink_to(source)
        print(f"  ✅ Created symlink: {target}")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def create_copy_fallback(
    source: Path, target: Path, force: bool = False, dry_run: bool = False
) -> bool:
    """Copy file as fallback when symlinks can't be created.

    Args:
        source: Path to the source file (in package)
        target: Path where copy should be created
        force: Overwrite existing target
        dry_run: Show what would be done without making changes

    Returns:
        True if successful, False otherwise
    """
    if target.exists() and not force:
        print(f"  ⚠️  Target exists: {target} (use --force to overwrite)")
        return False

    if dry_run:
        print(f"  [DRY-RUN] Would copy: {source} -> {target}")
        return True

    try:
        # Remove existing target if force is enabled
        if target.exists():
            target.unlink()

        # Ensure parent directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source, target)
        print(f"  ✅ Copied (fallback): {target}")
        print("  ⚠️  Note: Changes to source won't reflect in copy")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def create_hook_link(
    hook_name: str,
    source: Path,
    target_subdir: str,
    force: bool = False,
    dry_run: bool = False,
) -> bool:
    """Create a single hook link.

    Args:
        hook_name: Name of the hook file
        source: Source file path in package
        target_subdir: Subdirectory in .claude/hooks/ (empty for root)
        force: Overwrite existing target
        dry_run: Show what would be done without making changes

    Returns:
        True if successful, False otherwise
    """
    # Verify source exists
    if not source.exists():
        print(f"  ❌ Source not found: {source}")
        return False

    # Build target path
    if target_subdir:
        target_path = CLAUDE_HOOKS_DIR / target_subdir / hook_name
    else:
        target_path = CLAUDE_HOOKS_DIR / hook_name

    print(f"\n🔗 Linking: {hook_name}")
    print(f"   Source: {source}")
    print(f"   Target: {target_path}")

    # Choose platform-specific method
    if is_windows():
        return create_symlink_windows(source, target_path, force, dry_run)
    else:
        return create_symlink_unix(source, target_path, force, dry_run)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create symlinks from P:/.claude/hooks/ to package reasoning hooks"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing hooks/symlinks"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Reasoning Hook Integration Script")
    print("=" * 60)
    print(f"Platform: {sys.platform}")
    print(f"Package hooks: {PACKAGE_HOOKS_DIR}")
    print(f"Claude hooks: {CLAUDE_HOOKS_DIR}")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")

    # Check if package hooks directory exists
    if not PACKAGE_HOOKS_DIR.exists():
        print(f"\n❌ Error: Package hooks directory not found: {PACKAGE_HOOKS_DIR}")
        return 1

    # Create each hook link
    success_count = 0
    failure_count = 0

    for hook_name, (source_path, target_subdir) in HOOK_MAPPINGS.items():
        if create_hook_link(hook_name, source_path, target_subdir, args.force, args.dry_run):
            success_count += 1
        else:
            failure_count += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"Summary: {success_count} succeeded, {failure_count} failed")

    if failure_count > 0 and not args.dry_run:
        print("\n⚠️  Some hooks failed to integrate.")
        print("   Troubleshooting:")
        if is_windows():
            print("   - Run as Administrator for symlink creation")
            print("   - Or enable Developer Mode in Windows Settings")
        else:
            print("   - Check permissions for P:/.claude/hooks/")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
