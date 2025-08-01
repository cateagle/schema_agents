"""
Research Chat Tool - Chat interface with research orchestrator agent using unified chat.
"""

import streamlit as st
import json
from typing import Optional, Dict, Any, List

from agent_system.llm_apis import OpenRouterLLMApi
from agent_system.core import Message
from research_coordinator import ResearchCoordinator, ResearchConfig
from streamlit_app.config.models import ResearchSession
from streamlit_app.ui.unified_chat import create_research_chat, MessageRole
from streamlit_app.ui.base_components import render_info_box
from streamlit_app.config.prompts.research_prompts import RESEARCH_COORDINATOR_SYSTEM_PROMPT


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
        
        # Create unified chat component
        self.chat = create_research_chat(
            chat_key="research_main",
            on_start_research=self._handle_start_research
        )
        
        # Initialize research progress tracking
        if 'research_progress' not in st.session_state:
            st.session_state.research_progress = {
                'status': 'idle',  # idle, running, completed, failed
                'start_time': None,
                'timeout': None,
                'current_step': '',
                'agents_completed': 0,
                'total_agents': 0
            }
    
    def _handle_start_research(self, content: str, data: Dict):
        """Handle starting research execution using the original tested approach."""
        # Get available schema from session
        available_schema = None
        if 'schema_session' in st.session_state and st.session_state.schema_session.current_schema:
            available_schema = st.session_state.schema_session.current_schema
            
        if not available_schema:
            st.error("❌ No schema available! Please create a schema first.")
            return

        # Use separate LLM to summarize conversation into search task
        query = self._summarize_conversation_to_search_task()
        if not query:
            st.error("❌ Could not extract search query from conversation.")
            return
        
        # Show the extracted query to the user
        st.info(f"🎯 **Research Query:** {query}")
        
        # Execute research using the original tested method
        self._execute_research_original(available_schema, query)
    
    def _summarize_conversation_to_search_task(self) -> str:
        """Use a separate LLM to summarize the entire conversation into a focused search task."""
        if not self.llm_api:
            return ""
        
        try:
            # Get the conversation messages from the chat
            conversation_messages = self.chat.get_messages()
            
            if not conversation_messages:
                return "Research based on the schema requirements"
            
            # Build conversation text for summarization
            conversation_text = ""
            for msg in conversation_messages:
                role = "User" if msg.role == MessageRole.USER else "Assistant"
                conversation_text += f"{role}: {msg.content}\n\n"
            
            # Get available schema for context
            available_schema = None
            if 'schema_session' in st.session_state and st.session_state.schema_session.current_schema:
                available_schema = st.session_state.schema_session.current_schema
            
            schema_context = ""
            if available_schema:
                schema_context = f"\nSCHEMA CONTEXT:\n{json.dumps(available_schema, indent=2)}\n"
            
            # Create focused system prompt for conversation summarization
            summarization_prompt = f"""You are a Research Query Extractor. Your ONLY job is to analyze a conversation and extract a clear, focused search query for research agents.

CONVERSATION TO ANALYZE:
{conversation_text}
{schema_context}

TASK: Summarize this entire conversation into ONE clear search query that research agents can use to find relevant data. 

REQUIREMENTS:
- Extract the core research intent from the conversation 
- Focus on what data needs to be found, not how to find it
- Be specific about the type of information needed
- Keep it as a single sentence or short phrase
- Do NOT include search strategy or methodology
- Do NOT include agent instructions

EXAMPLE OUTPUT: "Find electric vehicles under €30,000 with range over 400km available in Europe"

YOUR SEARCH QUERY:"""

            # Make the LLM call for summarization
            summarization_messages = [Message(role="system", content=summarization_prompt)]
            response = self.llm_api.chat_completion(summarization_messages)
            
            # Extract and clean the query
            query = response.content.strip()
            
            # Remove common prefixes if they exist
            prefixes_to_remove = [
                "Search query:", "Query:", "Research query:", "Find:", "Search for:", "Research:"
            ]
            for prefix in prefixes_to_remove:
                if query.lower().startswith(prefix.lower()):
                    query = query[len(prefix):].strip()
            
            # Ensure we have a meaningful query
            if len(query) < 10:
                query = "Research based on the conversation requirements"
            
            return query
            
        except Exception as e:
            st.error(f"Error summarizing conversation: {str(e)}")
            return "Research based on the schema requirements"
    
    def _extract_research_query(self, conversation) -> str:
        """Extract research query from chat conversation."""
        # Get user messages from the chat (conversation is list of ChatMessage objects)
        user_messages = [msg.content for msg in conversation if msg.role.value == "user"]
        
        if user_messages:
            # Use the most recent substantial message or combine them
            recent_message = user_messages[-1]
            if len(recent_message) > 20:
                return recent_message
            else:
                return " ".join(user_messages)
        
        return ""
    
    def _execute_research_original(self, schema: Dict[str, Any], query: str) -> None:
        """Execute research using the original battle-tested approach."""
        try:
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
            
            # Set up progress tracking with real status
            import time
            st.session_state.research_progress = {
                'status': 'running',
                'start_time': time.time(),
                'timeout': time.time() + self.config.get('agent_timeout', 300),
                'current_step': 'Initializing research coordination...',
                'agents_completed': 0,
                'total_agents': self.config.get('num_agents', 3)
            }
            
            st.toast("🔍 Research started!")
            
            # Create progress callback for real-time updates
            def update_progress(message: str):
                if 'research_progress' in st.session_state:
                    st.session_state.research_progress['current_step'] = message
                    # Estimate progress based on message content
                    if "agents" in message.lower() and "complete" in message.lower():
                        # Try to extract completed count from message
                        import re
                        numbers = re.findall(r'\d+', message)
                        if len(numbers) >= 2:
                            completed = int(numbers[0])
                            total = int(numbers[1])
                            st.session_state.research_progress['agents_completed'] = completed
                            st.session_state.research_progress['total_agents'] = total
            
            # Execute research with progress tracking
            with st.spinner("Executing multi-agent research..."):
                result = self.research_coordinator.coordinate_research(
                    query=query,
                    schema=schema,
                    progress_callback=update_progress
                )
            
            # Handle results - coordinator returns "status": "completed", not "success"
            if result.get('status') == 'completed':
                new_results = result.get('results', [])
                st.session_state.research_results.extend(new_results)
                
                # Mark as completed
                st.session_state.research_progress['status'] = 'completed'
                st.session_state.research_progress['agents_completed'] = st.session_state.research_progress['total_agents']
                
                st.success(f"✅ Research completed! Found {len(new_results)} new results.")
                st.rerun()
            else:
                st.session_state.research_progress['status'] = 'failed'
                st.error(f"❌ Research failed: Status = {result.get('status', 'Unknown')}")
                
        except Exception as e:
            st.session_state.research_progress['status'] = 'failed'
            st.error(f"❌ Research execution failed: {str(e)}")
        
    def _process_research_message(self, message: str) -> str:
        """Process user message through research orchestrator LLM."""
        if not self.llm_api:
            return "Please configure your API key first."
        
        try:
            # Get available schema from session
            available_schema = None
            if 'schema_session' in st.session_state and st.session_state.schema_session.current_schema:
                available_schema = st.session_state.schema_session.current_schema
            
            # Create system prompt for research orchestrator
            system_prompt = self._get_research_orchestrator_prompt(available_schema)
            conversation_history = [Message(role="system", content=system_prompt)]
            
            # Add conversation history from chat
            for msg in self.chat.get_messages():
                conversation_history.append(Message(
                    role=msg.role.value,
                    content=msg.content
                ))
            
            # Add current message
            conversation_history.append(Message(role="user", content=message))
            
            # Get response from research orchestrator
            response = self.llm_api.chat_completion(conversation_history)
            return response.content.strip()
            
        except Exception as e:
            return f"Error processing message: {str(e)}"
    
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
- When ready, the user will click "Start Research" to execute the plan
- Be specific about search strategies and expected data structure
- Reference the available schema when planning research
- Help the user understand what data will be collected and how

Be helpful, direct, and focused on research planning and analysis."""
    
    def render(self, available_schema: Optional[Dict[str, Any]] = None) -> None:
        """Render the research chat interface."""
        if not self.llm_api:
            render_info_box("Please configure your API key in the sidebar first.", "warning")
            return
        
        # Render the unified chat
        self.chat.render(llm_callback=self._process_research_message)
        
        # Show research progress below chat
        self._render_research_progress()
    
    def _render_research_progress(self):
        """Display research progress and status."""
        progress = st.session_state.research_progress
        
        if progress['status'] == 'running':
            import time
            current_time = time.time()
            elapsed = current_time - progress['start_time']
            remaining = progress['timeout'] - current_time
            
            # Progress header
            st.markdown("### 🔍 Research in Progress")
            
            # Progress bar
            if progress['total_agents'] > 0:
                progress_pct = progress['agents_completed'] / progress['total_agents']
                st.progress(progress_pct)
                st.write(f"**Agents:** {progress['agents_completed']}/{progress['total_agents']} completed")
            
            # Status and timing
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", progress['current_step'])
            with col2:
                st.metric("Elapsed", f"{elapsed:.0f}s")
            with col3:
                if remaining > 0:
                    st.metric("Timeout in", f"{remaining:.0f}s")
                else:
                    st.error("⏰ Research timed out!")
                    progress['status'] = 'failed'
            
            st.markdown("---")
            
        elif progress['status'] == 'completed':
            st.success("✅ Research completed successfully!")
            if st.button("🔄 Start New Research"):
                st.session_state.research_progress['status'] = 'idle'
                st.rerun()
            st.markdown("---")
            
        elif progress['status'] == 'failed':
            st.error("❌ Research failed or timed out!")
            if st.button("🔄 Try Again"):
                st.session_state.research_progress['status'] = 'idle'
                st.rerun()
            st.markdown("---")
    
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