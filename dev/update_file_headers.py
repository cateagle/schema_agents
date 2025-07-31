# FILE: dev/update_file_headers.py
"""
Update Python files to have proper file path header comments.
OPTIMIZED: Uses fast file discovery from check_file_headers.
"""
import sys
from pathlib import Path

# Get project root (parent of dev directory)
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the fast file discovery from check_file_headers
from dev.check_file_headers import get_project_root, find_python_files_fast, check_file_header


def update_file_header(file_path: Path, project_root: Path) -> bool:
    """
    Update a Python file to have the correct header comment.
    Returns True if file was modified.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"Could not read {file_path}: {e}")
        return False

    if not lines:
        # Empty file - add just the header comment
        relative_path = file_path.relative_to(project_root)
        header_comment = f"# FILE: {relative_path}\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(header_comment)
        return True

    # Get relative path for expected comment
    relative_path = file_path.relative_to(project_root)
    expected_comment = f"# FILE: {relative_path}\n"

    # Check for shebang on first line
    has_shebang = lines[0].startswith("#!")

    if has_shebang:
        # Comment should be on second line (index 1)
        if len(lines) < 2:
            # Insert header comment as second line
            lines.insert(1, expected_comment)
        elif lines[1] == expected_comment:
            # Already correct
            return False
        elif lines[1].startswith("# FILE:") or (
            lines[1].startswith("#") and "/" in lines[1] and lines[1].endswith(".py\n")
        ):
            # Line 1 is an incorrect header comment - replace it
            lines[1] = expected_comment
        else:
            # Line 1 is not a header comment - insert header before it
            lines.insert(1, expected_comment)
    else:
        # Comment should be on first line
        if lines[0] != expected_comment:
            # Check if first line is already a file path comment (wrong path or format)
            if lines[0].startswith("# FILE:") or (
                lines[0].startswith("#") and "/" in lines[0] and lines[0].endswith(".py\n")
            ):
                # Replace the incorrect header
                lines[0] = expected_comment
            else:
                # Insert header comment as first line
                lines.insert(0, expected_comment)
        else:
            # Already correct
            return False

    # Write the updated file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except PermissionError as e:
        print(f"Could not write {file_path}: {e}")
        return False


def main() -> int:
    """Main function to update all Python files with proper headers."""
    project_root = get_project_root()

    print(f"Scanning for Python files in {project_root}...")
    python_files = find_python_files_fast(project_root)
    print(f"Found {len(python_files)} Python files to check")

    updated_files = []

    for py_file in python_files:
        has_header, _ = check_file_header(py_file, project_root)
        if not has_header:
            if update_file_header(py_file, project_root):
                relative_path = py_file.relative_to(project_root)
                updated_files.append(relative_path)

    if updated_files:
        print("Updated files:")
        for file_path in updated_files:
            print(f"  ✅ {file_path}")
        print(f"\n{len(updated_files)} files updated with header comments.")
    else:
        print("✅ All Python files already have correct header comments.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
