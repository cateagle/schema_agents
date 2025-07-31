"""
Tests for the SessionManager class.
"""

import pytest
from streamlit_app.core.session_manager import SessionManager
from streamlit_app.config.models import AppPhase, AppConfig, ResearchSession


class TestSessionManager:
    """Tests for SessionManager."""
    
    def test_initialization(self, mock_st_session_state):
        """Test session manager initialization."""
        manager = SessionManager(mock_st_session_state)
        manager.initialize_session()
        
        # Check that all required keys are initialized
        assert "app_config" in mock_st_session_state
        assert "research_session" in mock_st_session_state
        assert "show_schema_modal" in mock_st_session_state
        assert "search_results" in mock_st_session_state
        
        # Check default values
        assert isinstance(mock_st_session_state["app_config"], AppConfig)
        assert isinstance(mock_st_session_state["research_session"], ResearchSession)
        assert mock_st_session_state["show_schema_modal"] is False
    
    def test_get_current_phase(self, mock_st_session_state, sample_research_session):
        """Test getting current phase."""
        mock_st_session_state["research_session"] = sample_research_session
        manager = SessionManager(mock_st_session_state)
        
        phase = manager.get_current_phase()
        assert phase == AppPhase.SETUP
    
    def test_advance_to_phase(self, mock_st_session_state):
        """Test advancing to next phase."""
        manager = SessionManager(mock_st_session_state)
        manager.initialize_session()
        
        manager.advance_to_phase(AppPhase.SCHEMA_BUILDING)
        
        assert mock_st_session_state["research_session"].phase == AppPhase.SCHEMA_BUILDING
    
    def test_update_research_session(self, mock_st_session_state):
        """Test updating research session data."""
        manager = SessionManager(mock_st_session_state)
        manager.initialize_session()
        
        test_schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        manager.update_research_session(schema=test_schema, query="test query")
        
        session = mock_st_session_state["research_session"]
        assert session.schema == test_schema
        assert session.query == "test query"
    
    def test_add_conversation_message(self, mock_st_session_state):
        """Test adding conversation messages."""
        manager = SessionManager(mock_st_session_state)
        manager.initialize_session()
        
        manager.add_conversation_message("user", "Hello")
        manager.add_conversation_message("assistant", "Hi there!")
        
        conversation = mock_st_session_state["research_session"].conversation_history
        assert len(conversation) == 2
        assert conversation[0] == {"role": "user", "content": "Hello"}
        assert conversation[1] == {"role": "assistant", "content": "Hi there!"}
    
    def test_is_ready_for_research(self, mock_st_session_state, sample_app_config):
        """Test research readiness check."""
        mock_st_session_state["app_config"] = sample_app_config
        manager = SessionManager(mock_st_session_state)
        manager.initialize_session()
        
        # Should not be ready without schema
        assert not manager.is_ready_for_research()
        
        # Add valid schema
        valid_schema = {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"]
        }
        manager.update_research_session(schema=valid_schema)
        
        # Should be ready now
        assert manager.is_ready_for_research()
    
    def test_reset_search_results(self, mock_st_session_state):
        """Test resetting search results."""
        manager = SessionManager(mock_st_session_state)
        manager.initialize_session()
        
        # Add some mock results
        mock_st_session_state["search_results"] = [{"test": "result"}]
        mock_st_session_state["research_session"].search_results = [{"test": "result"}]
        
        manager.reset_search_results()
        
        assert mock_st_session_state["search_results"] == []
        assert mock_st_session_state["research_session"].search_results == []
    
    def test_get_session_summary(self, mock_st_session_state, sample_app_config, sample_research_session):
        """Test getting session summary."""
        mock_st_session_state["app_config"] = sample_app_config
        mock_st_session_state["research_session"] = sample_research_session
        
        manager = SessionManager(mock_st_session_state)
        summary = manager.get_session_summary()
        
        assert "phase" in summary
        assert "has_schema" in summary
        assert "conversation_length" in summary
        assert "ready_for_research" in summary
        
        assert summary["phase"] == "setup"
        assert summary["has_schema"] is True
        assert summary["conversation_length"] == 2