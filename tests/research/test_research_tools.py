#!/usr/bin/env python3
"""
Test script for the new research coordination tools.
"""

import json
from agent_system.tools import (
    JSONAnalysisTool, JSONAnalysisConfig, JSONAnalysisInput,
    ResultValidationTool, ResultValidationConfig, ResultValidationInput,
    ResultAggregationTool, ResultAggregationConfig, ResultAggregationInput
)

def test_json_analysis_tool():
    """Test JSON Analysis Tool functionality."""
    print("Testing JSON Analysis Tool...")
    
    # Create test data
    test_data = [
        {"title": "AI Research Paper", "url": "https://example.com/ai", "date": "2024-01-01", "authors": ["Smith", "Jones"]},
        {"title": "Machine Learning Trends", "url": "https://example.com/ml", "authors": ["Brown"]},
        {"title": "Deep Learning Guide", "url": "https://example.com/dl", "date": "2024-02-01", "content": "Comprehensive guide"},
        {"title": "AI Research Paper", "url": "https://example.com/ai", "date": "2024-01-01", "authors": ["Smith", "Jones"]},  # Duplicate
    ]
    
    # Create tool and test
    tool = JSONAnalysisTool(config=JSONAnalysisConfig(include_patterns=True, include_quality_checks=True))
    
    input_data = JSONAnalysisInput(json_data=test_data, focus_areas=["title", "authors"])
    result = tool.call(input_data.dict())
    
    print(f"✓ JSON Analysis completed")
    print(f"  Total objects: {result['total_objects']}")
    print(f"  Field completeness keys: {list(result['field_completeness'].keys())}")
    print(f"  Quality issues found: {len(result['quality_issues'])}")
    print(f"  Patterns detected: {list(result['patterns'].keys())}")
    print(f"  Gaps identified: {len(result['gaps'])}")
    print(f"  Recommendations: {len(result['recommendations'])}")
    
    return True

def test_result_validation_tool():
    """Test Result Validation Tool functionality."""
    print("\nTesting Result Validation Tool...")
    
    # Create test schema
    test_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "url": {"type": "string", "format": "uri"},
            "date": {"type": "string"},
            "score": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["title", "url"]
    }
    
    # Create test data (some valid, some invalid)
    test_data = [
        {"title": "Valid Article", "url": "https://example.com", "date": "2024-01-01", "score": 0.8},  # Valid
        {"title": "Missing URL"},  # Invalid - missing required URL
        {"title": "Bad URL", "url": "not-a-url", "score": "bad-score"},  # Invalid - bad URL and score type
        {"url": "https://example.com/test"},  # Invalid - missing required title
    ]
    
    # Create tool and test
    tool = ResultValidationTool(config=ResultValidationConfig(auto_fix_minor_issues=True))
    
    input_data = ResultValidationInput(json_data=test_data, schema=test_schema)
    result = tool.call(input_data.dict())
    
    print(f"✓ Result Validation completed")
    print(f"  Total objects: {result['total_objects']}")
    print(f"  Valid objects: {result['valid_objects']}")
    print(f"  Invalid objects: {result['invalid_objects']}")
    print(f"  Validation errors: {len(result['validation_errors'])}")
    print(f"  Auto-fixes applied: {len(result['auto_fixed_issues'])}")
    print(f"  Validated data length: {len(result['validated_data'])}")
    
    return True

def test_result_aggregation_tool():
    """Test Result Aggregation Tool functionality."""
    print("\nTesting Result Aggregation Tool...")
    
    # Create test batches from different sources
    batch1 = {
        "source": "academic",
        "results": [
            {"title": "AI Research", "content": "Academic paper about AI", "url": "https://academic.com/ai", "score": 0.9},
            {"title": "ML Trends", "content": "Machine learning analysis", "url": "https://academic.com/ml", "score": 0.7}
        ]
    }
    
    batch2 = {
        "source": "news",
        "results": [
            {"title": "AI Research", "content": "News article about AI research", "url": "https://news.com/ai", "score": 0.6},  # Similar title
            {"title": "Tech Innovation", "content": "Latest tech innovations", "url": "https://news.com/tech", "score": 0.8}
        ]
    }
    
    batch3 = {
        "source": "blog",
        "results": [
            {"title": "AI Research", "content": "Academic paper about AI", "url": "https://academic.com/ai", "score": 0.9},  # Exact duplicate
            {"title": "Future of AI", "content": "Blog post about AI future", "url": "https://blog.com/ai", "score": 0.5}
        ]
    }
    
    # Create tool and test
    tool = ResultAggregationTool(config=ResultAggregationConfig(
        deduplication_method="content_hash",
        merge_similar_results=True,
        prioritize_sources=["academic", "news"]
    ))
    
    input_data = ResultAggregationInput(
        result_batches=[batch1, batch2, batch3],
        aggregation_strategy="merge_and_dedupe",
        ranking_criteria=["relevance", "authority"]
    )
    result = tool.call(input_data.dict())
    
    print(f"✓ Result Aggregation completed")
    print(f"  Total input results: {result['total_input_results']}")
    print(f"  Total output results: {result['total_output_results']}")
    print(f"  Duplicates removed: {result['duplicates_removed']}")
    print(f"  Results merged: {result['results_merged']}")
    print(f"  Source statistics: {result['source_statistics']}")
    
    return True

def test_tool_integration():
    """Test that tools can work together in a pipeline."""
    print("\nTesting Tool Integration Pipeline...")
    
    # Step 1: Create some test research results
    research_results = [
        {"title": "AI Ethics Paper", "url": "https://ethics.com/ai", "content": "Ethics in AI", "relevance": 0.9},
        {"title": "ML Safety Research", "url": "https://safety.com/ml", "content": "Machine learning safety", "relevance": 0.8},
        {"title": "AI Ethics Paper", "url": "https://ethics.com/ai", "content": "Ethics in AI", "relevance": 0.9},  # Duplicate
        {"title": "Bad Data", "url": "not-a-url", "content": "", "relevance": "bad"},  # Bad data
    ]
    
    # Step 2: Analyze the data
    analysis_tool = JSONAnalysisTool()
    analysis_input = JSONAnalysisInput(json_data=research_results, focus_areas=["title", "url"])
    analysis_result = analysis_tool.call(analysis_input.dict())
    
    print(f"  Analysis found {len(analysis_result['quality_issues'])} quality issues")
    
    # Step 3: Validate against a schema
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "url": {"type": "string"},
            "content": {"type": "string"},
            "relevance": {"type": "number"}
        },
        "required": ["title", "url"]
    }
    
    validation_tool = ResultValidationTool(config=ResultValidationConfig(auto_fix_minor_issues=True))
    validation_input = ResultValidationInput(json_data=research_results, schema=schema)
    validation_result = validation_tool.call(validation_input.dict())
    
    print(f"  Validation: {validation_result['valid_objects']}/{validation_result['total_objects']} objects valid")
    
    # Step 4: Aggregate results (treating as if from multiple sources)
    batch = {"source": "research_pipeline", "results": validation_result['validated_data']}
    
    aggregation_tool = ResultAggregationTool()
    aggregation_input = ResultAggregationInput(result_batches=[batch])
    aggregation_result = aggregation_tool.call(aggregation_input.dict())
    
    print(f"  Aggregation: {aggregation_result['total_output_results']} final results after deduplication")
    
    print("✓ Integration pipeline completed successfully!")
    return True

if __name__ == "__main__":
    try:
        print("Testing Research Coordination Tools")
        print("=" * 50)
        
        # Test individual tools
        test_json_analysis_tool()
        test_result_validation_tool()
        test_result_aggregation_tool()
        
        # Test integration
        test_tool_integration()
        
        print("\n" + "="*60)
        print("✅ ALL RESEARCH TOOLS TESTS PASSED!")
        print("Research coordination tools are ready for Step 3.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)