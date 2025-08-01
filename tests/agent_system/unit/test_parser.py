"""
Tests for the response parser functionality.
"""

import pytest
import json

from agent_system.core import ResponseParser


class TestResponseParser:
    """Test response parser functionality."""
    
    def test_parse_single_tool_call(self):
        """Test parsing a single tool call from response."""
        response = '''
        I need to calculate something for you.
        <TOOL>
        {"tool": "calculator", "input": {"expression": "2 + 2"}}
        </TOOL>
        Let me process that calculation.
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["tool"] == "calculator"
        assert tool_calls[0]["input"]["expression"] == "2 + 2"
    
    def test_parse_multiple_tool_calls(self):
        """Test parsing multiple tool calls from response."""
        response = '''
        I'll need to use several tools for this task.
        
        First, let me calculate:
        <TOOL>{"tool": "calculator", "input": {"expression": "5 * 3"}}</TOOL>
        
        Then I'll search for information:
        <TOOL>{"tool": "web_search", "input": {"query": "machine learning", "max_results": 5}}</TOOL>
        
        Finally, let me do another calculation:
        <TOOL>{"tool": "calculator", "input": {"expression": "sqrt(16)"}}</TOOL>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        
        assert len(tool_calls) == 3
        assert tool_calls[0]["tool"] == "calculator"
        assert tool_calls[0]["input"]["expression"] == "5 * 3"
        assert tool_calls[1]["tool"] == "web_search"
        assert tool_calls[1]["input"]["query"] == "machine learning"
        assert tool_calls[2]["tool"] == "calculator"
        assert tool_calls[2]["input"]["expression"] == "sqrt(16)"
    
    def test_parse_single_result(self):
        """Test parsing a single result from response."""
        response = '''
        Based on my analysis, here are the findings:
        <RESULT>
        {"answer": 42, "explanation": "The ultimate answer to everything", "confidence": 0.95}
        </RESULT>
        This completes my analysis.
        '''
        
        results = ResponseParser.parse_results(response)
        
        assert len(results) == 1
        assert results[0]["answer"] == 42
        assert results[0]["explanation"] == "The ultimate answer to everything"
        assert results[0]["confidence"] == 0.95
    
    def test_parse_multiple_results(self):
        """Test parsing multiple results from response."""
        response = '''
        Here are my findings:
        
        <RESULT>{"category": "math", "result": 15, "method": "calculation"}</RESULT>
        
        And here's additional analysis:  
        <RESULT>{"category": "research", "sources": 5, "summary": "Comprehensive overview"}</RESULT>
        
        Final conclusion:
        <RESULT>{"overall_confidence": 0.9, "recommendations": ["action1", "action2"]}</RESULT>
        '''
        
        results = ResponseParser.parse_results(response)
        
        assert len(results) == 3
        assert results[0]["category"] == "math"
        assert results[1]["category"] == "research"
        assert results[2]["overall_confidence"] == 0.9
        assert results[2]["recommendations"] == ["action1", "action2"]
    
    def test_parse_tools_and_results_mixed(self):
        """Test parsing response with both tool calls and results."""
        response = '''
        I'll solve this step by step.
        
        <TOOL>{"tool": "calculator", "input": {"expression": "10 / 2"}}</TOOL>
        
        The calculation gives us 5.
        
        <RESULT>{"step1": "Division completed", "intermediate_result": 5}</RESULT>
        
        Now let me do the next calculation:
        
        <TOOL>{"tool": "calculator", "input": {"expression": "5 * 3"}}</TOOL>
        
        Perfect! The final result is 15.
        
        <RESULT>{"final_answer": 15, "steps": ["10 / 2 = 5", "5 * 3 = 15"]}</RESULT>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        assert len(tool_calls) == 2
        assert len(results) == 2
        
        assert tool_calls[0]["input"]["expression"] == "10 / 2"
        assert tool_calls[1]["input"]["expression"] == "5 * 3"
        
        assert results[0]["intermediate_result"] == 5
        assert results[1]["final_answer"] == 15
    
    def test_extract_all_method(self):
        """Test the extract_all convenience method."""
        response = '''
        <TOOL>{"tool": "test_tool", "input": {"param": "value"}}</TOOL>
        Processing...
        <RESULT>{"output": "processed_value", "status": "success"}</RESULT>
        '''
        
        tool_calls, results = ResponseParser.extract_all(response)
        
        assert len(tool_calls) == 1
        assert len(results) == 1
        assert tool_calls[0]["tool"] == "test_tool"
        assert results[0]["output"] == "processed_value"
    
    def test_parse_empty_response(self):
        """Test parsing response with no tool calls or results."""
        response = '''
        This is just a regular response with no special formatting.
        I'm providing some general information and guidance.
        No tools needed for this simple explanation.
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        assert len(tool_calls) == 0
        assert len(results) == 0
    
    def test_parse_malformed_json_in_tool(self):
        """Test handling of malformed JSON in tool calls."""
        response = '''
        <TOOL>{"tool": "calculator", "input": {"expression": "2 + 2"}}</TOOL>
        <TOOL>{"tool": "invalid", "input": {missing quotes and brackets}</TOOL>
        <TOOL>{"tool": "web_search", "input": {"query": "valid query", "max_results": 3}}</TOOL>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        
        # Should skip malformed JSON and only return valid ones
        assert len(tool_calls) == 2
        assert tool_calls[0]["tool"] == "calculator"
        assert tool_calls[1]["tool"] == "web_search"
    
    def test_parse_malformed_json_in_result(self):
        """Test handling of malformed JSON in results."""
        response = '''
        <RESULT>{"valid": "result", "number": 123}</RESULT>
        <RESULT>{invalid json with missing quotes}</RESULT>
        <RESULT>{"another_valid": "result", "array": [1, 2, 3]}</RESULT>
        '''
        
        results = ResponseParser.parse_results(response)
        
        # Should skip malformed JSON and only return valid ones
        assert len(results) == 2
        assert results[0]["valid"] == "result"
        assert results[1]["another_valid"] == "result"
    
    def test_parse_nested_json_structures(self):
        """Test parsing complex nested JSON structures."""
        response = '''
        <TOOL>
        {
            "tool": "complex_tool",
            "input": {
                "config": {
                    "precision": 10,
                    "options": ["opt1", "opt2"]
                },
                "data": {
                    "values": [1, 2, 3],
                    "metadata": {"source": "test", "valid": true}
                }
            }
        }
        </TOOL>
        
        <RESULT>
        {
            "analysis": {
                "summary": "Complex analysis completed",
                "details": {
                    "processing_time": 1.5,
                    "accuracy": 0.98,
                    "warnings": []
                }
            },
            "data": {
                "processed_items": 100,
                "results": [
                    {"id": 1, "value": "result1"},
                    {"id": 2, "value": "result2"}
                ]
            }
        }
        </RESULT>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        assert len(tool_calls) == 1
        assert len(results) == 1
        
        # Check nested structure preservation
        tool_call = tool_calls[0]
        assert tool_call["tool"] == "complex_tool"
        assert tool_call["input"]["config"]["precision"] == 10
        assert tool_call["input"]["data"]["values"] == [1, 2, 3]
        assert tool_call["input"]["data"]["metadata"]["valid"] == True
        
        result = results[0]
        assert result["analysis"]["details"]["accuracy"] == 0.98
        assert result["data"]["processed_items"] == 100
        assert len(result["data"]["results"]) == 2
    
    def test_parse_whitespace_handling(self):
        """Test parsing with various whitespace formatting."""
        response = '''
        <TOOL>
        
        {
            "tool": "spaced_tool",
            "input": {
                "param": "value"
            }
        }
        
        </TOOL>
        
        
        <RESULT>
        
        
        {"result": "spaced_result"}
        
        
        </RESULT>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        assert len(tool_calls) == 1
        assert len(results) == 1
        assert tool_calls[0]["tool"] == "spaced_tool"
        assert results[0]["result"] == "spaced_result"
    
    def test_parse_inline_formatting(self):
        """Test parsing with inline tag formatting."""
        response = '''
        I need to <TOOL>{"tool": "inline_tool", "input": {"data": "inline"}}</TOOL> and then <RESULT>{"status": "inline_complete"}</RESULT> finish.
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        assert len(tool_calls) == 1
        assert len(results) == 1
        assert tool_calls[0]["tool"] == "inline_tool"
        assert results[0]["status"] == "inline_complete"
    
    def test_parse_unicode_content(self):
        """Test parsing with unicode characters."""
        response = '''
        <TOOL>{"tool": "unicode_tool", "input": {"text": "Hello 世界! 🌍 Testing unicode: αβγ"}}</TOOL>
        <RESULT>{"message": "Processed unicode: café, naïve, résumé", "emoji": "✅ Success!"}</RESULT>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        assert len(tool_calls) == 1
        assert len(results) == 1
        assert "世界" in tool_calls[0]["input"]["text"]
        assert "🌍" in tool_calls[0]["input"]["text"]
        assert "café" in results[0]["message"]
        assert "✅" in results[0]["emoji"]
    
    def test_parse_case_sensitivity(self):
        """Test that parser is case sensitive for tags."""
        response = '''
        <TOOL>{"tool": "correct_case", "input": {"param": "value"}}</TOOL>
        <tool>{"tool": "wrong_case", "input": {"param": "value"}}</tool>
        <Tool>{"tool": "wrong_case2", "input": {"param": "value"}}</Tool>
        <RESULT>{"correct": "case"}</RESULT>
        <result>{"wrong": "case"}</result>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        # Should only find correctly cased tags
        assert len(tool_calls) == 1
        assert len(results) == 1
        assert tool_calls[0]["tool"] == "correct_case"
        assert results[0]["correct"] == "case"
    
    def test_parse_multiline_json(self):
        """Test parsing JSON that spans multiple lines."""
        response = '''
        <TOOL>
        {
            "tool": "multiline_tool",
            "input": {
                "long_text": "This is a very long text that might span multiple lines and contains various characters and symbols !@#$%^&*()",
                "array": [
                    "item1",
                    "item2", 
                    "item3"
                ],
                "nested": {
                    "deep": {
                        "value": "found"
                    }
                }
            }
        }
        </TOOL>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["tool"] == "multiline_tool"
        assert len(tool_calls[0]["input"]["array"]) == 3
        assert tool_calls[0]["input"]["nested"]["deep"]["value"] == "found"
    
    def test_parse_special_characters_in_strings(self):
        """Test parsing JSON with special characters in strings."""
        response = r'''
        <TOOL>{"tool": "special_chars", "input": {"text": "Contains \"quotes\" and \\backslashes\\ and \nnewlines"}}</TOOL>
        <RESULT>{"output": "Processed: quotes=\"test\", path=C:\\folder\\file.txt"}</RESULT>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        assert len(tool_calls) == 1
        assert len(results) == 1
        assert '"quotes"' in tool_calls[0]["input"]["text"]
        assert '\\backslashes\\' in tool_calls[0]["input"]["text"]


class TestParserEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_parse_very_large_response(self):
        """Test parsing very large responses."""
        # Create a large JSON structure
        large_data = {"items": [f"item_{i}" for i in range(1000)]}
        response = f'<RESULT>{json.dumps(large_data)}</RESULT>'
        
        results = ResponseParser.parse_results(response)
        
        assert len(results) == 1
        assert len(results[0]["items"]) == 1000
        assert results[0]["items"][0] == "item_0"
        assert results[0]["items"][-1] == "item_999"
    
    def test_parse_empty_json_objects(self):
        """Test parsing empty JSON objects."""
        response = '''
        <TOOL>{}</TOOL>
        <RESULT>{}</RESULT>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        # Empty JSON objects should be skipped as they're invalid
        assert len(tool_calls) == 0  # No valid tool calls
        assert len(results) == 1  # Results can be empty objects
        assert results[0] == {}
    
    def test_parse_deeply_nested_structures(self):
        """Test parsing deeply nested JSON structures."""
        nested_structure = {"level1": {"level2": {"level3": {"level4": {"level5": {"value": "deep"}}}}}}
        response = f'<RESULT>{json.dumps(nested_structure)}</RESULT>'
        
        results = ResponseParser.parse_results(response)
        
        assert len(results) == 1
        assert results[0]["level1"]["level2"]["level3"]["level4"]["level5"]["value"] == "deep"
    
    def test_parse_tags_within_json_strings(self):
        """Test that tags within JSON strings are not parsed as separate tags."""
        response = '''
        <TOOL>{"tool": "test", "input": {"message": "This contains <TOOL> and </TOOL> tags as text"}}</TOOL>
        <RESULT>{"content": "Result with <RESULT> tags inside the string"}</RESULT>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        # Should only find the actual tags, not the ones in strings
        assert len(tool_calls) == 1
        assert len(results) == 1
        assert "<TOOL>" in tool_calls[0]["input"]["message"]
        assert "<RESULT>" in results[0]["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])