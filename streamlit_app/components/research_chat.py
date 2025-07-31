"""
Research Chat Tool - Chat interface with research orchestrator agent.
"""

import streamlit as st
import json
from typing import Optional, Dict, Any, List

from agent_system.llm_apis import OpenRouterLLMApi
from agent_system.core import Message
from research_coordinator import ResearchCoordinator, ResearchConfig
from streamlit_app.config.models import ResearchSession
from streamlit_app.ui.base_components import (
    render_chat_message,
    render_action_buttons,
    render_info_box,
    render_typing_indicator
)


class ResearchChatTool:
    """Research tool with chat interface for the research orchestrator agent."""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        self.api_key = api_key
        self.config = config
        
        # Initialize LLM API for chat
        self.llm_api = OpenRouterLLMApi({
            "api_key": api_key,
            "model": config.get('conversation_model', 'anthropic/claude-3.5-sonnet'),
            "temperature": 0.7
        }) if api_key else None
        
        # Initialize research coordinator (for actual research execution)
        self.research_coordinator = None
        
        # Initialize session state for research chat
        if 'research_chat_session' not in st.session_state:
            st.session_state.research_chat_session = ResearchSession()
        if 'research_results' not in st.session_state:
            st.session_state.research_results = []
        if 'research_conversation' not in st.session_state:
            st.session_state.research_conversation = []
    
    def render(self, available_schema: Optional[Dict[str, Any]] = None) -> None:
        """Render the research chat interface."""
        st.header("🔍 Research Tool")
        st.markdown("Chat with the research orchestrator to plan and execute research.")
        
        if not self.llm_api:
            render_info_box("Please configure your API key in the sidebar first.", "warning")
            return
        
        # Show schema info
        schema_info = self._render_schema_info(available_schema)
        
        # Chat interface
        self._render_chat_interface(available_schema)
        
        st.markdown("---")
        
        # Research execution section
        self._render_research_execution(available_schema)
        
        st.markdown("---")
        
        # Results section
        self._render_results_section()
    
    def _render_schema_info(self, schema: Optional[Dict[str, Any]]) -> str:
        """Show current schema status."""
        if schema:
            st.success("📋 **Schema Available** - Ready for research")
            with st.expander("View Schema"):
                st.json(schema)
            return "schema_available"
        else:
            st.warning("⚠️ **No Schema** - Create one in Schema Builder or Schema Catalog first")
            return "no_schema"
    
    def _render_chat_interface(self, schema: Optional[Dict[str, Any]]) -> None:
        """Render the chat interface with research orchestrator."""
        st.subheader("💬 Research Planning Chat")
        
        conversation = st.session_state.research_conversation
        
        # Check if we need to process a new user message
        if conversation and conversation[-1]["role"] == "user":
            # Check if this is a new message that needs processing
            if "processing_message" not in st.session_state:
                st.session_state.processing_message = True
                # Show typing indicator and process the last message
                self._show_typing_and_process(conversation[-1]["content"], schema)
                return
        
        # Display conversation history with auto-scroll
        if conversation:
            # Create a container for chat messages
            chat_container = st.container()
            with chat_container:
                for message in conversation:
                    render_chat_message(message)
                
                # Add some space at the bottom for better UX
                st.write("")
        else:
            render_info_box("Start by describing what research you want to conduct.", "info")
        
        # Chat input
        with st.form("research_chat_form", clear_on_submit=True):
            user_message = st.text_area(
                "Your message:",
                placeholder="Describe your research requirements, refine the search strategy, or ask questions about the results...",
                height=100
            )
            
            col1, col2 = st.columns([3, 1])
            with col1:
                submit_button = st.form_submit_button("Send Message", use_container_width=True)
            with col2:
                clear_button = st.form_submit_button("Clear Chat", use_container_width=True)
        
        if submit_button and user_message.strip():
            user_msg = user_message.strip()
            
            # Add user message to conversation immediately
            st.session_state.research_conversation.append({
                "role": "user", 
                "content": user_msg
            })
            
            # Rerun to show user message first
            st.rerun()
        
        if clear_button:
            st.session_state.research_conversation = []
            st.rerun()
    
    def _show_typing_and_process(self, message: str, schema: Optional[Dict[str, Any]]) -> None:
        """Show typing indicator and process the message."""
        # Create a placeholder for the typing indicator
        typing_placeholder = st.empty()
        
        # Show typing indicator
        with typing_placeholder.container():
            render_typing_indicator()
        
        # Process the message
        if self.llm_api:
            try:
                # Create conversation for research orchestrator
                system_prompt = self._get_research_orchestrator_prompt(schema)
                conversation = [Message(role="system", content=system_prompt)]
                
                # Add conversation history (including the user message we just added)
                for msg in st.session_state.research_conversation:
                    conversation.append(Message(role=msg["role"], content=msg["content"]))
                
                # Get response from research orchestrator
                response = self.llm_api.chat_completion(conversation)
                
                # Clear typing indicator
                typing_placeholder.empty()
                
                # Add assistant response
                st.session_state.research_conversation.append({
                    "role": "assistant",
                    "content": response.content.strip()
                })
                
                # Clear processing flag
                if "processing_message" in st.session_state:
                    del st.session_state.processing_message
                
                # Trigger rerun to show assistant response
                st.rerun()
                
            except Exception as e:
                typing_placeholder.empty()
                # Clear processing flag on error too
                if "processing_message" in st.session_state:
                    del st.session_state.processing_message
                st.error(f"Error processing message: {str(e)}")
    
    def _process_chat_message_async(self, message: str, schema: Optional[Dict[str, Any]]) -> None:
        """Process a chat message with the research orchestrator asynchronously."""
        if not self.llm_api:
            return
        
        # Show loading indicator
        with st.status("🤖 Assistant is thinking...", expanded=False) as status:
            # Create conversation for research orchestrator
            system_prompt = self._get_research_orchestrator_prompt(schema)
            conversation = [Message(role="system", content=system_prompt)]
            
            # Add conversation history (including the user message we just added)
            for msg in st.session_state.research_conversation:
                conversation.append(Message(role=msg["role"], content=msg["content"]))
            
            status.update(label="🧠 Processing your message...", state="running")
            
            # Get response from research orchestrator
            response = self.llm_api.chat_completion(conversation)
            
            status.update(label="✅ Response ready!", state="complete")
        
        # Add assistant response
        st.session_state.research_conversation.append({
            "role": "assistant",
            "content": response.content.strip()
        })
        
        # Trigger rerun to show assistant response
        st.rerun()
    
    def _process_chat_message(self, message: str, schema: Optional[Dict[str, Any]]) -> None:
        """Process a chat message with the research orchestrator (legacy method)."""
        if not self.llm_api:
            return
        
        # Add user message
        st.session_state.research_conversation.append({
            "role": "user", 
            "content": message
        })
        
        # Create conversation for research orchestrator
        system_prompt = self._get_research_orchestrator_prompt(schema)
        conversation = [Message(role="system", content=system_prompt)]
        
        # Add conversation history
        for msg in st.session_state.research_conversation[:-1]:  # Exclude the last message we just added
            conversation.append(Message(role=msg["role"], content=msg["content"]))
        
        # Add current user message
        conversation.append(Message(role="user", content=message))
        
        # Get response from research orchestrator
        response = self.llm_api.chat_completion(conversation)
        
        # Add assistant response
        st.session_state.research_conversation.append({
            "role": "assistant",
            "content": response.content.strip()
        })
    
    def _get_research_orchestrator_prompt(self, schema: Optional[Dict[str, Any]]) -> str:
        """Get the system prompt for research orchestrator chat."""
        schema_info = ""
        if schema:
            schema_info = f"""
AVAILABLE SCHEMA:
{json.dumps(schema, indent=2)}

This schema defines the structure of data you should help the user research."""
        
        results_info = ""
        if st.session_state.research_results:
            results_count = len(st.session_state.research_results)
            results_info = f"""
PREVIOUS RESULTS:
You have {results_count} research results available from previous searches that you can reference and analyze."""
        
        return f"""You are a Research Orchestrator Agent. You help users plan, execute, and analyze research using multiple specialized agents.

{schema_info}

{results_info}

Your role is to:
1. **Planning**: Help users refine their research requirements and search strategy
2. **Preparation**: Explain what research will be conducted when they click "Start Research"
3. **Analysis**: If results are available, help analyze and interpret the findings
4. **Iteration**: Suggest improvements to research strategy based on results

**Important Guidelines:**
- You are in CHAT MODE - you don't execute research directly
- Research is triggered only when the user clicks "Start Research" button
- If no schema is available, guide them to create one first
- Be conversational and helpful in planning the research approach
- If results exist, offer to analyze them or suggest refinements

**Current Research Config:**
- Number of agents: {self.config.get('num_agents', 3)}
- Results per agent: {self.config.get('max_results_per_agent', 10)}
- Agent timeout: {self.config.get('agent_timeout', 300)}s
- Research model: {self.config.get('agent_model', 'anthropic/claude-3.5-sonnet')}

Start by asking what they want to research or help them understand the research process."""
    
    def _render_research_execution(self, schema: Optional[Dict[str, Any]]) -> None:
        """Render research execution controls."""
        st.subheader("🚀 Execute Research")
        
        if not schema:
            st.error("❌ Cannot start research without a schema. Please create one in Schema Builder or Schema Catalog.")
            return
        
        conversation = st.session_state.research_conversation
        if not conversation:
            st.warning("💬 Start a conversation first to plan your research strategy.")
            return
        
        # Research summary
        st.info("📋 **Ready to Research** - Click below to execute multi-agent research based on your conversation and schema.")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🔍 Start Research", use_container_width=True, type="primary"):
                self._execute_research(schema, conversation)
        
        with col2:
            if st.button("🔄 Clear Results", use_container_width=True):
                st.session_state.research_results = []
                st.rerun()
        
        with col3:
            if st.button("📊 Analyze Results", 
                        disabled=len(st.session_state.research_results) == 0,
                        use_container_width=True):
                self._trigger_results_analysis()
    
    def _execute_research(self, schema: Dict[str, Any], conversation: List[Dict[str, str]]) -> None:
        """Execute research using the research coordinator."""
        try:
            # Extract research query from conversation
            query = self._extract_research_query(conversation)
            
            # Create research coordinator if not exists
            if not self.research_coordinator:
                research_config = ResearchConfig(
                    max_agents=self.config.get('num_agents', 3),
                    agent_timeout=self.config.get('agent_timeout', 300),
                    max_results_per_agent=self.config.get('max_results_per_agent', 10),
                    research_depth='medium',
                    enable_validation=True,
                    enable_aggregation=True
                )
                
                agent_llm_api = OpenRouterLLMApi({
                    "api_key": self.api_key,
                    "model": self.config.get('agent_model', 'anthropic/claude-3.5-sonnet'),
                    "temperature": 0.3
                })
                
                self.research_coordinator = ResearchCoordinator(
                    llm_api=agent_llm_api,
                    research_config=research_config
                )
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(message: str):
                status_text.text(f"🔄 {message}")
            
            # Execute research
            with st.spinner("Executing multi-agent research..."):
                result = self.research_coordinator.coordinate_research(
                    query=query,
                    schema=schema,
                    progress_callback=progress_callback
                )
            
            progress_bar.progress(100)
            status_text.empty()
            
            # Handle results
            if result.get('success', True):
                new_results = result.get('results', [])
                # Append to existing results
                st.session_state.research_results.extend(new_results)
                
                st.success(f"✅ Research completed! Found {len(new_results)} new results. Total: {len(st.session_state.research_results)}")
                
                # Add system message about research completion
                st.session_state.research_conversation.append({
                    "role": "assistant",
                    "content": f"Research completed! I found {len(new_results)} new results that match your criteria. The results are now available for analysis. You can ask me questions about the findings or request specific analysis."
                })
                
                st.rerun()
            else:
                error_msg = result.get('error', 'Unknown error occurred')
                st.error(f"❌ Research failed: {error_msg}")
                
        except Exception as e:
            st.error(f"❌ Research execution failed: {str(e)}")
    
    def _extract_research_query(self, conversation: List[Dict[str, str]]) -> str:
        """Extract research query from conversation."""
        # Simple extraction - get user messages
        user_messages = [msg["content"] for msg in conversation if msg["role"] == "user"]
        
        if user_messages:
            # Use the most recent substantial message or combine them
            recent_message = user_messages[-1]
            if len(recent_message) > 20:
                return recent_message
            else:
                return " ".join(user_messages)
        
        return "research query"
    
    def _trigger_results_analysis(self) -> None:
        """Add a system message to trigger results analysis."""
        results_count = len(st.session_state.research_results)
        analysis_request = f"Please analyze the {results_count} research results I have. What insights can you provide?"
        self._process_chat_message(analysis_request, None)
        st.rerun()
    
    def _render_results_section(self) -> None:
        """Render results display section."""
        results = st.session_state.research_results
        
        if not results:
            render_info_box("No research results yet. Start a conversation and execute research to see results here.", "info")
            return
        
        st.subheader(f"📋 Research Results ({len(results)} found)")
        
        # Results display with tabs
        tab1, tab2, tab3 = st.tabs(["📊 Summary", "🔍 Raw Data", "📥 Export"])
        
        with tab1:
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Results", len(results))
            with col2:
                unique_sources = len(set(r.get('sourceUrl', '') for r in results))
                st.metric("Unique Sources", unique_sources)
            with col3:
                if results and 'price' in results[0]:
                    prices = [r.get('price', 0) for r in results if r.get('price')]
                    if prices:
                        avg_price = sum(prices) / len(prices)
                        st.metric("Avg Price", f"€{avg_price:.0f}")
            
            # Show sample results
            st.subheader("Sample Results")
            for i, result in enumerate(results[:3]):
                with st.expander(f"Result {i+1}: {result.get('brand', 'Unknown')} {result.get('modelName', 'Unknown')}"):
                    st.json(result)
        
        with tab2:
            st.json(results)
        
        with tab3:
            self._render_export_options(results)
    
    def _render_export_options(self, results: List[Dict[str, Any]]) -> None:
        """Render export options."""
        if not results:
            render_info_box("No results to export.", "info")
            return
        
        st.markdown("### 📥 Export Results")
        
        # Export format selection
        export_format = st.selectbox(
            "Export Format:",
            ["json", "csv"],
            format_func=lambda x: x.upper()
        )
        
        if export_format == "json":
            export_data = json.dumps(results, indent=2)
            filename = "research_results.json"
            mime = "application/json"
        else:  # csv
            import pandas as pd
            df = pd.json_normalize(results)
            export_data = df.to_csv(index=False)
            filename = "research_results.csv"
            mime = "text/csv"
        
        st.download_button(
            f"📥 Download {export_format.upper()}",
            data=export_data,
            file_name=filename,
            mime=mime,
            use_container_width=True
        )