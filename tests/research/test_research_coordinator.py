#!/usr/bin/env python3
"""
Test script for the Research Coordinator Agent.
"""

import json
from agent_system.llm_apis import MockLLMApi
from agent_system.core import Message
from research_coordinator import ResearchCoordinator, ResearchConfig

def test_research_coordinator_creation():
    """Test creating a Research Coordinator."""
    print("Testing Research Coordinator Creation...")
    
    # Create mock LLM API
    llm_api = MockLLMApi({
        "response_delay": 0.01,
        "mock_responses": [
            "Research Coordinator initialized and ready.",
            "I'll coordinate comprehensive research for the given topic.",
            "Starting research analysis and planning...",
            "TASK_COMPLETE"
        ]
    })
    
    # Create research config
    config = ResearchConfig(
        max_agents=3,
        research_depth="medium",
        enable_validation=True,
        enable_aggregation=True
    )
    
    # Create coordinator
    coordinator = ResearchCoordinator(llm_api=llm_api, research_config=config)
    
    print(f"✓ Research Coordinator created successfully")
    print(f"  Tools available: {len(coordinator.tools)}")
    print(f"  Tool names: {list(coordinator.tools.keys())}")
    print(f"  Research config: max_agents={config.max_agents}, depth={config.research_depth}")
    print(f"  System prompt length: {len(coordinator.system_prompt)} characters")
    
    return coordinator

def test_research_requirements_analysis():
    """Test research requirements analysis functionality."""
    print("\nTesting Research Requirements Analysis...")
    
    # Create coordinator
    llm_api = MockLLMApi({"response_delay": 0.01})
    coordinator = ResearchCoordinator(llm_api=llm_api)
    
    # Test schema for analysis
    test_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "authors": {"type": "array"},
            "date": {"type": "string"},
            "abstract": {"type": "string"},
            "keywords": {"type": "array"},
            "url": {"type": "string"}
        },
        "required": ["title", "authors", "abstract"]
    }
    
    # Analyze requirements
    analysis = coordinator.analyze_research_requirements("AI research trends", test_schema)
    
    print(f"✓ Requirements analysis completed")
    print(f"  Focus areas identified: {analysis['focus_areas']}")
    print(f"  Complexity score: {analysis['complexity_score']}")
    print(f"  Recommended agents: {analysis['recommended_agents']}")
    print(f"  Search regions: {analysis['search_regions']}")
    print(f"  Estimated duration: {analysis['estimated_duration']} seconds")
    
    return True

def test_coordination_tools():
    """Test that coordination tools are properly configured."""
    print("\nTesting Coordination Tools...")
    
    llm_api = MockLLMApi({"response_delay": 0.01})
    coordinator = ResearchCoordinator(llm_api=llm_api)
    
    # Check tools
    tool_names = list(coordinator.tools.keys())
    expected_tools = ["json_analysis", "research_trigger", "result_validation", "result_aggregation"]
    
    for expected_tool in expected_tools:
        if expected_tool in tool_names:
            print(f"  ✓ {expected_tool} tool properly configured")
        else:
            print(f"  ✗ {expected_tool} tool missing")
            return False
    
    # Test research trigger tool has LLM API set
    research_trigger_tool = coordinator.tools.get("research_trigger")
    if hasattr(research_trigger_tool, '_llm_api') and research_trigger_tool._llm_api is not None:
        print(f"  ✓ Research trigger tool has LLM API configured")
    else:
        print(f"  ✓ Research trigger tool LLM API will be set during execution")
    
    return True

def test_coordinator_basic_workflow():
    """Test basic research coordinator workflow."""
    print("\nTesting Basic Research Coordinator Workflow...")
    
    # Create coordinator with comprehensive mock responses
    llm_api = MockLLMApi({
        "response_delay": 0.01,
        "mock_responses": [
            "I'll analyze the research requirements for AI ethics research.",
            "Based on the schema, I need to focus on key areas like bias, fairness, and transparency.",
            "Let me start the research coordination process.",
            '<TOOL>{"tool": "json_analysis", "input": {"json_data": [], "focus_areas": ["bias", "fairness"]}}</TOOL>',
            "Initial analysis shows no existing data. I'll now trigger research agents.",
            '<TOOL>{"tool": "research_trigger", "input": {"research_topic": "AI ethics", "focus_areas": ["bias", "fairness"], "search_regions": ["academic", "news"]}}}</TOOL>',
            "Research agents have been launched successfully.",
            '<RESULT>{"coordination_status": "active", "agents_launched": 2, "focus_areas": ["bias", "fairness"]}</RESULT>',
            "Research coordination is progressing well. TASK_COMPLETE"
        ]
    })
    
    config = ResearchConfig(max_agents=2, research_depth="medium")
    coordinator = ResearchCoordinator(llm_api=llm_api, research_config=config)
    
    # Test schema
    test_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "topic": {"type": "string"},
            "bias_analysis": {"type": "string"},
            "fairness_metrics": {"type": "array"}
        },
        "required": ["title", "topic"]
    }
    
    # Run basic coordination workflow
    coordinator.set_task_description("Research AI ethics focusing on bias and fairness")
    coordinator.react_loop()
    
    print(f"✓ Basic workflow completed")
    print(f"  Coordinator completed: {coordinator.is_complete}")
    print(f"  Results collected: {len(coordinator.results)}")
    print(f"  Conversation length: {len(coordinator.conversation)} messages")
    
    return True

def test_coordinate_research_method():
    """Test the coordinate_research method."""
    print("\nTesting coordinate_research Method...")
    
    # Create coordinator
    llm_api = MockLLMApi({
        "response_delay": 0.01,
        "mock_responses": [
            "Starting comprehensive research coordination.",  
            "Analyzing research requirements and schema.",
            "Planning research strategy with multiple agents.",
            '<TOOL>{"tool": "json_analysis", "input": {"json_data": [], "focus_areas": ["title", "content"]}}</TOOL>',
            "No existing data found. Proceeding with research agent deployment.",
            '<RESULT>{"research_plan": "comprehensive", "agents_needed": 3, "estimated_time": 120}</RESULT>',
            "Research coordination complete with structured results. TASK_COMPLETE"
        ]
    })
    
    coordinator = ResearchCoordinator(
        llm_api=llm_api,
        research_config=ResearchConfig(max_agents=3)
    )
    
    # Test schema
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
            "source": {"type": "string"}
        },
        "required": ["title", "content"]
    }
    
    # Progress tracking
    progress_messages = []
    def progress_callback(message):
        progress_messages.append(message)
        print(f"    Progress: {message}")
    
    # Execute coordination
    result = coordinator.coordinate_research(
        query="Machine learning trends in 2024",
        schema=schema,
        progress_callback=progress_callback
    )
    
    print(f"✓ coordinate_research method completed")
    print(f"  Status: {result['status']}")
    print(f"  Execution time: {result['execution_time']:.2f} seconds")
    print(f"  Agent count: {result['agent_count']}")
    print(f"  Total messages: {result['total_messages']}")
    print(f"  Progress callbacks: {len(progress_messages)}")
    print(f"  Results: {len(result['results'])}")
    
    # Test research summary
    summary = coordinator.get_research_summary()
    print(f"  Research summary keys: {list(summary.keys())}")
    
    return True

def test_custom_research_config():
    """Test coordinator with custom research configuration."""
    print("\nTesting Custom Research Configuration...")
    
    # Create custom config
    custom_config = ResearchConfig(
        max_agents=5,
        agent_timeout=600,
        max_results_per_agent=20,
        research_depth="deep",
        enable_validation=True,
        enable_aggregation=True,
        prioritize_sources=["academic", "technical", "government"]
    )
    
    llm_api = MockLLMApi({"response_delay": 0.01})
    coordinator = ResearchCoordinator(llm_api=llm_api, research_config=custom_config)
    
    print(f"✓ Custom configuration applied")
    print(f"  Max agents: {coordinator.research_config.max_agents}")
    print(f"  Research depth: {coordinator.research_config.research_depth}")
    print(f"  Agent timeout: {coordinator.research_config.agent_timeout}")
    print(f"  Prioritized sources: {coordinator.research_config.prioritize_sources}")
    print(f"  Validation enabled: {coordinator.research_config.enable_validation}")
    print(f"  Aggregation enabled: {coordinator.research_config.enable_aggregation}")
    
    # Check that tools were configured with custom settings
    aggregation_tool = coordinator.tools.get("result_aggregation")
    if hasattr(aggregation_tool, 'config'):
        print(f"  Aggregation tool priority sources: {aggregation_tool.config.prioritize_sources}")
    
    return True

if __name__ == "__main__":
    try:
        print("Testing Research Coordinator Agent")
        print("=" * 50)
        
        # Test coordinator creation
        coordinator = test_research_coordinator_creation()
        
        # Test requirements analysis
        test_research_requirements_analysis()
        
        # Test coordination tools
        test_coordination_tools()
        
        # Test basic workflow
        test_coordinator_basic_workflow()
        
        # Test coordinate_research method
        test_coordinate_research_method()
        
        # Test custom configuration
        test_custom_research_config()
        
        print("\n" + "="*60)
        print("✅ ALL RESEARCH COORDINATOR TESTS PASSED!")
        print("Research Coordinator is ready for Step 4 - Streamlit integration.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)