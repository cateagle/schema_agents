"""
Clean, simplified Streamlit application.
Complete separation: Schema Builder | Research Tool
No phases, minimal configuration, maximum usability.
"""

import streamlit as st
import sys
import os
import json

# Add the project root to Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit_app.config.streamlined_config import (
    StreamlinedConfig, 
    CONVERSATION_MODELS, 
    AGENT_MODELS
)
from streamlit_app.components.schema_builder import SchemaBuilder
from streamlit_app.components.research_chat import ResearchChatTool
from streamlit_app.config.models import SchemaSession


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
    
    # Main content: Three simple tabs
    tab1, tab2, tab3 = st.tabs(["📋 Schema", "🔍 Search", "📊 Data"])
    
    # Global schema state
    current_schema = None
    if 'schema_session' in st.session_state and st.session_state.schema_session.current_schema:
        current_schema = st.session_state.schema_session.current_schema
    
    with tab1:
        # Better layout: wide chat, narrow schema editor
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if not config.is_valid:
                st.warning("⚠️ Please configure your API key in the sidebar first.")
            else:
                schema_builder = SchemaBuilder(config.openrouter_api_key)
                schema_builder.render()
        
        with col2:
            st.subheader("Current Schema")
            
            # Use the current schema directly in the text area
            schema_display = ""
            if current_schema:
                schema_display = json.dumps(current_schema, indent=2)
            
            schema_text = st.text_area(
                "Edit or paste JSON schema:",
                value=schema_display,
                height=400,
                help="This shows your current schema. Edit directly or use the AI assistant.",
                key="schema_editor"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💾 Update", type="primary", use_container_width=True):
                    try:
                        schema = json.loads(schema_text) if schema_text.strip() else None
                        if 'schema_session' not in st.session_state:
                            st.session_state.schema_session = SchemaSession()
                        st.session_state.schema_session.current_schema = schema
                        st.success("✅ Schema updated!")
                        st.rerun()
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {str(e)}")
            
            with col_b:
                if st.button("🗑️ Clear", use_container_width=True):
                    if 'schema_session' not in st.session_state:
                        st.session_state.schema_session = SchemaSession()
                    st.session_state.schema_session.current_schema = None
                    st.success("Schema cleared!")
                    st.rerun()
            
            # Show schema info and validation
            if current_schema:
                properties_count = len(current_schema.get('properties', {}))
                schema_title = current_schema.get('title', 'Untitled')
                
                # Basic validation
                is_valid = True
                validation_issues = []
                
                if 'type' not in current_schema:
                    is_valid = False
                    validation_issues.append("Missing 'type'")
                
                if 'properties' not in current_schema:
                    is_valid = False
                    validation_issues.append("Missing 'properties'")
                
                # Display status
                if is_valid:
                    st.success(f"✅ **{schema_title}** • {properties_count} properties • Valid")
                else:
                    issues_text = ", ".join(validation_issues)
                    st.error(f"❌ **{schema_title}** • {properties_count} properties • Issues: {issues_text}")
    
    with tab2:
        if not config.is_valid:
            st.warning("⚠️ Please configure your API key in the sidebar first.")
        elif not current_schema:
            st.warning("⚠️ Please define a schema in the Schema tab first.")
        else:
            # Show current schema info
            st.info(f"Using schema: **{current_schema.get('title', 'Untitled')}** with {len(current_schema.get('properties', {}))} properties")
            
            research_config = {
                'num_agents': config.num_agents,
                'max_results_per_agent': config.max_results_per_agent,
                'agent_timeout': config.agent_timeout,
                'agent_model': config.agent_model,
                'conversation_model': config.conversation_model
            }
            research_chat = ResearchChatTool(config.openrouter_api_key, research_config)
            research_chat.render(available_schema=current_schema)
    
    with tab3:
        if 'research_results' in st.session_state and st.session_state.research_results:
            results = st.session_state.research_results
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                # Copy to clipboard button
                results_json = json.dumps(results, indent=2)
                if st.button("📋 Copy Results", use_container_width=True):
                    # Use JavaScript to copy to clipboard
                    st.components.v1.html(f"""
                    <script>
                    navigator.clipboard.writeText(`{results_json.replace('`', '\\`')}`).then(function() {{
                        console.log('Results copied to clipboard');
                    }});
                    </script>
                    """, height=0)
                    st.toast("📋 Results copied to clipboard!")
            
            with col2:
                # Download button
                st.download_button(
                    label="💾 Download JSON",
                    data=results_json,
                    file_name="research_results.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col3:
                st.success(f"Found {len(results)} results")
            
            # Single JSON block display
            st.json(results)
        else:
            st.info("No research data yet. Run a search first.")


if __name__ == "__main__":
    main()