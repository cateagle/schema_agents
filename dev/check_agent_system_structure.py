#!/usr/bin/env python3
"""
Agent System Structure Validator

This script validates the structure and naming conventions of the agent system package.
It checks module organization, imports, and class definitions according to the specified rules.
Now integrated with the component registry for comprehensive validation.
"""

import os
import ast
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
import importlib
import importlib.util


class AgentSystemValidator:
    """Validates the structure of the agent system package."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.errors = []
        self.warnings = []
        
    def log_error(self, message: str):
        """Log an error message."""
        self.errors.append(message)
        print(f"ERROR: {message}")
        
    def log_warning(self, message: str):
        """Log a warning message."""
        self.warnings.append(message)
        print(f"WARNING: {message}")
        
    def log_info(self, message: str):
        """Log an info message."""
        print(f"INFO: {message}")
        
    def extract_classes_from_file(self, file_path: Path) -> List[str]:
        """Extract class names from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    
            return classes
        except Exception as e:
            self.log_error(f"Failed to parse {file_path}: {e}")
            return []
    
    def extract_imports_from_file(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """Extract import statements from a Python file. Returns (absolute_imports, relative_imports)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            absolute_imports = []
            relative_imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        absolute_imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:  # Relative import
                        module = node.module or ""
                        for alias in node.names:
                            relative_imports.append(f"{'.' * node.level}{module}.{alias.name}")
                    else:  # Absolute import
                        module = node.module or ""
                        for alias in node.names:
                            absolute_imports.append(f"{module}.{alias.name}" if module else alias.name)
                            
            return absolute_imports, relative_imports
        except Exception as e:
            self.log_error(f"Failed to parse imports from {file_path}: {e}")
            return [], []
    
    def extract_all_list(self, file_path: Path) -> Optional[List[str]]:
        """Extract the __all__ list from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if (isinstance(node, ast.Assign) and 
                    len(node.targets) == 1 and 
                    isinstance(node.targets[0], ast.Name) and 
                    node.targets[0].id == '__all__'):
                    
                    if isinstance(node.value, ast.List):
                        result = []
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                result.append(elt.value)
                        return result
                    elif isinstance(node.value, ast.Constant) and isinstance(node.value.value, list):
                        return node.value.value
                        
            return None
        except Exception as e:
            self.log_error(f"Failed to extract __all__ from {file_path}: {e}")
            return None
    
    def check_core_module(self) -> bool:
        """Check the core module structure."""
        self.log_info("Checking core module...")
        
        core_dir = self.base_dir / "agent_system" / "core"
        init_file = core_dir / "__init__.py"
        
        if not core_dir.exists():
            self.log_error("Core directory does not exist")
            return False
            
        if not init_file.exists():
            self.log_error("Core __init__.py does not exist")
            return False
        
        # Check that core module contains Agent, LLMApi, and Tool classes
        expected_classes = {"Agent", "LLMApi", "Tool"}
        found_classes = set()
        
        for py_file in core_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            classes = self.extract_classes_from_file(py_file)
            found_classes.update(classes)
        
        missing_classes = expected_classes - found_classes
        if missing_classes:
            self.log_error(f"Core module missing classes: {missing_classes}")
        
        # Check __init__.py imports
        all_list = self.extract_all_list(init_file)
        if all_list is None:
            self.log_error("Core __init__.py missing __all__ list")
        elif set(all_list) != expected_classes:
            self.log_error(f"Core __init__.py __all__ should contain {expected_classes}, found {set(all_list)}")
        
        # Check for absolute imports only
        abs_imports, rel_imports = self.extract_imports_from_file(init_file)
        if rel_imports:
            self.log_error(f"Core __init__.py contains relative imports: {rel_imports}")
        
        return len([e for e in self.errors if "Core" in e]) == 0
    
    def check_module_structure(self, module_name: str, suffix: str, class_suffix: str) -> bool:
        """Generic method to check module structure (tools, agents, llm_apis)."""
        self.log_info(f"Checking {module_name} module...")
        
        module_dir = self.base_dir / "agent_system" / module_name
        init_file = module_dir / "__init__.py"
        
        if not module_dir.exists():
            self.log_error(f"{module_name.title()} directory does not exist")
            return False
            
        if not init_file.exists():
            self.log_error(f"{module_name.title()} __init__.py does not exist")
            return False
        
        # Find all Python files in the module directory
        py_files = [f for f in module_dir.glob("*.py") if f.name != "__init__.py"]
        expected_classes = []
        
        for py_file in py_files:
            # Check file naming convention
            if not py_file.name.endswith(f"_{suffix}.py"):
                self.log_error(f"File {py_file.name} should end with '_{suffix}.py'")
                continue
            
            # Check class definitions
            classes = self.extract_classes_from_file(py_file)
            
            # Find classes with the required suffix
            suffix_classes = [cls for cls in classes if cls.endswith(class_suffix)]
            
            if len(suffix_classes) != 1:
                self.log_error(f"File {py_file.name} should contain exactly one class ending with '{class_suffix}', found {len(suffix_classes)}: {suffix_classes}")
                continue
                
            class_name = suffix_classes[0]
            expected_classes.append(class_name)
            
            # Check for absolute imports only
            abs_imports, rel_imports = self.extract_imports_from_file(py_file)
            if rel_imports:
                self.log_error(f"{py_file.name} contains relative imports: {rel_imports}")
        
        # Check __init__.py structure
        all_list = self.extract_all_list(init_file)
        if all_list is None:
            self.log_error(f"{module_name.title()} __init__.py missing __all__ list")
        elif set(all_list) != set(expected_classes):
            self.log_error(f"{module_name.title()} __init__.py __all__ should contain {set(expected_classes)}, found {set(all_list)}")
        
        # Check for absolute imports only in __init__.py
        abs_imports, rel_imports = self.extract_imports_from_file(init_file)
        if rel_imports:
            self.log_error(f"{module_name.title()} __init__.py contains relative imports: {rel_imports}")
        
        return len([e for e in self.errors if module_name.title() in e]) == 0
    
    def check_tools_module(self) -> bool:
        """Check the tools module structure."""
        return self.check_module_structure("tools", "tool", "Tool")
    
    def check_agents_module(self) -> bool:
        """Check the agents module structure."""
        return self.check_module_structure("agents", "agent", "Agent")
    
    def check_llm_apis_module(self) -> bool:
        """Check the llm_apis module structure."""
        return self.check_module_structure("llm_apis", "llm_api", "LLMApi")
    
    def update_init_file(self, module_name: str, suffix: str, class_suffix: str):
        """Update __init__.py file for a module."""
        self.log_info(f"Updating {module_name} __init__.py...")
        
        module_dir = self.base_dir / "agent_system" / module_name
        init_file = module_dir / "__init__.py"
        
        if not module_dir.exists():
            self.log_error(f"{module_name.title()} directory does not exist")
            return
        
        # Find all Python files and extract classes
        py_files = [f for f in module_dir.glob("*.py") if f.name != "__init__.py"]
        imports = []
        all_classes = []
        
        for py_file in py_files:
            if py_file.name.endswith(f"_{suffix}.py"):
                classes = self.extract_classes_from_file(py_file)
                # Find classes with the required suffix
                suffix_classes = [cls for cls in classes if cls.endswith(class_suffix)]
                
                if len(suffix_classes) == 1:
                    module_path = f"agent_system.{module_name}.{py_file.stem}"
                    class_name = suffix_classes[0]
                    imports.append(f"from {module_path} import {class_name}")
                    all_classes.append(class_name)
        
        # Generate __init__.py content
        content = f'"""\n{module_name.title()} module for the agent system.\n\n'
        
        if module_name == "tools":
            content += "This module contains various tools that agents can use to complete tasks.\n"
        elif module_name == "agents":
            content += "This module contains pre-configured agent classes for common tasks.\n"
        elif module_name == "llm_apis":
            content += "This module contains implementations for different LLM API providers.\n"
        
        content += '"""\n\n'
        
        for import_line in sorted(imports):
            content += import_line + '\n'
        
        content += f'\n__all__ = {sorted(all_classes)}\n'
        
        # Write the file
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.log_info(f"Updated {init_file}")
    
    def update_core_init_file(self):
        """Update core __init__.py file."""
        self.log_info("Updating core __init__.py...")
        
        core_dir = self.base_dir / "agent_system" / "core"
        init_file = core_dir / "__init__.py"
        
        if not core_dir.exists():
            self.log_error("Core directory does not exist")
            return
        
        content = '''"""
Agent System Core Module

This module provides the core components for the agent system:
- Agent: The main agent class that executes tasks
- LLMApi: Interface for LLM API providers
- Tool: Base class for agent tools
"""

from agent_system.core.agent import Agent
from agent_system.core.llm_api import LLMApi
from agent_system.core.tool import Tool

__all__ = ["Agent", "LLMApi", "Tool"]
'''
        
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.log_info(f"Updated {init_file}")
    
    def generate_component_report(self) -> Dict[str, List[str]]:
        """Generate a report of all registered components."""
        report = {
            'tools': [],
            'agents': [],
            'llm_apis': []
        }
        
        # Check each module type
        for module_name, suffix, class_suffix in [
            ('tools', 'tool', 'Tool'),
            ('agents', 'agent', 'Agent'),
            ('llm_apis', 'llm_api', 'LLMApi')
        ]:
            module_dir = self.base_dir / "agent_system" / module_name
            
            if not module_dir.exists():
                continue
                
            # Find all Python files and extract classes
            py_files = [f for f in module_dir.glob("*.py") if f.name != "__init__.py"]
            
            for py_file in py_files:
                if py_file.name.endswith(f"_{suffix}.py"):
                    classes = self.extract_classes_from_file(py_file)
                    # Find classes with the required suffix
                    suffix_classes = [cls for cls in classes if cls.endswith(class_suffix)]
                    
                    for class_name in suffix_classes:
                        report[module_name].append({
                            'class': class_name,
                            'file': py_file.name,
                            'path': str(py_file.relative_to(self.base_dir))
                        })
        
        return report
    
    def print_component_report(self, report: Dict[str, List[str]]):
        """Print a formatted component report."""
        print("\n" + "="*50)
        print("REGISTERED COMPONENTS REPORT")
        print("="*50)
        
        for module_name in ['tools', 'agents', 'llm_apis']:
            components = report[module_name]
            module_title = module_name.replace('_', ' ').title()
            
            print(f"\n📦 {module_title} ({len(components)} found):")
            all_lengths = [len(comp['class']) for comp in components]
            max_length = max(all_lengths) if all_lengths else 10
            if not components:
                print("   No components found")
            else:
                for comp in sorted(components, key=lambda x: x['class']):

                    print(f"   • {comp['class']}{' ' * (max_length - len(comp['class']))}\t{comp['file']}")

        # Summary statistics
        total_components = sum(len(report[key]) for key in report)
        print(f"\n📊 Total Components: {total_components}")
        print(f"   Tools: {len(report['tools'])}")
        print(f"   Agents: {len(report['agents'])}")
        print(f"   LLM APIs: {len(report['llm_apis'])}")
    
    def check_registry_integration(self) -> bool:
        """Check if components are properly registered in the registry."""
        self.log_info("Checking registry integration...")
        
        try:
            # Import the registry
            sys.path.insert(0, str(self.base_dir))
            from agent_system.core.registry import get_registry
            
            registry = get_registry()
            
            # Validate registry contents
            validation_errors = registry.validate_naming_conventions()
            for error in validation_errors:
                self.log_error(f"Registry validation: {error}")
            
            # Generate registry report
            report = registry.generate_report()
            
            print("\n" + "="*50)
            print("REGISTRY REPORT")
            print("="*50)
            
            print(f"\nTotal registered components: {report['total_components']}")
            print(f"Tools: {len(report['tools'])}")
            print(f"Agents: {len(report['agents'])}")
            print(f"LLM APIs: {len(report['llm_apis'])}")
            print(f"Exceptions: {len(report['exceptions'])}")
            
            # Check for unregistered components
            self._check_unregistered_components(registry)
            
            return len(validation_errors) == 0
            
        except ImportError as e:
            self.log_error(f"Failed to import registry: {e}")
            return False
        finally:
            # Clean up sys.path
            if str(self.base_dir) in sys.path:
                sys.path.remove(str(self.base_dir))
    
    def _check_unregistered_components(self, registry):
        """Check for components that should be registered but aren't."""
        # Check tools
        tools_dir = self.base_dir / "agent_system" / "tools"
        if tools_dir.exists():
            for py_file in tools_dir.glob("*_tool.py"):
                if py_file.name == "__init__.py":
                    continue
                classes = self.extract_classes_from_file(py_file)
                for cls in classes:
                    if cls.endswith("Tool") and not registry.is_registered(cls):
                        self.log_warning(f"Tool class '{cls}' is not registered")
        
        # Check agents
        agents_dir = self.base_dir / "agent_system" / "agents"
        if agents_dir.exists():
            for py_file in agents_dir.glob("*_agent.py"):
                if py_file.name == "__init__.py":
                    continue
                classes = self.extract_classes_from_file(py_file)
                for cls in classes:
                    if cls.endswith("Agent") and not registry.is_registered(cls):
                        self.log_warning(f"Agent class '{cls}' is not registered")
    
    def run_validation(self, check_core: bool, check_tools: bool, check_agents: bool, check_llm_apis: bool, update: bool, check_registry: bool):
        """Run the validation process."""
        self.log_info(f"Validating agent system structure in {self.base_dir}")
        
        # If no specific modules are specified, check all
        if not any([check_core, check_tools, check_agents, check_llm_apis, check_registry]):
            check_core = check_tools = check_agents = check_llm_apis = check_registry = True
        
        if update:
            if check_core:
                self.update_core_init_file()
            if check_tools:
                self.update_init_file("tools", "tool", "Tool")
            if check_agents:
                self.update_init_file("agents", "agent", "Agent")
            if check_llm_apis:
                self.update_init_file("llm_apis", "llm_api", "LLMApi")
            return
        
        # Run validation
        results = {}
        
        if check_core:
            results['core'] = self.check_core_module()
        if check_tools:
            results['tools'] = self.check_tools_module()
        if check_agents:
            results['agents'] = self.check_agents_module()
        if check_llm_apis:
            results['llm_apis'] = self.check_llm_apis_module()
        if check_registry:
            results['registry'] = self.check_registry_integration()
        
        # Generate and print component report
        report = self.generate_component_report()
        self.print_component_report(report)
        
        # Print validation summary
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        
        for module, passed in results.items():
            status = "PASS" if passed else "FAIL"
            print(f"{module.upper()}: {status}")
        
        if self.errors:
            print(f"\nTotal errors: {len(self.errors)}")
        if self.warnings:
            print(f"Total warnings: {len(self.warnings)}")
        
        if not self.errors:
            print("\n✅ All checks passed!")
        else:
            print("\n❌ Validation failed. Please fix the errors above.")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate the structure of the agent system package"
    )
    
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to check (default: current directory)"
    )
    
    parser.add_argument(
        "--core",
        action="store_true",
        help="Check the core module"
    )
    
    parser.add_argument(
        "--tools",
        action="store_true",
        help="Check the tools module"
    )
    
    parser.add_argument(
        "--agents",
        action="store_true",
        help="Check the agents module"
    )
    
    parser.add_argument(
        "--llm_apis",
        action="store_true",
        help="Check the llm_apis module"
    )
    
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update the __init__.py files"
    )
    
    parser.add_argument(
        "--registry",
        action="store_true",
        help="Check the component registry"
    )
    
    args = parser.parse_args()
    
    validator = AgentSystemValidator(args.directory)
    validator.run_validation(
        check_core=args.core,
        check_tools=args.tools,
        check_agents=args.agents,
        check_llm_apis=args.llm_apis,
        update=args.update,
        check_registry=args.registry
    )


if __name__ == "__main__":
    main()