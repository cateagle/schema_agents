#!/usr/bin/env python3
# FILE: dev/clear_cache.py
"""Clear all cache files and directories to prevent cache inconsistencies.

This script removes various cache directories and files that can cause issues
during development and testing, including:
- Python __pycache__ directories
- pytest cache directories
- mypy cache directories
- coverage cache files
- egg-info directories
- build directories
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Set, Optional
import argparse


class CacheCleaner:
    """Utility class for clearing various cache files and directories."""

    def __init__(self, verbose: bool = True, dry_run: bool = False):
        self.verbose = verbose
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent.absolute()
        self.cleared_count = 0
        self.failed_count = 0

    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def clear_directory(self, path: Path, description: Optional[str] = None) -> bool:
        """Clear a directory and return success status.

        Args:
            path: Path to directory to clear
            description: Optional description for logging

        Returns:
            bool: True if successful, False if failed
        """
        if not path.exists():
            return True

        desc = description or f"directory {path}"

        if self.dry_run:
            self.log(f"   [DRY RUN] Would remove {desc}")
            return True

        try:
            shutil.rmtree(path)
            self.log(f"   ✅ Cleared {desc}")
            self.cleared_count += 1
            return True
        except Exception as e:
            self.log(f"   ❌ Failed to clear {desc}: {e}")
            self.failed_count += 1
            return False

    def clear_file(self, path: Path, description: Optional[str] = None) -> bool:
        """Clear a file and return success status.

        Args:
            path: Path to file to clear
            description: Optional description for logging

        Returns:
            bool: True if successful, False if failed
        """
        if not path.exists():
            return True

        desc = description or f"file {path}"

        if self.dry_run:
            self.log(f"   [DRY RUN] Would remove {desc}")
            return True

        try:
            path.unlink()
            self.log(f"   ✅ Cleared {desc}")
            self.cleared_count += 1
            return True
        except Exception as e:
            self.log(f"   ❌ Failed to clear {desc}: {e}")
            self.failed_count += 1
            return False

    def find_cache_directories(self) -> List[Path]:
        """Find all cache directories in the project.

        Returns:
            List of Path objects for cache directories
        """
        cache_patterns = {
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".coverage",
            "htmlcov",
            "build",
            "dist",
            "*.egg-info",
        }

        cache_dirs = []

        # Walk through project directory
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)

            # Skip virtual environment directory
            if ".venv" in str(root_path) or "venv" in str(root_path):
                continue

            # Check directories
            for dir_name in dirs:
                if dir_name in cache_patterns or dir_name.endswith(".egg-info"):
                    cache_dirs.append(root_path / dir_name)

            # Check files
            for file_name in files:
                if file_name in {".coverage", ".coverage.*"} or file_name.startswith(".coverage."):
                    cache_dirs.append(root_path / file_name)

        return cache_dirs

    def clear_python_caches(self) -> bool:
        """Clear Python __pycache__ directories.

        Returns:
            bool: True if all clears successful, False if any failed
        """
        self.log("🔄 Clearing Python __pycache__ directories...")

        success = True
        pycache_dirs = []

        for root, dirs, files in os.walk(self.project_root):
            if ".venv" in str(root) or "venv" in str(root):
                continue

            for dir_name in dirs:
                if dir_name == "__pycache__":
                    pycache_dirs.append(Path(root) / dir_name)

        if not pycache_dirs:
            self.log("   ℹ️  No __pycache__ directories found")
            return True

        for cache_dir in pycache_dirs:
            if not self.clear_directory(
                cache_dir, f"__pycache__ at {cache_dir.relative_to(self.project_root)}"
            ):
                success = False

        return success

    def clear_pytest_caches(self) -> bool:
        """Clear pytest cache directories.

        Returns:
            bool: True if all clears successful, False if any failed
        """
        self.log("🔄 Clearing pytest cache directories...")

        success = True
        pytest_dirs = []

        for root, dirs, files in os.walk(self.project_root):
            if ".venv" in str(root) or "venv" in str(root):
                continue

            for dir_name in dirs:
                if dir_name == ".pytest_cache":
                    pytest_dirs.append(Path(root) / dir_name)

        if not pytest_dirs:
            self.log("   ℹ️  No .pytest_cache directories found")
            return True

        for cache_dir in pytest_dirs:
            if not self.clear_directory(
                cache_dir, f"pytest cache at {cache_dir.relative_to(self.project_root)}"
            ):
                success = False

        return success

    def clear_mypy_caches(self) -> bool:
        """Clear mypy cache directories.

        Returns:
            bool: True if all clears successful, False if any failed
        """
        self.log("🔄 Clearing mypy cache directories...")

        success = True
        mypy_dirs = []

        for root, dirs, files in os.walk(self.project_root):
            if ".venv" in str(root) or "venv" in str(root):
                continue

            for dir_name in dirs:
                if dir_name == ".mypy_cache":
                    mypy_dirs.append(Path(root) / dir_name)

        if not mypy_dirs:
            self.log("   ℹ️  No .mypy_cache directories found")
            return True

        for cache_dir in mypy_dirs:
            if not self.clear_directory(
                cache_dir, f"mypy cache at {cache_dir.relative_to(self.project_root)}"
            ):
                success = False

        return success

    def clear_coverage_files(self) -> bool:
        """Clear coverage cache files.

        Returns:
            bool: True if all clears successful, False if any failed
        """
        self.log("🔄 Clearing coverage cache files...")

        success = True
        coverage_items = []

        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)

            if ".venv" in str(root) or "venv" in str(root):
                continue

            # Coverage files
            for file_name in files:
                if file_name == ".coverage" or file_name.startswith(".coverage."):
                    coverage_items.append(root_path / file_name)

            # Coverage HTML directories
            for dir_name in dirs:
                if dir_name == "htmlcov":
                    coverage_items.append(root_path / dir_name)

        if not coverage_items:
            self.log("   ℹ️  No coverage files found")
            return True

        for item in coverage_items:
            if item.is_file():
                if not self.clear_file(
                    item, f"coverage file at {item.relative_to(self.project_root)}"
                ):
                    success = False
            else:
                if not self.clear_directory(
                    item, f"coverage directory at {item.relative_to(self.project_root)}"
                ):
                    success = False

        return success

    def clear_build_artifacts(self) -> bool:
        """Clear build artifacts and egg-info directories.

        Returns:
            bool: True if all clears successful, False if any failed
        """
        self.log("🔄 Clearing build artifacts...")

        success = True
        build_dirs = []

        for root, dirs, files in os.walk(self.project_root):
            if ".venv" in str(root) or "venv" in str(root):
                continue

            for dir_name in dirs:
                if dir_name in {"build", "dist"} or dir_name.endswith(".egg-info"):
                    build_dirs.append(Path(root) / dir_name)

        if not build_dirs:
            self.log("   ℹ️  No build artifacts found")
            return True

        for build_dir in build_dirs:
            if not self.clear_directory(
                build_dir, f"build artifact at {build_dir.relative_to(self.project_root)}"
            ):
                success = False

        return success

    def clear_all_caches(self) -> bool:
        """Clear all types of cache files and directories.

        Returns:
            bool: True if all operations successful, False if any failed
        """
        if self.verbose:
            action = "Would clear" if self.dry_run else "Clearing"
            print(f"🧹 {action} all cache files and directories...")
            print()

        tasks = [
            self.clear_python_caches,
            self.clear_pytest_caches,
            self.clear_mypy_caches,
            self.clear_coverage_files,
            self.clear_build_artifacts,
        ]

        all_success = True

        for task in tasks:
            if not task():
                all_success = False
            if self.verbose:
                print()

        # Summary
        if self.verbose:
            if self.dry_run:
                print("🔍 Dry run completed - no files were actually removed")
            elif all_success:
                print(f"✅ Cache clearing completed successfully!")
                if self.cleared_count > 0:
                    print(f"   Cleared {self.cleared_count} cache items")
                else:
                    print("   No cache items found to clear")
            else:
                print(f"⚠️  Cache clearing completed with {self.failed_count} failures")
                print(f"   Successfully cleared {self.cleared_count} items")

        return all_success


def main() -> int:
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(
        description="Clear all cache files and directories",
        epilog="""
This script clears the following cache types:
• Python __pycache__ directories
• pytest .pytest_cache directories  
• mypy .mypy_cache directories
• coverage .coverage files and htmlcov directories
• build artifacts (build/, dist/, *.egg-info)

This helps prevent cache inconsistencies during development and testing.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Minimal output - only show errors"
    )

    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be cleared without actually removing files",
    )

    parser.add_argument(
        "--type",
        "-t",
        choices=["python", "pytest", "mypy", "coverage", "build", "all"],
        default="all",
        help="Clear only specific cache type (default: all)",
    )

    args = parser.parse_args()

    cleaner = CacheCleaner(verbose=not args.quiet, dry_run=args.dry_run)

    # Map cache types to methods
    type_map = {
        "python": cleaner.clear_python_caches,
        "pytest": cleaner.clear_pytest_caches,
        "mypy": cleaner.clear_mypy_caches,
        "coverage": cleaner.clear_coverage_files,
        "build": cleaner.clear_build_artifacts,
        "all": cleaner.clear_all_caches,
    }

    # Run selected cache clearing
    success = type_map[args.type]()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
