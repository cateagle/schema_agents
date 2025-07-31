"""
Clean, simplified Streamlit application.
Complete separation: Schema Builder | Research Tool
No phases, minimal configuration, maximum usability.
"""

import streamlit as st
import sys
import os

# Add the project root to Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit_app.config.streamlined_config import (
    StreamlinedConfig, 
    CONVERSATION_MODELS, 
    AGENT_MODELS
)
from streamlit_app.components.schema_catalog import SchemaCatalogUI
from streamlit_app.components.schema_builder import SchemaBuilder
from streamlit_app.components.research_chat import ResearchChatTool


def render_sidebar() -> StreamlinedConfig:
    """Render clean, minimal sidebar."""
    # Initialize config in session state
    if 'config' not in st.session_state:
        st.session_state.config = StreamlinedConfig()
    
    config = st.session_state.config
    
    st.sidebar.title("⚙️ Settings")
    
    # API Key
    with st.sidebar.expander("🔑 API Configuration", expanded=not config.is_valid):
        api_key = st.text_input(
            "OpenRouter API Key:",
            value=config.openrouter_api_key,
            type="password",
            help="Get your key at openrouter.ai"
        )
        if api_key != config.openrouter_api_key:
            config.openrouter_api_key = api_key
            st.rerun()
        
        if config.is_valid:
            st.success("✅ API configured")
        else:
            st.error("❌ API key required")
    
    # Models
    with st.sidebar.expander("🤖 Model Selection"):
        conv_model = st.selectbox(
            "Schema Builder Model:",
            CONVERSATION_MODELS,
            index=CONVERSATION_MODELS.index(config.conversation_model) 
            if config.conversation_model in CONVERSATION_MODELS else 0
        )
        
        agent_model = st.selectbox(
            "Research Agent Model:",
            AGENT_MODELS,
            index=AGENT_MODELS.index(config.agent_model)
            if config.agent_model in AGENT_MODELS else 0
        )
        
        if conv_model != config.conversation_model:
            config.conversation_model = conv_model
        if agent_model != config.agent_model:
            config.agent_model = agent_model
    
    # Research Settings
    with st.sidebar.expander("🔍 Research Configuration"):
        num_agents = st.slider("Number of Agents:", 1, 10, config.num_agents)
        max_results = st.slider("Results per Agent:", 1, 50, config.max_results_per_agent)
        timeout = st.slider("Timeout (seconds):", 10, 600, config.agent_timeout)
        
        config.num_agents = num_agents
        config.max_results_per_agent = max_results
        config.agent_timeout = timeout
    
    return config


def main():
    """Main application."""
    # Page setup
    st.set_page_config(
        page_title="AI Research Tool",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for minimal space usage
    st.markdown("""
    <style>
        /* Hide Streamlit's default header */
        .stApp [data-testid="stHeader"] {
            display: none;
        }
        
        /* Remove top padding from main container */
        .block-container {
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        /* Compact tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 1rem;
        }
        
        /* Compact header */
        .main-title {
            margin-bottom: 0.5rem !important;
        }
        .main-caption {
            margin-bottom: 1rem !important;
            margin-top: -0.5rem !important;
        }
        
        /* Chat enhancements */
        .stForm {
            border: none !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            background: white !important;
        }
        
        /* Better form input styling */
        .stTextArea textarea {
            border-radius: 8px !important;
            border: 2px solid #e9ecef !important;
            transition: border-color 0.2s ease !important;
        }
        
        .stTextArea textarea:focus {
            border-color: #007bff !important;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.1) !important;
        }
        
        /* Button styling */
        .stButton button {
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Minimal header
    st.markdown('<h1 class="main-title">🤖 JSON Schema Search Agent</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    config = render_sidebar()
    
    # Main content: Three independent tools
    tab1, tab2, tab3 = st.tabs(["📚 Schema Catalog", "📋 Schema Builder", "🔍 Research Tool"])
    
    # Schema sources
    catalog_schema = None
    builder_schema = None
    
    with tab1:
        # Schema Catalog - always available
        catalog_ui = SchemaCatalogUI()
        catalog_schema = catalog_ui.render()
    
    with tab2:
        if not config.is_valid:
            st.warning("⚠️ Please configure your API key in the sidebar first.")
        else:
            schema_builder = SchemaBuilder(config.openrouter_api_key)
            builder_schema = schema_builder.render()
    
    with tab3:
        if not config.is_valid:
            st.warning("⚠️ Please configure your API key in the sidebar first.")
        else:
            # Get schema from multiple sources
            available_schema = None
            schema_source = "None"
            
            # Priority: 1. Catalog selection, 2. Schema builder, 3. Manual
            if catalog_schema:
                available_schema = catalog_schema
                schema_source = "Schema Catalog"
            elif 'schema_session' in st.session_state and st.session_state.schema_session.current_schema:
                available_schema = st.session_state.schema_session.current_schema
                schema_source = "Schema Builder"
            
            # Show schema source
            if available_schema:
                st.info(f"📋 Using schema from: **{schema_source}**")
            
            # Research tool config
            research_config = {
                'num_agents': config.num_agents,
                'max_results_per_agent': config.max_results_per_agent,
                'agent_timeout': config.agent_timeout,
                'agent_model': config.agent_model,
                'conversation_model': config.conversation_model,
                'research_depth': 'medium'
            }
            
            research_chat = ResearchChatTool(config.openrouter_api_key, research_config)
            research_chat.render(available_schema)


if __name__ == "__main__":
    main()