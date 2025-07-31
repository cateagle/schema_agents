"""
Result analysis and processing logic using the agent system.
"""

import json
from typing import Dict, Any, List, Optional
from agent_system.llm_apis import OpenRouterLLMApi
from agent_system.core import Message
from agent_system.tools import JSONAnalysisTool, JSONAnalysisConfig, JSONAnalysisInput

from streamlit_app.config.prompts.analysis_prompts import (
    RESULT_INTERPRETATION_PROMPT,
    RESEARCH_SUMMARY_PROMPT,
    QUALITY_ASSESSMENT_PROMPT
)


class ResultProcessor:
    """Handles result analysis and interpretation."""
    
    def __init__(self, openrouter_api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.api_key = openrouter_api_key
        self.model = model
        
        # Initialize LLM API for agent system
        self.llm_api = OpenRouterLLMApi({
            "api_key": openrouter_api_key,
            "model": model,
            "temperature": 0.3
        })
        
        # Initialize JSON analysis tool
        self.json_analysis_tool = JSONAnalysisTool(
            config=JSONAnalysisConfig(
                include_patterns=True,
                include_quality_checks=True
            )
        )
    
    def analyze_results(
        self, 
        query: str, 
        schema: Dict[str, Any], 
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze research results using agent system tools."""
        try:
            # Use JSON analysis tool to analyze results
            analysis_input = JSONAnalysisInput(
                json_data=results,
                focus_areas=list(schema.get("properties", {}).keys()),
                quality_threshold=0.7
            )
            
            # Get structured analysis from tool
            tool_result = self.json_analysis_tool.call(analysis_input)
            
            # Generate additional insights using LLM
            conversation = [
                Message(role="system", content=RESULT_INTERPRETATION_PROMPT.format(
                    query=query,
                    schema=json.dumps(schema, indent=2),
                    results=self._prepare_results_for_analysis(results)
                )),
                Message(role="user", content="Please analyze these research results and provide insights.")
            ]
            
            response = self.llm_api.chat_completion(conversation)
            
            # Calculate basic metrics
            metrics = self._calculate_result_metrics(results, schema)
            
            return {
                "analysis": response.content.strip(),
                "tool_analysis": tool_result,
                "metrics": metrics,
                "total_results": len(results),
                "quality_score": self._calculate_quality_score(results, schema)
            }
            
        except Exception as e:
            return {
                "analysis": f"Error analyzing results: {str(e)}",
                "metrics": {},
                "total_results": len(results),
                "quality_score": 0
            }
    
    def generate_research_summary(
        self,
        topic: str,
        results: List[Dict[str, Any]],
        agent_count: int,
        execution_time: float,
        key_findings: str = ""
    ) -> str:
        """Generate a comprehensive research summary using agent system."""
        try:
            conversation = [
                Message(role="system", content=RESEARCH_SUMMARY_PROMPT.format(
                    topic=topic,
                    total_results=len(results),
                    agent_count=agent_count,
                    execution_time=f"{execution_time:.1f}s",
                    findings=key_findings or "Various research insights discovered"
                )),
                Message(role="user", content="Please generate a comprehensive research summary.")
            ]
            
            response = self.llm_api.chat_completion(conversation)
            return response.content.strip()
            
        except Exception as e:
            return f"Error generating research summary: {str(e)}"
    
    def assess_result_quality(
        self, 
        schema: Dict[str, Any], 
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess the quality of research results using agent system."""
        try:
            results_text = self._prepare_results_for_analysis(results, max_results=10)
            
            conversation = [
                Message(role="system", content=QUALITY_ASSESSMENT_PROMPT.format(
                    schema=json.dumps(schema, indent=2),
                    results=results_text
                )),
                Message(role="user", content="Please assess the quality of these research results.")
            ]
            
            response = self.llm_api.chat_completion(conversation)
            
            # Calculate additional quality metrics
            completeness = self._calculate_completeness(results, schema)
            consistency = self._calculate_consistency(results)
            
            return {
                "assessment": response.content.strip(),
                "completeness_score": completeness,
                "consistency_score": consistency,
                "overall_quality": (completeness + consistency) / 2
            }
            
        except Exception as e:
            return {
                "assessment": f"Error assessing quality: {str(e)}",
                "completeness_score": 0,
                "consistency_score": 0,
                "overall_quality": 0
            }
    
    def _prepare_results_for_analysis(
        self, 
        results: List[Dict[str, Any]], 
        max_results: int = 20
    ) -> str:
        """Prepare results for LLM analysis by truncating and formatting."""
        if not results:
            return "No results to analyze"
        
        # Limit number of results to avoid token limits
        sample_results = results[:max_results]
        
        # Format results as readable text
        formatted_results = []
        for i, result in enumerate(sample_results, 1):
            result_str = f"Result {i}:\n"
            for key, value in result.items():
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                result_str += f"  {key}: {value}\n"
            formatted_results.append(result_str)
        
        results_text = "\n".join(formatted_results)
        
        if len(results) > max_results:
            results_text += f"\n... and {len(results) - max_results} more results"
        
        return results_text
    
    def _calculate_result_metrics(
        self, 
        results: List[Dict[str, Any]], 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate basic metrics about the results."""
        if not results:
            return {}
        
        # Field coverage
        schema_fields = set(schema.get("properties", {}).keys())
        field_coverage = {}
        
        for field in schema_fields:
            covered_count = sum(1 for result in results if field in result and result[field])
            field_coverage[field] = covered_count / len(results)
        
        # Required field compliance
        required_fields = schema.get("required", [])
        required_compliance = 0
        if required_fields:
            for result in results:
                if all(field in result and result[field] for field in required_fields):
                    required_compliance += 1
            required_compliance = required_compliance / len(results)
        
        return {
            "field_coverage": field_coverage,
            "required_compliance": required_compliance,
            "avg_fields_per_result": sum(len(result) for result in results) / len(results),
            "unique_sources": len(set(result.get("url", "") for result in results if result.get("url")))
        }
    
    def _calculate_quality_score(
        self, 
        results: List[Dict[str, Any]], 
        schema: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score (0-10)."""
        if not results:
            return 0
        
        # Factors for quality scoring
        completeness = self._calculate_completeness(results, schema)
        consistency = self._calculate_consistency(results)
        source_diversity = min(1.0, len(set(r.get("url", "") for r in results)) / max(1, len(results)))
        
        # Weighted average
        quality_score = (completeness * 0.4 + consistency * 0.3 + source_diversity * 0.3) * 10
        return round(quality_score, 1)
    
    def _calculate_completeness(self, results: List[Dict[str, Any]], schema: Dict[str, Any]) -> float:
        """Calculate how complete the results are compared to schema."""
        if not results:
            return 0
        
        schema_fields = set(schema.get("properties", {}).keys())
        if not schema_fields:
            return 1.0
        
        total_completeness = 0
        for result in results:
            result_fields = set(result.keys())
            completeness = len(result_fields.intersection(schema_fields)) / len(schema_fields)
            total_completeness += completeness
        
        return total_completeness / len(results)
    
    def _calculate_consistency(self, results: List[Dict[str, Any]]) -> float:
        """Calculate consistency across results."""
        if len(results) <= 1:
            return 1.0
        
        # Check field consistency
        all_fields = set()
        for result in results:
            all_fields.update(result.keys())
        
        if not all_fields:
            return 0
        
        consistency_scores = []
        for field in all_fields:
            field_present_count = sum(1 for result in results if field in result)
            field_consistency = field_present_count / len(results)
            consistency_scores.append(field_consistency)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0