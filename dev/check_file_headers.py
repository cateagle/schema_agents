# FILE: dev/check_file_headers.py
"""
Check that all Python files have proper file path header comments.
OPTIMIZED: Uses git to find files, respecting .gitignore automatically.
"""
import sys
from pathlib import Path

# Get project root (parent of dev directory)
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os
import subprocess
from typing import List, Tuple


def get_project_root() -> Path:
    """Get project root by moving up one directory from this script."""
    return Path(__file__).parent.parent.absolute()


def find_python_files_fast(project_root: Path) -> List[Path]:
    """
    Find all Python files using git ls-files (respects .gitignore automatically).
    This is 10-100x faster than globbing and manual exclusion checking.
    """
    try:
        # Use git to find tracked Python files - automatically respects .gitignore
        result = subprocess.run(
            ["git", "ls-files", "*.py"], cwd=project_root, capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            python_files = []
            for line in result.stdout.strip().split("\n"):
                if line:  # Skip empty lines
                    file_path = project_root / line
                    if file_path.exists():
                        python_files.append(file_path)
            return sorted(python_files)
        else:
            # Fallback to manual method if git fails
            return find_python_files_manual_fast(project_root)

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Git not available or timeout - fallback to manual method
        return find_python_files_manual_fast(project_root)


def find_python_files_manual_fast(project_root: Path) -> List[Path]:
    """
    Fallback method that avoids traversing excluded directories.
    Much faster than the original implementation.
    """
    # Common directories to skip entirely (don't even traverse them)
    skip_dirs = {
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".git",
        ".mypy_cache",
        "node_modules",
        "build",
        "dist",
        ".eggs",
        "eggs",
        "wheels",
        ".tox",
        ".nox",
    }

    python_files = []

    def should_skip_dir(dir_path: Path) -> bool:
        """Check if we should skip this directory entirely."""
        return dir_path.name in skip_dirs or dir_path.name.startswith(".")

    # Walk the directory tree manually, skipping excluded directories
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)

        # Remove excluded directories from dirs list to prevent traversing them
        dirs[:] = [d for d in dirs if not should_skip_dir(root_path / d)]

        # Check Python files in current directory
        for file in files:
            if file.endswith(".py"):
                python_files.append(root_path / file)

    return sorted(python_files)


def check_file_header(file_path: Path, project_root: Path) -> Tuple[bool, str]:
    """
    Check if a Python file has the correct header comment.
    Returns (has_correct_header, error_message).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError) as e:
        return False, f"Could not read file: {e}"

    if not lines:
        return False, "File is empty"

    # Get relative path for expected comment
    relative_path = file_path.relative_to(project_root)
    expected_comment = f"# FILE: {relative_path}\n"

    # Check for shebang on first line
    has_shebang = lines[0].startswith("#!")

    if has_shebang:
        # Comment should be on second line
        if len(lines) < 2:
            return False, "File has shebang but no second line for header comment"

        if lines[1] != expected_comment:
            actual = lines[1].strip() if len(lines) > 1 else "(missing)"
            return False, f"Expected '{expected_comment.strip()}' on line 2, got '{actual}'"
    else:
        # Comment should be on first line
        if lines[0] != expected_comment:
            actual = lines[0].strip()
            return False, f"Expected '{expected_comment.strip()}' on line 1, got '{actual}'"

    return True, ""


def main() -> int:
    """Main function to check all Python files for proper headers."""
    project_root = get_project_root()

    print(f"Scanning for Python files in {project_root}...")
    python_files = find_python_files_fast(project_root)
    print(f"Found {len(python_files)} Python files to check")

    errors = []

    for py_file in python_files:
        has_header, error_msg = check_file_header(py_file, project_root)
        if not has_header:
            relative_path = py_file.relative_to(project_root)
            errors.append(f"{relative_path}: {error_msg}")

    if errors:
        print("Files with missing or incorrect header comments:")
        for error in errors:
            print(f"  ❌ {error}")
        print(f"\n{len(errors)} files need header comments.")
        print("Run 'python dev/update_file_headers.py' to fix automatically.")
        return 1
    else:
        print("✅ All Python files have correct header comments.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
