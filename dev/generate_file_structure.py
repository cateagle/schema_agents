# FILE: dev/generate_file_structure.py
"""
Generate file structure documentation in markdown format.
Uses git to discover files and applies configurable patterns for comments.
Fully generic and reusable across Python projects via TOML configuration.
"""

import sys
from pathlib import Path

# Get project root (parent of dev directory)
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import subprocess
import argparse
import fnmatch
from typing import Dict, List, Set, Optional, Tuple, Any, Union
import toml


class FileStructureConfig:
    """Configuration loader for file structure generator."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.get_default_config_path()
        self._config: Optional[Dict[str, Any]] = None

    @staticmethod
    def get_default_config_path() -> Path:
        """Get default config path in dev/config directory."""
        dev_root = Path(__file__).parent.absolute()
        return dev_root / "config" / "file_structure_config.toml"

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from TOML file."""
        if self._config is None:
            try:
                if self.config_path.exists() and toml is not None:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        self._config = toml.load(f)
                else:
                    raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            except Exception as e:
                raise RuntimeError(f"Could not load config from {self.config_path}: {e}")
        return self._config

    def get_path_patterns(self) -> Dict[str, str]:
        """Get flattened path patterns from all categories."""
        config = self.load_config()
        path_patterns: Dict[str, str] = {}

        # Flatten all path pattern categories into a single dictionary
        pattern_sections = config.get("path_patterns", {})
        for category, patterns in pattern_sections.items():
            if isinstance(patterns, dict):
                path_patterns.update(patterns)

        return path_patterns

    def get_formatting_config(self) -> Dict[str, Union[int, str, bool]]:
        """Get formatting configuration."""
        config = self.load_config()
        formatting = config.get("formatting", {})
        # Ensure type safety by validating the structure
        result: Dict[str, Union[int, str, bool]] = {}
        for key, value in formatting.items():
            if isinstance(value, (int, str, bool)):
                result[key] = value
        return result

    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration."""
        config = self.load_config()
        return config.get("validation", {})

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        config = self.load_config()
        return config.get("output", {})

    def get_section_templates(self) -> Dict[str, Any]:
        """Get section templates."""
        config = self.load_config()
        return config.get("section_templates", {})

    def get_common_directories(self) -> Dict[str, Any]:
        """Get common directories configuration."""
        config = self.load_config()
        return config.get("common_directories", {})

    def get_key_directories(self) -> Dict[str, Any]:
        """Get key directories configuration."""
        config = self.load_config()
        return config.get("key_directories", {})

    def get_file_naming_conventions(self) -> Dict[str, str]:
        """Get file naming conventions."""
        config = self.load_config()
        conventions = config.get("file_naming_conventions", {})
        # Ensure all values are strings
        result: Dict[str, str] = {}
        for key, value in conventions.items():
            if isinstance(value, str):
                result[key] = value
        return result

    def get_directory_limits(self) -> Dict[str, int]:
        """Get directory depth limits configuration."""
        config = self.load_config()
        return config.get("directory_limits", {})

    def get_incomplete_patterns(self) -> Dict[str, str]:
        """Get special comments for incomplete/limited directories."""
        config = self.load_config()
        return config.get("incomplete_patterns", {})


class FileStructureGenerator:
    """Generates file structure documentation from git tracked files using configurable patterns."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        min_comment_distance: Optional[int] = None,
        comment_indent_step: Optional[int] = None,
        config_path: Optional[Path] = None,
    ):
        self.project_root = project_root or self.get_project_root()
        self.config = FileStructureConfig(config_path)

        # Load formatting config
        formatting_config = self.config.get_formatting_config()

        # Use provided parameters or fall back to config, then defaults
        # Ensure we get int values from config
        config_min_distance = formatting_config.get("min_comment_distance")
        if isinstance(config_min_distance, int):
            default_min_distance = config_min_distance
        else:
            default_min_distance = 2

        config_indent_step = formatting_config.get("comment_indent_step")
        if isinstance(config_indent_step, int):
            default_indent_step = config_indent_step
        else:
            default_indent_step = 4

        self.min_comment_distance = (
            min_comment_distance if min_comment_distance is not None else default_min_distance
        )
        self.comment_indent_step = (
            comment_indent_step if comment_indent_step is not None else default_indent_step
        )

        # Project name handling
        project_name_override = formatting_config.get("project_name_override", "")
        if isinstance(project_name_override, str) and project_name_override:
            self.project_name = project_name_override
        else:
            self.project_name = self.project_root.name

        # Load path patterns from config
        self.path_patterns: Dict[str, str] = self.config.get_path_patterns()

        # Load directory limits from config
        self.directory_limits: Dict[str, int] = self.config.get_directory_limits()

        # Display options from config
        show_file_counts = formatting_config.get("show_file_counts", True)
        show_additional_sections = formatting_config.get("show_additional_sections", True)
        show_key_directories = formatting_config.get("show_key_directories", True)

        self.show_file_counts = isinstance(show_file_counts, bool) and show_file_counts
        self.show_additional_sections = (
            isinstance(show_additional_sections, bool) and show_additional_sections
        )
        self.show_key_directories = isinstance(show_key_directories, bool) and show_key_directories

    @staticmethod
    def get_project_root() -> Path:
        """Get project root by finding the directory containing dev/generate_file_structure.py."""
        script_dir = Path(__file__).parent.absolute()
        return script_dir.parent

    def get_git_files(self) -> List[Path]:
        """Get all git-tracked, staged, and working directory files."""
        try:
            # Get committed files
            committed_result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            committed_files = (
                set(committed_result.stdout.strip().split("\n"))
                if committed_result.stdout.strip()
                else set()
            )

            # Get staged files (in index)
            staged_result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            staged_files = (
                set(staged_result.stdout.strip().split("\n"))
                if staged_result.stdout.strip()
                else set()
            )

            # Get modified files in working directory
            modified_result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            modified_files = (
                set(modified_result.stdout.strip().split("\n"))
                if modified_result.stdout.strip()
                else set()
            )

            # Get untracked files (but be selective to avoid performance issues)
            untracked_result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            untracked_files = (
                set(untracked_result.stdout.strip().split("\n"))
                if untracked_result.stdout.strip()
                else set()
            )

            # Combine all files and filter out empty strings
            all_files = (committed_files | staged_files | modified_files | untracked_files) - {""}

            # Convert to Path objects and filter for existing files
            paths = []
            for file_str in all_files:
                if file_str:  # Skip empty strings
                    path = self.project_root / file_str
                    if path.exists():  # Only include files that actually exist
                        paths.append(path)

            return sorted(paths)

        except subprocess.CalledProcessError as e:
            print(f"Error running git command: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return []

    def should_limit_directory_depth(self, dir_path: str) -> Optional[int]:
        """Check if a directory should have limited depth and return the limit."""
        for pattern, limit in self.directory_limits.items():
            if fnmatch.fnmatch(dir_path, pattern) or dir_path.startswith(pattern.rstrip("/*")):
                return limit
        return None

    def build_tree_structure(self, files: List[Path]) -> Dict[str, Any]:
        """Build hierarchical tree structure from file paths with directory depth limits."""
        tree: Dict[str, Any] = {}

        for file_path in files:
            relative_path = file_path.relative_to(self.project_root)
            parts = relative_path.parts

            current = tree
            current_path = ""

            for i, part in enumerate(parts):
                current_path = "/".join(parts[: i + 1]) if current_path else part

                # Check if we should limit depth for this directory
                if i < len(parts) - 1:  # Not the final file
                    depth_limit = self.should_limit_directory_depth(current_path)
                    if depth_limit is not None and i >= depth_limit:
                        # We've reached the depth limit, mark the directory as incomplete and stop
                        if part not in current:
                            current[part] = {
                                "type": "dir",
                                "path": self.project_root / current_path,
                                "incomplete": True,
                            }
                        else:
                            current[part]["incomplete"] = True
                        break

                if part not in current:
                    if i == len(parts) - 1:  # This is a file
                        current[part] = {"type": "file", "path": file_path}
                    else:  # This is a directory
                        current[part] = {"type": "dir", "path": self.project_root / current_path}

                if current[part]["type"] == "dir" and "children" not in current[part]:
                    current[part]["children"] = {}

                if current[part]["type"] == "dir" and not current[part].get("incomplete", False):
                    current = current[part]["children"]
                else:
                    break  # We've reached a file or incomplete directory, stop traversing

        return tree

    def get_path_comment_from_patterns(self, path: str, is_incomplete: bool = False) -> str:
        """Get comment for a path using pattern matching."""
        # Normalize path separators for matching
        normalized_path = str(Path(path))

        # Check for incomplete directory special comments first
        if is_incomplete:
            incomplete_patterns = self.config.get_incomplete_patterns()
            for pattern, comment in incomplete_patterns.items():
                normalized_pattern = str(Path(pattern))
                if normalized_path == normalized_pattern or normalized_path.endswith(
                    "/" + normalized_pattern
                ):
                    return comment
                if fnmatch.fnmatch(normalized_path, pattern):
                    return comment

        # Try exact matches first
        for pattern, comment in self.path_patterns.items():
            # Normalize pattern as well
            normalized_pattern = str(Path(pattern))
            if normalized_path == normalized_pattern or normalized_path.endswith(
                "/" + normalized_pattern
            ):
                return comment

        # Try pattern matches
        for pattern, comment in self.path_patterns.items():
            if fnmatch.fnmatch(normalized_path, pattern):
                return comment

        # Try basename matches for files
        basename = Path(path).name
        for pattern, comment in self.path_patterns.items():
            if fnmatch.fnmatch(basename, pattern):
                return comment

        return ""

    def calculate_comment_position(self, name: str, depth: int) -> int:
        """Calculate the position where comments should start for alignment."""
        base_indent = depth * 4  # 4 spaces per level
        name_length = len(name)
        total_width = base_indent + name_length + self.min_comment_distance

        # Round up to the next multiple of comment_indent_step
        aligned_position = (
            (total_width + self.comment_indent_step - 1) // self.comment_indent_step
        ) * self.comment_indent_step

        return max(aligned_position, total_width)

    def format_tree_markdown(
        self, tree: Dict[str, Any], prefix: str, path_prefix: str
    ) -> List[str]:
        """Format tree structure as markdown with aligned comments."""
        lines: List[str] = []

        items = sorted(tree.items(), key=lambda x: (x[1].get("type", "dir") != "dir", x[0]))

        for i, (name, info) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            full_line_prefix = prefix + current_prefix

            # Calculate depth for comment alignment
            depth = len(prefix) // 4

            # Get the relative path for pattern matching
            if info.get("path"):
                try:
                    relative_path = str(info["path"].relative_to(self.project_root))
                except ValueError:
                    relative_path = path_prefix + "/" + name if path_prefix else name
            else:
                relative_path = path_prefix + "/" + name if path_prefix else name

            # Check if this is an incomplete directory
            is_incomplete = info.get("incomplete", False)

            comment = self.get_path_comment_from_patterns(relative_path, is_incomplete)

            # Create the base line
            base_line = f"{full_line_prefix}{name}"

            if comment:
                # Calculate where comments should be aligned
                comment_position = self.calculate_comment_position(name, depth + 1)
                current_length = len(base_line)

                if current_length < comment_position:
                    spacing = " " * (comment_position - current_length)
                else:
                    spacing = " " * self.min_comment_distance

                final_line = f"{base_line}{spacing}# {comment}"
            else:
                final_line = base_line

            lines.append(final_line)

            # Handle subdirectories (but not if incomplete)
            if (
                info.get("type") == "dir"
                and "children" in info
                and info["children"]
                and not is_incomplete
            ):
                next_prefix = prefix + ("    " if is_last else "│   ")
                next_path_prefix = relative_path
                child_lines = self.format_tree_markdown(
                    info["children"], next_prefix, next_path_prefix
                )
                lines.extend(child_lines)

        return lines

    def validate_patterns(self) -> Tuple[bool, List[str]]:
        """Validate that path patterns are being used."""
        validation_config = self.config.get_validation_config()

        if not validation_config.get("warn_unused_patterns", False):
            return True, []

        files = self.get_git_files()
        used_patterns = set()
        warnings = []

        for file_path in files:
            relative_path = str(file_path.relative_to(self.project_root))
            for pattern in self.path_patterns:
                if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(
                    Path(relative_path).name, pattern
                ):
                    used_patterns.add(pattern)

        unused_patterns = set(self.path_patterns.keys()) - used_patterns
        for pattern in unused_patterns:
            warnings.append(f"Unused pattern: {pattern}")

        require_all_used = validation_config.get("require_all_patterns_used", False)
        is_valid = not require_all_used or len(unused_patterns) == 0

        return is_valid, warnings

    def generate_additional_sections(self) -> List[str]:
        """Generate additional sections from config."""
        if not self.show_additional_sections:
            return []

        lines: List[str] = []

        # Check if we should include file naming conventions
        conventions = self.config.get_file_naming_conventions()
        if conventions:
            lines.extend(self.generate_file_naming_conventions_section())

        # Check if we should include key directories section
        if self.show_key_directories:
            lines.extend(self.generate_key_directories_section())

        return lines

    def generate_key_directories_section(self) -> List[str]:
        """Generate key directories section from config."""
        if not self.show_key_directories:
            return []

        lines: List[str] = [
            "",
            "## Key Directories",
            "",
        ]

        # Get section templates for intro
        templates = self.config.get_section_templates()
        key_dirs_intro = templates.get("key_directories_intro", {})
        intro_desc = key_dirs_intro.get("description", [])
        if isinstance(intro_desc, list):
            for desc_line in intro_desc:
                lines.append(desc_line)

        if intro_desc:
            lines.append("")

        # Get key directories from config
        key_dirs = self.config.get_key_directories()

        for section_key, section_config in key_dirs.items():
            if isinstance(section_config, dict):
                title = section_config.get("title", section_key.replace("_", " ").title())
                description = section_config.get("description", "")

                lines.append(f"### {title}")
                if description:
                    lines.append(f"{description}")
                lines.append("")

        return lines

    def generate_file_naming_conventions_section(self) -> List[str]:
        """Generate file naming conventions section from config."""
        lines: List[str] = [
            "## File Naming Conventions",
            "",
        ]

        conventions = self.config.get_file_naming_conventions()

        for convention_text in conventions.values():
            lines.append(f"- {convention_text}")

        lines.append("")
        return lines

    def generate_documentation(self) -> str:
        """Generate complete file structure documentation."""
        files = self.get_git_files()

        if not files:
            return "Error: Could not retrieve git files. Make sure you're in a git repository."

        tree = self.build_tree_structure(files)
        tree_lines = self.format_tree_markdown(tree, "", "")

        # Count statistics
        file_count = len([f for f in files if f.is_file()])
        dir_count = len(set(f.parent for f in files if f.parent != self.project_root))

        # Get header template
        templates = self.config.get_section_templates()
        header_template = templates.get("header", {})

        title_template = header_template.get("title_template", "# {project_name} - File Structure")
        title = title_template.format(project_name=self.project_name)

        # Add navigation links below title
        navigation_line = "[← Back to README](../README.md) | [Documentation](documentation.md)"

        description_lines = header_template.get(
            "description",
            [
                "This document provides an overview of the project file organization.",
                "The structure is automatically generated from git-tracked files.",
            ],
        )

        # Prepare sections
        sections = [title, "", navigation_line, ""]

        # Add description
        if isinstance(description_lines, list):
            sections.extend(description_lines)
        sections.append("")

        # Add statistics if enabled
        if self.show_file_counts:
            statistics_template = header_template.get(
                "statistics_template", "**Statistics**: {file_count} files, {dir_count} directories"
            )
            statistics_line = statistics_template.format(file_count=file_count, dir_count=dir_count)
            sections.extend([statistics_line, ""])

        # Main structure section
        sections.extend(
            [
                "## Project Structure",
                "",
                "```",
                self.project_name + "/",
            ]
        )

        sections.extend(tree_lines)
        sections.append("```")

        # Add additional sections
        additional_sections = self.generate_additional_sections()
        sections.extend(additional_sections)

        # Add footer if configured
        footer_template = templates.get("footer", {})
        if footer_template:
            footer_text = footer_template.get("text", "")
            if footer_text:
                sections.extend(["", footer_text])

        return "\n".join(sections)


def main():
    """Main function to run the file structure generator."""
    parser = argparse.ArgumentParser(description="Generate file structure documentation")

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate subcommand
    generate_parser = subparsers.add_parser(
        "generate", help="Generate file structure documentation"
    )
    generate_parser.add_argument("--project-root", type=Path, help="Project root directory")
    generate_parser.add_argument("--output", type=Path, help="Output file path")
    generate_parser.add_argument("--config", type=Path, help="Configuration file path")
    generate_parser.add_argument(
        "--min-comment-distance", type=int, help="Minimum spaces before comments"
    )
    generate_parser.add_argument("--comment-indent-step", type=int, help="Comment alignment step")

    # Validate subcommand
    validate_parser = subparsers.add_parser(
        "validate", help="Validate that documentation is up to date"
    )
    validate_parser.add_argument("--project-root", type=Path, help="Project root directory")
    validate_parser.add_argument("--config", type=Path, help="Configuration file path")
    validate_parser.add_argument("--output", type=Path, help="Documentation file to check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Only pass formatting arguments if they exist (for generate command)
        generator_kwargs = {
            "project_root": args.project_root,
            "config_path": args.config,
        }

        if hasattr(args, "min_comment_distance") and args.min_comment_distance is not None:
            generator_kwargs["min_comment_distance"] = args.min_comment_distance

        if hasattr(args, "comment_indent_step") and args.comment_indent_step is not None:
            generator_kwargs["comment_indent_step"] = args.comment_indent_step

        generator = FileStructureGenerator(**generator_kwargs)

        if args.command == "generate":
            documentation = generator.generate_documentation()

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(documentation)
                print(f"Documentation written to {args.output}")
            else:
                print(documentation)

        elif args.command == "validate":
            # Check if documentation is up to date
            current_docs = generator.generate_documentation()

            output_file = args.output or Path("doc/file_structure.md")

            if not output_file.exists():
                print(f"Error: Documentation file {output_file} does not exist", file=sys.stderr)
                print("Run with 'generate' command to create it", file=sys.stderr)
                sys.exit(1)

            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_docs = f.read()
            except Exception as e:
                print(f"Error reading {output_file}: {e}", file=sys.stderr)
                sys.exit(1)

            if current_docs.strip() != existing_docs.strip():
                print(f"Error: Documentation file {output_file} is out of date", file=sys.stderr)
                print("Run with 'generate' command to update it", file=sys.stderr)
                sys.exit(1)
            else:
                print("Documentation is up to date")

            # Also validate patterns
            is_valid, warnings = generator.validate_patterns()
            if warnings:
                for warning in warnings:
                    print(f"Warning: {warning}", file=sys.stderr)
            if not is_valid:
                print("Pattern validation failed", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
