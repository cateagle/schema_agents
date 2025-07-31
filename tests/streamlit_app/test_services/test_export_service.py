"""
Tests for the ExportService.
"""

import json
import pytest
from streamlit_app.services.export_service import ExportService


class TestExportService:
    """Tests for ExportService."""
    
    def test_export_to_json(self, sample_research_results):
        """Test JSON export functionality."""
        metadata = {"query": "test query", "total_results": 3}
        
        result = ExportService.export_to_json(sample_research_results, metadata, pretty=True)
        
        # Should be valid JSON
        data = json.loads(result)
        
        assert "metadata" in data
        assert "results" in data
        assert "export_timestamp" in data
        assert data["total_results"] == 3
        assert len(data["results"]) == 3
        assert data["metadata"]["query"] == "test query"
    
    def test_export_to_json_no_metadata(self, sample_research_results):
        """Test JSON export without metadata."""
        result = ExportService.export_to_json(sample_research_results, pretty=False)
        
        data = json.loads(result)
        
        assert data["metadata"] == {}
        assert len(data["results"]) == 3
    
    def test_export_to_csv(self, sample_research_results):
        """Test CSV export functionality."""
        result = ExportService.export_to_csv(sample_research_results)
        
        lines = result.strip().split('\n')
        
        # Should have header + 3 data rows
        assert len(lines) == 4
        
        # Check header contains expected fields
        header = lines[0]
        assert "title" in header
        assert "authors" in header
        assert "url" in header
        
        # Check first data row
        first_row = lines[1]
        assert "Advanced AI Techniques" in first_row
    
    def test_export_to_csv_empty_results(self):
        """Test CSV export with empty results."""
        result = ExportService.export_to_csv([])
        
        assert result == "No results to export"
    
    def test_export_to_markdown(self, sample_research_results):
        """Test Markdown export functionality."""
        title = "Test Research Results"
        metadata = {"query": "AI papers", "total_results": 3}
        
        result = ExportService.export_to_markdown(sample_research_results, title, metadata)
        
        # Check title
        assert "# Test Research Results" in result
        
        # Check metadata section
        assert "## Research Information" in result
        assert "Query**: AI papers" in result
        
        # Check results section
        assert "## Results" in result
        assert "### Result 1" in result
        assert "Advanced AI Techniques" in result
        
        # Check that URLs are properly linked
        assert "[https://example.com/paper1](https://example.com/paper1)" in result
    
    def test_create_research_summary_export(self, sample_research_results):
        """Test comprehensive research summary export."""
        query = "AI research papers"
        schema = {"type": "object", "properties": {"title": {"type": "string"}}}
        
        exports = ExportService.create_research_summary_export(
            query, schema, sample_research_results
        )
        
        # Should contain all three formats
        assert "json" in exports
        assert "csv" in exports
        assert "markdown" in exports
        
        # Check JSON export
        json_data = json.loads(exports["json"])
        assert json_data["metadata"]["research_query"] == query
        assert len(json_data["results"]) == 3
        
        # Check CSV export
        csv_lines = exports["csv"].strip().split('\n')
        assert len(csv_lines) == 4  # header + 3 results
        
        # Check Markdown export
        assert f"# Research Results: {query}" in exports["markdown"]
    
    def test_get_filename_for_export(self):
        """Test filename generation."""
        query = "AI research papers & machine learning"
        
        filename = ExportService.get_filename_for_export(query, "json")
        
        # Should sanitize the query
        assert "AI_research_papers" in filename
        assert filename.endswith(".json")
        assert "&" not in filename  # Should be sanitized
    
    def test_calculate_export_stats(self, sample_research_results):
        """Test export statistics calculation."""
        stats = ExportService.calculate_export_stats(sample_research_results)
        
        assert stats["total_results"] == 3
        assert "unique_fields" in stats
        assert "field_coverage" in stats
        assert "unique_sources" in stats
        assert "avg_fields_per_result" in stats
        
        # Check field coverage
        coverage = stats["field_coverage"]
        assert coverage["title"] == 100.0  # All results have title
        assert coverage["url"] == 100.0    # All results have URL
        
        assert stats["unique_sources"] == 3  # All URLs are unique
    
    def test_calculate_export_stats_empty(self):
        """Test export statistics with empty results."""
        stats = ExportService.calculate_export_stats([])
        
        assert stats == {}
    
    def test_export_handles_nested_objects(self):
        """Test that export handles nested objects correctly."""
        results_with_nested = [
            {
                "title": "Test Paper",
                "metadata": {"keywords": ["AI", "ML"], "scores": {"relevance": 8.5}},
                "authors": ["Dr. Smith", "Dr. Jones"]
            }
        ]
        
        # JSON should preserve structure
        json_export = ExportService.export_to_json(results_with_nested)
        data = json.loads(json_export)
        result = data["results"][0]
        assert isinstance(result["metadata"], dict)
        assert isinstance(result["authors"], list)
        
        # CSV should convert nested objects to JSON strings
        csv_export = ExportService.export_to_csv(results_with_nested)
        lines = csv_export.strip().split('\n')
        data_row = lines[1]
        
        # Should contain JSON representations of nested data
        assert '"keywords": ["AI", "ML"]' in data_row or "'keywords': ['AI', 'ML']" in data_row
        
        # Markdown should handle nested objects
        md_export = ExportService.export_to_markdown(results_with_nested)
        assert "metadata" in md_export.lower()
        assert "keywords" in md_export