"""
Agents module for the agent system.

This module contains pre-configured agent classes for common tasks.
"""

from agent_system.agents.math_solver_agent import MathSolverAgent
from agent_system.agents.research_agent import ResearchAgent
from agent_system.agents.analysis_agent import AnalysisAgent

__all__ = ["MathSolverAgent", "ResearchAgent", "AnalysisAgent"]