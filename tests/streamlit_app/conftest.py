"""
Test configuration and fixtures for the Streamlit app tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from streamlit_app.config.models import AppConfig, ResearchSession, AppPhase


@pytest.fixture
def mock_st_session_state():
    """Mock Streamlit session state."""
    return {}


@pytest.fixture
def sample_app_config():
    """Sample app configuration for testing."""
    return AppConfig(
        openrouter_api_key="test-key-123",
        conversation_model="anthropic/claude-3.5-sonnet",
        agent_model="anthropic/claude-3.5-sonnet",
        num_agents=3,
        max_results_per_agent=10,
        agent_timeout=300
    )


@pytest.fixture
def sample_research_session():
    """Sample research session for testing."""
    return ResearchSession(
        phase=AppPhase.SETUP,
        conversation_history=[
            {"role": "user", "content": "I want to research AI papers"},
            {"role": "assistant", "content": "Great! Let me help you build a schema for AI papers."}
        ],
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "authors": {"type": "array"},
                "url": {"type": "string"}
            },
            "required": ["title", "url"]
        },
        query="AI research papers"
    )


@pytest.fixture
def sample_research_results():
    """Sample research results for testing."""
    return [
        {
            "title": "Advanced AI Techniques",
            "authors": ["Dr. Smith", "Dr. Johnson"],
            "url": "https://example.com/paper1",
            "abstract": "This paper discusses advanced AI techniques...",
            "relevance_score": 8.5
        },
        {
            "title": "Machine Learning Fundamentals",
            "authors": ["Prof. Davis"],
            "url": "https://example.com/paper2",
            "abstract": "A comprehensive overview of ML fundamentals...",
            "relevance_score": 7.8
        },
        {
            "title": "Neural Network Architectures",
            "authors": ["Dr. Wilson", "Dr. Brown", "Dr. Lee"],
            "url": "https://example.com/paper3",
            "abstract": "An analysis of various neural network architectures...",
            "relevance_score": 9.1
        }
    ]


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    mock = Mock()
    mock.chat_completion.return_value = "Mocked LLM response"
    mock.simple_completion.return_value = "Mocked simple response"
    mock.validate_api_key.return_value = (True, "API key is valid")
    return mock


@pytest.fixture
def mock_schema_processor():
    """Mock schema processor."""
    mock = Mock()
    mock.process_schema_conversation.return_value = "Let me help you build a schema..."
    mock.validate_schema.return_value = (True, [])
    mock.extract_schema_from_response.return_value = None
    return mock


@pytest.fixture
def mock_research_service():
    """Mock research service."""
    mock = Mock()
    mock.execute_research.return_value = {
        "success": True,
        "results": [],
        "execution_time": 120.5,
        "agent_count": 3
    }
    mock.get_research_status.return_value = {"status": "completed"}
    mock.validate_research_config.return_value = (True, [])
    return mock


@pytest.fixture
def mock_result_processor():
    """Mock result processor."""
    mock = Mock()
    mock.analyze_results.return_value = {
        "analysis": "The results show interesting patterns...",
        "metrics": {
            "field_coverage": {"title": 1.0, "authors": 0.8, "url": 1.0},
            "required_compliance": 1.0,
            "unique_sources": 3
        },
        "quality_score": 8.5
    }
    return mock


@pytest.fixture
def valid_json_schema():
    """Valid JSON schema for testing."""
    return {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the research paper"
            },
            "authors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of authors"
            },
            "url": {
                "type": "string",
                "format": "uri",
                "description": "URL to the paper"
            },
            "abstract": {
                "type": "string",
                "description": "Paper abstract"
            },
            "publication_date": {
                "type": "string",
                "format": "date",
                "description": "Publication date"
            }
        },
        "required": ["title", "url"]
    }


@pytest.fixture
def invalid_json_schema():
    """Invalid JSON schema for testing."""
    return {
        "type": "invalid_type",
        "properties": {
            "title": "not_an_object"
        }
    }


@pytest.fixture
def sample_export_data():
    """Sample data for testing exports."""
    return {
        "query": "AI research papers",
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "url": {"type": "string"}
            }
        },
        "results": [
            {"title": "Test Paper 1", "url": "https://example.com/1"},
            {"title": "Test Paper 2", "url": "https://example.com/2"}
        ],
        "metadata": {
            "execution_time": 45.2,
            "agent_count": 2
        }
    }