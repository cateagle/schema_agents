"""
Example of how to integrate the new chat factory into existing components.
This shows how to replace the old chat implementations with the new factory.
"""

import streamlit as st
from typing import Optional, Dict, Any
from streamlit_app.ui.chat_factory import ChatFactory, MessageRole
from streamlit_app.core.schema_processor import SchemaProcessor


class SchemaBuilderWithNewChat:
    """Example: Schema Builder using the new chat factory."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.processor = SchemaProcessor(api_key) if api_key else None
        
        # Create chat interface using factory
        self.chat = ChatFactory.create_schema_builder_chat(
            key="schema_builder_v2",
            on_schema_extract=self._handle_schema_extraction
        )
    
    def _handle_schema_extraction(self, schema: Dict[str, Any]):
        """Handle extracted schema."""
        # Save to session state or process further
        st.session_state["extracted_schema"] = schema
        st.success(f"Schema extracted with {len(schema.get('properties', {}))} properties")
    
    def _process_user_message(self, message: str) -> str:
        """Process user message and return AI response."""
        if not self.processor:
            return "Please configure your API key first."
        
        try:
            # Use existing schema processor
            conversation_history = [
                {"role": msg.role.value, "content": msg.content} 
                for msg in self.chat.messages
            ]
            
            response = self.processor.process_schema_conversation(
                conversation_history, 
                message
            )
            
            return response
            
        except Exception as e:
            return f"Error processing message: {str(e)}"
    
    def render(self):
        """Render the schema builder with new chat."""
        st.header("🏗️ Schema Builder (New Version)")
        
        if not self.processor:
            st.warning("⚠️ Please configure your API key in the sidebar first.")
            return
        
        # Render the chat - much simpler than before!
        self.chat.render(process_message=self._process_user_message)
        
        # Show extracted schema if available
        if "extracted_schema" in st.session_state:
            st.markdown("---")
            st.subheader("📋 Extracted Schema")
            st.json(st.session_state.extracted_schema)


class ResearchChatWithNewFactory:
    """Example: Research chat using the new factory."""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        self.api_key = api_key
        self.config = config
        
        # Create research chat
        self.chat = ChatFactory.create_research_chat(
            key="research_v2",
            on_start_research=self._handle_research_start
        )
        
        # Mock LLM for demo (replace with real LLM)
        self.mock_responses = [
            "I understand you want to research {topic}. Let me create a comprehensive research plan.",
            "Based on your requirements, I'll set up multiple agents to search for relevant information.",
            "The research will include data validation and result aggregation. Ready to proceed?"
        ]
        self.response_index = 0
    
    def _handle_research_start(self, research_plan: str):
        """Handle research start trigger."""
        st.info("🚀 Research execution would start here!")
        # In real app: trigger research coordinator
        # self.research_coordinator.start_research(research_plan)
    
    def _process_user_message(self, message: str) -> str:
        """Process user message for research planning."""
        # Mock response (replace with real LLM)
        response = self.mock_responses[self.response_index % len(self.mock_responses)]
        self.response_index += 1
        
        # Extract topic from message
        topic = message.split()[:3]  # First few words as topic
        topic_str = " ".join(topic) if topic else "your request"
        
        return response.format(topic=topic_str)
    
    def render(self):
        """Render research chat interface."""
        st.header("🔍 Research Assistant (New Version)")
        
        # Simple one-liner to render complete chat!
        self.chat.render(process_message=self._process_user_message)


def demo_integration():
    """Demo showing how to use the new chat components."""
    st.set_page_config(
        page_title="Chat Integration Demo",
        page_icon="🔗",
        layout="wide"
    )
    
    st.title("🔗 Chat Factory Integration Demo")
    st.markdown("This shows how to replace existing chat implementations with the new factory.")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        demo_type = st.selectbox(
            "Demo Type",
            ["Schema Builder", "Research Chat", "Both"]
        )
        
        api_key = st.text_input(
            "API Key (optional for demo)",
            type="password",
            value="demo-key"
        )
        
        st.markdown("---")
        st.markdown("### Benefits of New Approach")
        st.markdown("""
        ✅ **Single source of truth** - No more DRY violations
        
        ✅ **Native Streamlit components** - Uses `st.chat_message` and `st.chat_input`
        
        ✅ **Stable styling** - No more layout breaking
        
        ✅ **Clean message flow** - Immediate user display + smooth loading
        
        ✅ **Configurable actions** - Easy to add buttons to messages
        
        ✅ **Built-in cleaning** - LLM response cleaning included
        
        ✅ **Factory pattern** - Easy to create new chat types
        
        ✅ **Session management** - Proper state handling
        """)
    
    # Main content
    if demo_type == "Schema Builder":
        builder = SchemaBuilderWithNewChat(api_key)
        builder.render()
        
    elif demo_type == "Research Chat":
        config = {"num_agents": 3, "timeout": 300}
        research = ResearchChatWithNewFactory(api_key, config)
        research.render()
        
    else:  # Both
        col1, col2 = st.columns(2)
        
        with col1:
            builder = SchemaBuilderWithNewChat(api_key)
            builder.render()
        
        with col2:
            config = {"num_agents": 3, "timeout": 300}
            research = ResearchChatWithNewFactory(api_key, config)
            research.render()
    
    # Show comparison
    st.markdown("---")
    st.subheader("📊 Before vs After Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ❌ Old Approach")
        st.markdown("""
        ```python
        # Lots of custom CSS injection
        chat_css = '''<style>...</style>'''
        st.markdown(chat_css, unsafe_allow_html=True)
        
        # Complex message rendering with HTML
        if role == 'user':
            _, col_content = st.columns([1, 4])
            with col_content:
                st.markdown(f'''
                <div class="chat-bubble user">
                ''', unsafe_allow_html=True)
                st.markdown(content)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Manual state management
        if "processing_message" not in st.session_state:
            st.session_state.processing_message = True
            # Complex async processing...
        
        # Duplicated code across components
        ```
        """)
    
    with col2:
        st.markdown("### ✅ New Approach")
        st.markdown("""
        ```python
        # Simple factory creation
        chat = ChatFactory.create_schema_builder_chat(
            key="my_chat",
            on_schema_extract=handle_schema
        )
        
        # One-liner rendering
        chat.render(process_message=my_llm_callback)
        
        # That's it! The factory handles:
        # - Message display with native components
        # - Action buttons
        # - State management
        # - Loading indicators
        # - Message cleaning
        # - Stable styling
        ```
        """)


if __name__ == "__main__":
    demo_integration()