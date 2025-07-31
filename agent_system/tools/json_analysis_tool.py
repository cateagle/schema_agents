"""
JSON Analysis Tool for analyzing lists of JSON objects.
"""

import json
from typing import Dict, Any, List, Optional, Set
from collections import Counter
from pydantic import Field

from agent_system.core import Tool, ToolConfig, ToolInputBase, ToolOutputBase, ToolExecutionError, register_tool


class JSONAnalysisConfig(ToolConfig):
    """Configuration for JSON analysis tool."""
    max_sample_size: int = Field(default=1000, description="Maximum number of objects to analyze")
    include_patterns: bool = Field(default=True, description="Include pattern detection")
    include_quality_checks: bool = Field(default=True, description="Include quality issue detection")


class JSONAnalysisInput(ToolInputBase):
    """Input for JSON analysis tool."""
    json_data: List[Dict[str, Any]] = Field(..., description="List of JSON objects to analyze")
    focus_areas: Optional[List[str]] = Field(default=None, description="Specific areas to focus analysis on")


class JSONAnalysisOutput(ToolOutputBase):
    """Output from JSON analysis tool."""
    total_objects: int = Field(..., description="Total number of JSON objects analyzed")
    field_completeness: Dict[str, Dict[str, Any]] = Field(..., description="Completeness analysis for each field")
    quality_issues: List[str] = Field(..., description="List of quality issues found")
    patterns: Dict[str, Any] = Field(..., description="Detected patterns in the data")
    gaps: List[str] = Field(..., description="Identified gaps in the data")
    recommendations: List[str] = Field(..., description="Recommendations for improvement")


@register_tool(
    config_class=JSONAnalysisConfig,
    input_class=JSONAnalysisInput,
    output_class=JSONAnalysisOutput,
    description="Analyze lists of JSON objects for patterns, completeness, and quality"
)
class JSONAnalysisTool(Tool[JSONAnalysisConfig, JSONAnalysisInput, JSONAnalysisOutput]):
    """Tool for analyzing lists of JSON objects."""
    
    def __init__(self, config: Optional[JSONAnalysisConfig] = None, alias: Optional[str] = None):
        super().__init__(
            name="json_analysis",
            short_description="Analyze JSON object lists for patterns and quality",
            long_description="Comprehensive analysis of JSON object collections including field completeness, quality issues, pattern detection, and gap identification",
            config=config or JSONAnalysisConfig(),
            alias=alias
        )
    
    @classmethod
    def _get_config_class(cls):
        return JSONAnalysisConfig
    
    @classmethod
    def _get_input_class(cls):
        return JSONAnalysisInput
    
    @classmethod
    def _get_output_class(cls):
        return JSONAnalysisOutput
    
    def _execute(self, input_data: JSONAnalysisInput, identity: Optional[Dict[str, Any]] = None) -> JSONAnalysisOutput:
        """Execute JSON analysis."""
        try:
            json_data = input_data.json_data
            focus_areas = input_data.focus_areas or []
            
            if not json_data:
                return JSONAnalysisOutput(
                    total_objects=0,
                    field_completeness={},
                    quality_issues=["No data provided for analysis"],
                    patterns={},
                    gaps=["No data to analyze"],
                    recommendations=["Provide JSON data for analysis"]
                )
            
            # Limit sample size for performance
            sample_data = json_data[:self.config.max_sample_size]
            total_objects = len(sample_data)
            
            # Analyze field completeness
            field_completeness = self._analyze_field_completeness(sample_data)
            
            # Detect quality issues
            quality_issues = []
            if self.config.include_quality_checks:
                quality_issues = self._detect_quality_issues(sample_data, focus_areas)
            
            # Detect patterns
            patterns = {}
            if self.config.include_patterns:
                patterns = self._detect_patterns(sample_data)
            
            # Identify gaps
            gaps = self._identify_gaps(sample_data, field_completeness, focus_areas)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                sample_data, field_completeness, quality_issues, gaps
            )
            
            return JSONAnalysisOutput(
                total_objects=total_objects,
                field_completeness=field_completeness,
                quality_issues=quality_issues,
                patterns=patterns,
                gaps=gaps,
                recommendations=recommendations
            )
            
        except Exception as e:
            raise ToolExecutionError(f"JSON analysis failed: {str(e)}")
    
    def _analyze_field_completeness(self, data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze completeness of each field across the dataset."""
        if not data:
            return {}
        
        # Collect all possible fields
        all_fields: Set[str] = set()
        for obj in data:
            all_fields.update(obj.keys())
        
        field_stats = {}
        total_objects = len(data)
        
        for field in all_fields:
            present_count = 0
            non_empty_count = 0
            value_types = Counter()
            sample_values = []
            
            for obj in data:
                if field in obj:
                    present_count += 1
                    value = obj[field]
                    
                    # Count non-empty values
                    if value is not None and value != "" and value != []:
                        non_empty_count += 1
                        value_types[type(value).__name__] += 1
                        
                        # Collect sample values (first 5)
                        if len(sample_values) < 5:
                            sample_values.append(str(value)[:100])  # Truncate long values
            
            field_stats[field] = {
                "present_count": present_count,
                "present_percentage": round((present_count / total_objects) * 100, 2),
                "non_empty_count": non_empty_count,
                "non_empty_percentage": round((non_empty_count / total_objects) * 100, 2),
                "value_types": dict(value_types),
                "sample_values": sample_values
            }
        
        return field_stats
    
    def _detect_quality_issues(self, data: List[Dict[str, Any]], focus_areas: List[str]) -> List[str]:
        """Detect quality issues in the data."""
        issues = []
        
        if not data:
            return ["No data to analyze"]
        
        total_objects = len(data)
        
        # Check for empty objects
        empty_objects = sum(1 for obj in data if not obj or len(obj) == 0)
        if empty_objects > 0:
            issues.append(f"Found {empty_objects} empty objects ({(empty_objects/total_objects)*100:.1f}%)")
        
        # Check for duplicate objects
        unique_objects = set()
        duplicates = 0
        for obj in data:
            obj_str = json.dumps(obj, sort_keys=True)
            if obj_str in unique_objects:
                duplicates += 1
            else:
                unique_objects.add(obj_str)
        
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate objects ({(duplicates/total_objects)*100:.1f}%)")
        
        # Check for inconsistent field types
        field_types = {}
        for obj in data:
            for field, value in obj.items():
                if field not in field_types:
                    field_types[field] = set()
                field_types[field].add(type(value).__name__)
        
        for field, types in field_types.items():
            if len(types) > 1:
                issues.append(f"Field '{field}' has inconsistent types: {', '.join(types)}")
        
        # Check focus areas if specified
        if focus_areas:
            for area in focus_areas:
                missing_area = sum(1 for obj in data if area not in obj or not obj[area])
                if missing_area > total_objects * 0.2:  # More than 20% missing
                    issues.append(f"Focus area '{area}' is missing or empty in {missing_area} objects ({(missing_area/total_objects)*100:.1f}%)")
        
        # Check for very long or very short values
        for obj in data:
            for field, value in obj.items():
                if isinstance(value, str):
                    if len(value) > 10000:
                        issues.append(f"Field '{field}' contains very long text values (>10k characters)")
                        break
                    elif len(value) == 0:
                        continue  # Already handled in completeness analysis
        
        return issues
    
    def _detect_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns in the data."""
        if not data:
            return {}
        
        patterns = {}
        
        # URL domain patterns
        url_domains = Counter()
        for obj in data:
            for field, value in obj.items():
                if isinstance(value, str) and ('url' in field.lower() or value.startswith(('http://', 'https://'))):
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(value).netloc
                        if domain:
                            url_domains[domain] += 1
                    except:
                        continue
        
        if url_domains:
            patterns["url_domains"] = dict(url_domains.most_common(10))
        
        # Date patterns
        date_fields = []
        for field in data[0].keys() if data else []:
            if any(date_word in field.lower() for date_word in ['date', 'time', 'created', 'updated', 'published']):
                date_fields.append(field)
        
        if date_fields:
            patterns["date_fields"] = date_fields
        
        # Value length patterns
        field_lengths = {}
        for obj in data:
            for field, value in obj.items():
                if isinstance(value, str):
                    if field not in field_lengths:
                        field_lengths[field] = []
                    field_lengths[field].append(len(value))
        
        # Calculate average lengths for string fields
        avg_lengths = {}
        for field, lengths in field_lengths.items():
            if lengths:
                avg_lengths[field] = {
                    "avg_length": round(sum(lengths) / len(lengths), 2),
                    "min_length": min(lengths),
                    "max_length": max(lengths)
                }
        
        if avg_lengths:
            patterns["field_lengths"] = avg_lengths
        
        return patterns
    
    def _identify_gaps(self, data: List[Dict[str, Any]], field_completeness: Dict[str, Dict[str, Any]], focus_areas: List[str]) -> List[str]:
        """Identify gaps in the data."""
        gaps = []
        
        if not data:
            return ["No data available"]
        
        # Check for low completeness fields
        for field, stats in field_completeness.items():
            if stats["non_empty_percentage"] < 50:
                gaps.append(f"Field '{field}' is only {stats['non_empty_percentage']}% complete")
        
        # Check for missing focus areas
        if focus_areas:
            all_fields = set()
            for obj in data:
                all_fields.update(obj.keys())
            
            for area in focus_areas:
                if area not in all_fields:
                    gaps.append(f"Focus area '{area}' is completely missing from the data")
        
        # Check for structural inconsistencies
        field_counts = Counter()
        for obj in data:
            field_counts[len(obj.keys())] += 1
        
        if len(field_counts) > 3:  # Many different object structures
            gaps.append(f"Inconsistent object structures: {len(field_counts)} different field count patterns")
        
        # Check for missing common fields
        common_fields = ['id', 'title', 'name', 'url', 'description', 'date', 'source']
        all_fields = set()
        for obj in data:
            all_fields.update(obj.keys())
        
        missing_common = [field for field in common_fields if field not in all_fields]
        if missing_common:
            gaps.append(f"Missing common fields: {', '.join(missing_common)}")
        
        return gaps
    
    def _generate_recommendations(self, data: List[Dict[str, Any]], field_completeness: Dict[str, Dict[str, Any]], 
                                quality_issues: List[str], gaps: List[str]) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        if not data:
            return ["Collect data for analysis"]
        
        # Recommendations based on completeness
        low_completeness_fields = [
            field for field, stats in field_completeness.items() 
            if stats["non_empty_percentage"] < 70
        ]
        
        if low_completeness_fields:
            recommendations.append(f"Improve data collection for fields: {', '.join(low_completeness_fields[:5])}")
        
        # Recommendations based on quality issues
        if "duplicate" in ' '.join(quality_issues).lower():
            recommendations.append("Implement deduplication process to remove duplicate objects")
        
        if "inconsistent types" in ' '.join(quality_issues).lower():
            recommendations.append("Standardize data types across fields to ensure consistency")
        
        # Recommendations based on gaps
        if any("missing" in gap.lower() for gap in gaps):
            recommendations.append("Expand data collection to include missing fields and focus areas")
        
        if len(data) < 10:
            recommendations.append("Increase sample size for more reliable analysis")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Data quality appears good - consider expanding analysis scope")
        
        return recommendations[:10]  # Limit to top 10 recommendations