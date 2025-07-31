"""
Export functionality for research results.
"""

import json
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime


class ExportService:
    """Service for exporting research results in various formats."""
    
    @staticmethod
    def export_to_json(
        results: List[Dict[str, Any]], 
        metadata: Optional[Dict[str, Any]] = None,
        pretty: bool = True
    ) -> str:
        """Export results to JSON format."""
        export_data = {
            "metadata": metadata or {},
            "export_timestamp": datetime.now().isoformat(),
            "total_results": len(results),
            "results": results
        }
        
        if pretty:
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(export_data, ensure_ascii=False)
    
    @staticmethod
    def export_to_csv(results: List[Dict[str, Any]]) -> str:
        """Export results to CSV format."""
        if not results:
            return "No results to export"
        
        # Get all unique fields from all results
        all_fields = set()
        for result in results:
            all_fields.update(result.keys())
        
        fieldnames = sorted(list(all_fields))
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        
        writer.writeheader()
        for result in results:
            # Handle nested objects by converting to JSON strings
            processed_result = {}
            for key, value in result.items():
                if isinstance(value, (dict, list)):
                    processed_result[key] = json.dumps(value)
                else:
                    processed_result[key] = value
            writer.writerow(processed_result)
        
        return output.getvalue()
    
    @staticmethod
    def export_to_markdown(
        results: List[Dict[str, Any]], 
        title: str = "Research Results",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export results to Markdown format."""
        lines = [f"# {title}", ""]
        
        # Add metadata if provided
        if metadata:
            lines.append("## Research Information")
            for key, value in metadata.items():
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
            lines.append("")
        
        # Add export info
        lines.extend([
            f"**Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Results**: {len(results)}",
            "",
            "## Results",
            ""
        ])
        
        # Add results
        for i, result in enumerate(results, 1):
            lines.append(f"### Result {i}")
            lines.append("")
            
            for key, value in result.items():
                formatted_key = key.replace('_', ' ').title()
                
                if isinstance(value, str) and value.startswith('http'):
                    lines.append(f"- **{formatted_key}**: [{value}]({value})")
                elif isinstance(value, (dict, list)):
                    lines.append(f"- **{formatted_key}**: `{json.dumps(value)}`")
                else:
                    lines.append(f"- **{formatted_key}**: {value}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def create_research_summary_export(
        query: str,
        schema: Dict[str, Any],
        results: List[Dict[str, Any]],
        analysis: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Create comprehensive export in multiple formats."""
        # Prepare metadata
        metadata = {
            "research_query": query,
            "schema_used": schema,
            "total_results": len(results),
        }
        
        if config:
            metadata.update({
                "num_agents": config.get("num_agents"),
                "research_depth": config.get("research_depth"),
                "max_results_per_agent": config.get("max_results_per_agent")
            })
        
        # Create exports
        exports = {
            "json": ExportService.export_to_json(results, metadata),
            "csv": ExportService.export_to_csv(results),
            "markdown": ExportService.export_to_markdown(
                results, 
                f"Research Results: {query}", 
                metadata
            )
        }
        
        # Add analysis to markdown if provided
        if analysis:
            markdown_lines = exports["markdown"].split("\n")
            # Insert analysis after the Results header
            results_index = next(i for i, line in enumerate(markdown_lines) if line == "## Results")
            markdown_lines.insert(results_index, "## Analysis")
            markdown_lines.insert(results_index + 1, "")
            markdown_lines.insert(results_index + 2, analysis)
            markdown_lines.insert(results_index + 3, "")
            exports["markdown"] = "\n".join(markdown_lines)
        
        return exports
    
    @staticmethod
    def get_filename_for_export(query: str, format_type: str) -> str:
        """Generate filename for export."""
        # Sanitize query for filename
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_query = safe_query.replace(' ', '_')[:50]  # Limit length
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"research_{safe_query}_{timestamp}.{format_type}"
    
    @staticmethod
    def calculate_export_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about the export data."""
        if not results:
            return {}
        
        # Field coverage analysis
        field_counts = {}
        all_fields = set()
        
        for result in results:
            all_fields.update(result.keys())
            for field in result.keys():
                field_counts[field] = field_counts.get(field, 0) + 1
        
        # Calculate coverage percentages
        field_coverage = {
            field: (count / len(results)) * 100 
            for field, count in field_counts.items()
        }
        
        # URL/source statistics
        unique_sources = len(set(
            result.get('url', result.get('source', '')) 
            for result in results 
            if result.get('url') or result.get('source')
        ))
        
        return {
            "total_results": len(results),
            "unique_fields": len(all_fields),
            "field_coverage": field_coverage,
            "unique_sources": unique_sources,
            "avg_fields_per_result": sum(len(result) for result in results) / len(results)
        }