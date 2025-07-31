"""
Tests for validation utilities.
"""

import pytest
from streamlit_app.utils.validation import (
    validate_json_schema,
    validate_property_definition,
    validate_research_result,
    validate_search_configuration,
    sanitize_filename,
    validate_json_string,
    analyze_schema_complexity
)


class TestValidation:
    """Tests for validation utilities."""
    
    def test_validate_json_schema_valid(self, valid_json_schema):
        """Test validation of valid JSON schema."""
        is_valid, errors = validate_json_schema(valid_json_schema)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_json_schema_invalid_structure(self):
        """Test validation of invalid schema structure."""
        invalid_schema = {"invalid": "schema"}
        
        is_valid, errors = validate_json_schema(invalid_schema)
        
        assert not is_valid
        assert len(errors) > 0
        assert any("type" in error for error in errors)
    
    def test_validate_json_schema_invalid_type(self):
        """Test validation of schema with invalid type."""
        invalid_schema = {
            "type": "invalid_type",
            "properties": {"test": {"type": "string"}}
        }
        
        is_valid, errors = validate_json_schema(invalid_schema)
        
        assert not is_valid
        assert any("object" in error for error in errors)
    
    def test_validate_json_schema_missing_properties(self):
        """Test validation of schema missing properties."""
        invalid_schema = {"type": "object"}
        
        is_valid, errors = validate_json_schema(invalid_schema)
        
        assert not is_valid
        assert any("properties" in error for error in errors)
    
    def test_validate_json_schema_invalid_required(self):
        """Test validation of schema with invalid required field."""
        invalid_schema = {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["nonexistent_field"]
        }
        
        is_valid, errors = validate_json_schema(invalid_schema)
        
        assert not is_valid
        assert any("nonexistent_field" in error for error in errors)
    
    def test_validate_property_definition_valid(self):
        """Test validation of valid property definition."""
        prop_def = {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "description": "A test string property"
        }
        
        errors = validate_property_definition("test_prop", prop_def)
        
        assert len(errors) == 0
    
    def test_validate_property_definition_invalid_type(self):
        """Test validation of property with invalid type."""
        prop_def = {"type": "invalid_type"}
        
        errors = validate_property_definition("test_prop", prop_def)
        
        assert len(errors) > 0
        assert any("invalid_type" in error for error in errors)
    
    def test_validate_property_definition_missing_type(self):
        """Test validation of property missing type."""
        prop_def = {"description": "No type specified"}
        
        errors = validate_property_definition("test_prop", prop_def)
        
        assert len(errors) > 0
        assert any("type" in error for error in errors)
    
    def test_validate_research_result_valid(self, valid_json_schema):
        """Test validation of valid research result."""
        result = {
            "title": "Test Paper",
            "url": "https://example.com",
            "authors": ["Dr. Smith"],
            "abstract": "Test abstract"
        }
        
        is_valid, errors = validate_research_result(result, valid_json_schema)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_research_result_missing_required(self, valid_json_schema):
        """Test validation of result missing required fields."""
        result = {
            "title": "Test Paper"
            # Missing required 'url' field
        }
        
        is_valid, errors = validate_research_result(result, valid_json_schema)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_search_configuration_valid(self):
        """Test validation of valid search configuration."""
        config = {
            "openrouter_api_key": "test-key-123",
            "conversation_model": "anthropic/claude-3.5-sonnet",
            "agent_model": "anthropic/claude-3.5-sonnet",
            "num_agents": 3,
            "max_results_per_agent": 10,
            "agent_timeout": 300
        }
        
        is_valid, errors = validate_search_configuration(config)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_search_configuration_missing_api_key(self):
        """Test validation of config missing API key."""
        config = {
            "num_agents": 3,
            "max_results_per_agent": 10,
            "agent_timeout": 300
        }
        
        is_valid, errors = validate_search_configuration(config)
        
        assert not is_valid
        assert any("API key" in error for error in errors)
    
    def test_validate_search_configuration_invalid_agents(self):
        """Test validation of config with invalid agent count."""
        config = {
            "openrouter_api_key": "test-key",
            "num_agents": 0,  # Invalid
            "max_results_per_agent": 10,
            "agent_timeout": 300
        }
        
        is_valid, errors = validate_search_configuration(config)
        
        assert not is_valid
        assert any("agents" in error for error in errors)
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        unsafe_filename = 'test<file>name:with|invalid*chars?.txt'
        
        safe_filename = sanitize_filename(unsafe_filename)
        
        # Should replace invalid characters with underscores
        assert '<' not in safe_filename
        assert '>' not in safe_filename
        assert ':' not in safe_filename
        assert '|' not in safe_filename
        assert '*' not in safe_filename
        assert '?' not in safe_filename
        
        # Should contain the base name
        assert 'test' in safe_filename
        assert 'file' in safe_filename
    
    def test_sanitize_filename_empty(self):
        """Test sanitization of empty filename."""
        result = sanitize_filename('')
        
        assert result == 'untitled'
    
    def test_sanitize_filename_too_long(self):
        """Test sanitization of very long filename."""
        long_filename = 'a' * 300
        
        result = sanitize_filename(long_filename)
        
        assert len(result) <= 255
    
    def test_validate_json_string_valid(self):
        """Test validation of valid JSON string."""
        json_string = '{"test": "value", "number": 123}'
        
        is_valid, parsed, message = validate_json_string(json_string)
        
        assert is_valid
        assert parsed == {"test": "value", "number": 123}
        assert "Valid" in message
    
    def test_validate_json_string_invalid(self):
        """Test validation of invalid JSON string."""
        json_string = '{"test": "value", "invalid": json}'
        
        is_valid, parsed, message = validate_json_string(json_string)
        
        assert not is_valid
        assert parsed is None
        assert "Invalid JSON" in message
    
    def test_analyze_schema_complexity_simple(self):
        """Test complexity analysis of simple schema."""
        simple_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "url": {"type": "string"}
            },
            "required": ["title"]
        }
        
        analysis = analyze_schema_complexity(simple_schema)
        
        assert analysis["total_properties"] == 2
        assert analysis["required_properties"] == 1
        assert analysis["optional_properties"] == 1
        assert analysis["complexity_score"] == 1.0  # 2 * 0.5
        assert "string" in analysis["property_types"]
        assert analysis["property_types"]["string"] == 2
    
    def test_analyze_schema_complexity_complex(self):
        """Test complexity analysis of complex schema."""
        complex_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "metadata": {"type": "object"},
                "tags": {"type": "array"},
                "score": {"type": "number"},
                "nested": {
                    "type": "object",
                    "properties": {"inner": {"type": "string"}}
                }
            },
            "required": ["title", "metadata", "tags"]
        }
        
        analysis = analyze_schema_complexity(complex_schema)
        
        assert analysis["total_properties"] == 5
        assert analysis["required_properties"] == 3
        assert analysis["optional_properties"] == 2
        assert analysis["nested_objects"] == 2
        assert analysis["array_properties"] == 1
        assert analysis["complexity_score"] > 5  # Higher complexity
        
        # Should have suggestions for complex schema
        assert len(analysis["suggestions"]) > 0
    
    def test_analyze_schema_complexity_invalid_schema(self):
        """Test complexity analysis of invalid schema."""
        invalid_schema = {"type": "string"}  # Not an object schema
        
        analysis = analyze_schema_complexity(invalid_schema)
        
        # Should return default analysis
        assert analysis["total_properties"] == 0
        assert analysis["complexity_score"] == 0