"""
Test to debug and validate DuckDuckGo web search functionality.
This test actually makes real web requests to figure out why the search is failing.
"""

import pytest
from agent_system.tools.web_search_tool import WebSearchTool, WebSearchConfig, WebSearchInput


class TestDuckDuckGoDebug:
    """Debug DuckDuckGo search implementation."""
    
    def test_ddgs_library_basic(self):
        """Test basic ddgs library functionality."""
        from ddgs import DDGS
        
        query = "python programming"
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        
        print(f"\n=== DDGS Library Test ===")
        print(f"Query: {query}")
        print(f"Results found: {len(results)}")
        
        if results:
            print("Sample result structure:")
            sample = results[0]
            for key, value in sample.items():
                print(f"  {key}: {str(value)[:100]}...")
        
        assert len(results) > 0, "Should find at least one result"
        assert all(isinstance(result, dict) for result in results)
        assert all('title' in result and 'href' in result for result in results)
        
    def test_ddgs_library_options(self):
        """Test ddgs library with different options."""
        from ddgs import DDGS
        
        query = "test search"
        
        print(f"\n=== Testing DDGS Options ===")
        
        # Test with different parameters
        with DDGS() as ddgs:
            # Basic search
            basic_results = list(ddgs.text(query, max_results=2))
            print(f"Basic search: {len(basic_results)} results")
            
            # Search with region
            region_results = list(ddgs.text(query, max_results=2, region='us-en'))
            print(f"US region search: {len(region_results)} results")
            
            # Search with safe search
            safe_results = list(ddgs.text(query, max_results=2, safesearch='moderate'))
            print(f"Safe search: {len(safe_results)} results")
        
        assert len(basic_results) > 0, "Basic search should return results"
            
    def test_web_search_tool_direct(self):
        """Test the WebSearchTool directly with DuckDuckGo."""
        print(f"\n=== Testing WebSearchTool ===")
        
        config = WebSearchConfig(search_engine="duckduckgo")
        tool = WebSearchTool(config=config)
        
        input_data = WebSearchInput(query="python tutorial", max_results=3)
        
        try:
            result_dict = tool.call(input_data.model_dump())
            print(f"SUCCESS: Found {len(result_dict['results'])} results")
            
            for i, search_result in enumerate(result_dict['results']):
                print(f"Result {i+1}:")
                print(f"  Title: {search_result['title']}")
                print(f"  URL: {search_result['url']}")
                print(f"  Snippet: {search_result['snippet'][:100]}...")
                
            assert len(result_dict['results']) > 0, "Should find at least one result"
            
        except Exception as e:
            print(f"FAILED: {str(e)}")
            # Re-raise to fail the test
            raise
            


if __name__ == "__main__":
    # Run tests directly for debugging
    test = TestDuckDuckGoDebug()
    
    print("Running DuckDuckGo debug tests...")
    
    try:
        test.test_ddgs_library_basic()
    except Exception as e:
        print(f"DDGS library basic test failed: {e}")
    
    try:
        test.test_ddgs_library_options()
    except Exception as e:
        print(f"DDGS library options test failed: {e}")
    
    try:
        test.test_web_search_tool_direct()
    except Exception as e:
        print(f"Web search tool test failed: {e}")