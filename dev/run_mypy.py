# FILE: dev/run_mypy.py
"""
Run mypy type checking with proper configuration and useful output.
Usage: python dev/run_mypy.py [files/folders...]
"""
import sys
from pathlib import Path

# Get project root (parent of dev directory)
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import subprocess
import os
import argparse


def get_project_root() -> Path:
    """Get project root by moving up one directory from this script."""
    return Path(__file__).parent.parent.absolute()


def run_mypy(
    targets=None,
    strict=False,
    quiet=False,
    show_error_codes=True,
    tests_only=False,
    split_mode=False,
):
    """
    Run mypy with appropriate configuration.

    Args:
        targets: List of files/folders to check (default: entire project)
        strict: Use strict checking mode
        quiet: Suppress summary output
        show_error_codes: Show error codes in output
        tests_only: Only check tests directory (uses lenient settings)
        split_mode: Run main code with hard errors, tests with info only
    """
    project_root = get_project_root()

    if split_mode:
        return run_mypy_split_mode(project_root, show_error_codes, quiet)

    # Base mypy command
    cmd = [sys.executable, "-m", "mypy"]

    # Add configuration file if it exists (prefer pyproject.toml, fallback to mypy.ini)
    config_file = None
    pyproject_file = project_root / "pyproject.toml"
    mypy_ini_file = project_root / "mypy.ini"

    if pyproject_file.exists():
        config_file = pyproject_file
        cmd.extend(["--config-file", str(config_file)])
    elif mypy_ini_file.exists():
        config_file = mypy_ini_file
        cmd.extend(["--config-file", str(config_file)])

    # Add command line options
    if strict:
        cmd.extend(["--strict", "--no-error-summary"])  # Avoid duplicate summary in strict mode

    if quiet:
        cmd.append("--no-error-summary")

    if show_error_codes:
        cmd.append("--show-error-codes")

    # Add targets or default to key project files
    if targets:
        cmd.extend(targets)
    elif tests_only:
        # Only check tests
        cmd.append("tests/")
        print("Checking tests directory only (lenient mode configured)")
    else:
        # Default targets - focus on main source files, include tests separately
        default_targets = [
            "models.py",
            "client.py",
            "chromadb_manager.py",
            "usage_example.py",
            "tests/",  # Tests will use lenient settings from config
        ]

        # Only add targets that exist
        for target in default_targets:
            target_path = project_root / target
            if target_path.exists():
                cmd.append(str(target_path))

    # Set working directory
    os.chdir(project_root)

    print(f"Running mypy with command: {' '.join(cmd[2:])}")  # Skip python -m mypy
    print(f"Working directory: {project_root}")
    if config_file:
        print(f"Using configuration: {config_file.name}")
    if not targets and not tests_only:
        print(
            "Note: Tests directory will use lenient checking (configured in [tool.mypy] overrides)"
        )
    print("-" * 60)

    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except FileNotFoundError:
        print("Error: mypy not found. Install it with: pip install mypy")
        return 1
    except Exception as e:
        print(f"Error running mypy: {e}")
        return 1


def run_mypy_split_mode(project_root: Path, show_error_codes: bool, quiet: bool) -> int:
    """
    Run mypy in split mode: strict on main code, informational on tests.

    Returns:
        Exit code from main code check only (tests are informational)
    """
    print("=" * 70)
    print("MYPY SPLIT MODE: Strict on main code, informational on tests")
    print("=" * 70)

    # Get main source files (exclude tests)
    main_targets = []
    potential_main_files = [
        "models.py",
        "client.py",
        "chromadb_manager.py",
        "usage_example.py",
        "dev/",  # Include dev scripts
    ]

    for target in potential_main_files:
        target_path = project_root / target
        if target_path.exists():
            main_targets.append(str(target_path))

    # Build base command
    base_cmd = [sys.executable, "-m", "mypy"]

    # Add configuration file if it exists (prefer pyproject.toml, fallback to mypy.ini)
    config_file = None
    pyproject_file = project_root / "pyproject.toml"
    mypy_ini_file = project_root / "mypy.ini"

    if pyproject_file.exists():
        config_file = pyproject_file
        base_cmd.extend(["--config-file", str(config_file)])
        print(f"Using mypy configuration from: {config_file.name}")
    elif mypy_ini_file.exists():
        config_file = mypy_ini_file
        base_cmd.extend(["--config-file", str(config_file)])
        print(f"Using mypy configuration from: {config_file.name}")
    else:
        print("No mypy configuration file found (pyproject.toml or mypy.ini)")

    if show_error_codes:
        base_cmd.append("--show-error-codes")

    if not quiet:
        base_cmd.append("--no-error-summary")

    main_exit_code = 0

    # === PHASE 1: Check main code with strict error handling ===
    if main_targets:
        print("\n🔍 PHASE 1: Checking main source code (STRICT - will fail on errors)")
        print("-" * 50)
        main_cmd = base_cmd + main_targets
        print(f"Command: {' '.join(main_cmd[2:])}")
        print()

        try:
            main_result = subprocess.run(main_cmd, cwd=project_root)
            main_exit_code = main_result.returncode

            if main_exit_code == 0:
                print("✅ Main code passed mypy checks!")
            else:
                print(f"❌ Main code has mypy errors (exit code: {main_exit_code})")
        except Exception as e:
            print(f"Error checking main code: {e}")
            main_exit_code = 1
    else:
        print("⚠️  No main source files found to check")

    # === PHASE 2: Check tests with informational output ===
    tests_path = project_root / "tests"
    if tests_path.exists():
        print("\n" + "=" * 50)
        print("📊 PHASE 2: Checking tests directory (INFORMATIONAL - won't fail)")
        print("-" * 50)

        tests_cmd = base_cmd + ["tests/"]
        print(f"Command: {' '.join(tests_cmd[2:])}")
        print()

        try:
            tests_result = subprocess.run(tests_cmd, cwd=project_root)

            if tests_result.returncode == 0:
                print("✅ Tests have no mypy issues!")
            else:
                print("ℹ️  Tests have mypy issues (informational only - not failing build)")
                print(
                    "   This is normal for tests with mocks, fixtures, and intentional type violations"
                )
        except Exception as e:
            print(f"Error checking tests (informational): {e}")
    else:
        print("\n📊 PHASE 2: No tests directory found")

    # === SUMMARY ===
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if main_exit_code == 0:
        print("✅ OVERALL RESULT: PASSED")
        print("   Main source code has no mypy errors")
        print("   (Test issues are informational only)")
    else:
        print("❌ OVERALL RESULT: FAILED")
        print(f"   Main source code has mypy errors (exit code: {main_exit_code})")
        print("   Fix main code errors to pass")

    print("\nNote: Only main source code errors affect the exit code.")
    print("      Test directory issues are shown for information only.")

    return main_exit_code


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="""
Run mypy type checking on the project with flexible modes.

Split mode (--split-mode) is especially useful for CI/development:
- Main source code is checked strictly and will fail on type errors
- Tests are checked informationally and won't cause overall failure
- This lets you catch real type issues while still seeing test type info

Configuration is read from pyproject.toml [tool.mypy] section (preferred) 
or mypy.ini as fallback.
        """,
        epilog="""
Examples:
  python dev/run_mypy.py                    # Check default files
  python dev/run_mypy.py models.py          # Check single file
  python dev/run_mypy.py tests/unit/        # Check single directory
  python dev/run_mypy.py --strict client.py # Strict checking on one file
  python dev/run_mypy.py --quiet            # Minimal output
  python dev/run_mypy.py --tests-only       # Only check tests (lenient mode)
  python dev/run_mypy.py --split-mode       # Main code strict, tests informational
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "targets", nargs="*", help="Files or directories to check (default: main project files)"
    )

    parser.add_argument("--strict", action="store_true", help="Use strict type checking mode")

    parser.add_argument("--quiet", action="store_true", help="Suppress summary output")

    parser.add_argument("--no-error-codes", action="store_true", help="Don't show error codes")

    parser.add_argument(
        "--tests-only",
        action="store_true",
        help="Only check tests directory (uses lenient settings)",
    )

    parser.add_argument(
        "--split-mode",
        action="store_true",
        help="Check main code strictly (fails on errors), tests informationally (shows issues but doesn't fail)",
    )

    args = parser.parse_args()

    return run_mypy(
        targets=args.targets,
        strict=args.strict,
        quiet=args.quiet,
        show_error_codes=not args.no_error_codes,
        tests_only=args.tests_only,
        split_mode=args.split_mode,
    )


if __name__ == "__main__":
    sys.exit(main())
