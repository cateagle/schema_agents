"""
Standalone Schema Builder component using unified chat.
Complete separation from research functionality.
"""

import streamlit as st
import json
import re
from typing import Optional, Dict, Any

from streamlit_app.core.schema_processor import SchemaProcessor
from streamlit_app.config.models import SchemaSession
from streamlit_app.ui.unified_chat import create_schema_builder_chat
from streamlit_app.ui.base_components import (
    render_schema_editor,
    render_info_box
)


class SchemaBuilder:
    """Standalone schema building component using unified chat."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.processor = SchemaProcessor(api_key) if api_key else None
        
        # Initialize session state for schema builder
        if 'schema_session' not in st.session_state:
            st.session_state.schema_session = SchemaSession()
        
        # Create unified chat component
        self.chat = create_schema_builder_chat(
            chat_key="schema_builder_main",
            on_export_schema=self._handle_export_schema
        )
    
    def _handle_extract_schema(self, content: str, data: Dict):
        """Handle schema extraction from chat message."""
        # Look for JSON schemas in different formats
        patterns = [
            r'```json\s*\n(.*?)\n```',  # Standard JSON blocks
            r'```\s*\n(\{.*?\})\s*\n```',  # JSON in generic code blocks
            r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'  # Inline JSON objects
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                try:
                    schema_text = matches[0].strip()
                    schema = json.loads(schema_text)
                    
                    # Save to session
                    session = st.session_state.schema_session
                    session.current_schema = schema
                    
                    st.success(f"✅ Schema extracted with {len(schema.get('properties', {}))} properties!")
                    st.rerun()
                    return
                except json.JSONDecodeError:
                    continue
        
        st.warning("No valid JSON schema found in the message.")
    
    def _handle_export_schema(self, content: str, data: Dict):
        """Handle schema export."""
        session = st.session_state.schema_session
        if session.current_schema:
            schema_json = json.dumps(session.current_schema, indent=2)
            st.download_button(
                "📥 Download Schema JSON",
                data=schema_json,
                file_name=f"schema_{session.current_schema.get('title', 'untitled')}.json",
                mime="application/json"
            )
        else:
            st.warning("No schema to export. Extract a schema first.")
    
    def _process_user_message(self, message: str) -> str:
        """Process user message through the schema processor."""
        if not self.processor:
            return "Please configure your API key first."
        
        try:
            # Get conversation history from chat
            conversation_history = []
            for msg in self.chat.get_messages():
                conversation_history.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Process through schema processor
            response = self.processor.process_schema_conversation(
                conversation_history, 
                message
            )
            
            # Auto-extract schema from response
            self._auto_extract_schema(response)
            
            return response
            
        except Exception as e:
            return f"Error processing message: {str(e)}"
    
    def _auto_extract_schema(self, content: str):
        """Automatically extract schema from LLM response."""
        # Look for JSON schemas in different formats
        patterns = [
            r'```json\s*\n(.*?)\n```',  # Standard JSON blocks
            r'```\s*\n(\{.*?\})\s*\n```',  # JSON in generic code blocks
            r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'  # Inline JSON objects
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                try:
                    schema_text = matches[0].strip()
                    schema = json.loads(schema_text)
                    
                    # Only extract if it looks like a schema (has type/properties)
                    if 'type' in schema or 'properties' in schema:
                        # Save to session
                        session = st.session_state.schema_session
                        session.current_schema = schema
                        return
                except json.JSONDecodeError:
                    continue
    
    def render(self) -> Optional[Dict[str, Any]]:
        """Render just the chat interface."""
        if not self.processor:
            render_info_box("Please configure your API key in the sidebar first.", "warning")
            return None
        
        # Get current session
        session = st.session_state.schema_session
        
        # Just render the unified chat - no extra columns
        self.chat.render(llm_callback=self._process_user_message)
        
        return session.current_schema
    
    def _render_conversation_interface(self, session: SchemaSession) -> None:
        """Render the conversation interface."""
        st.subheader("💬 Schema Conversation")
        
        # Check if we need to process a new user message
        if session.conversation_history and session.conversation_history[-1]["role"] == "user":
            # Check if this is a new message that needs processing
            if "processing_schema_message" not in st.session_state:
                st.session_state.processing_schema_message = True
                # Process the last message
                self._process_user_message_async(session, session.conversation_history[-1]["content"])
                return
        
        # Display conversation history
        if session.conversation_history:
            with st.container():
                for message in session.conversation_history[-10:]:  # Show last 10 messages
                    render_chat_message(message)
        else:
            render_info_box("Start by describing what kind of data you want to collect.", "info")
        
        # Message input
        with st.form("schema_message_form", clear_on_submit=True):
            user_message = st.text_area(
                "Your message:",
                placeholder="Describe the data structure you need...",
                height=100
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                submit_button = st.form_submit_button("Send Message", use_container_width=True)
            with col2:
                clear_button = st.form_submit_button("Clear Chat", use_container_width=True)
            with col3:
                if st.form_submit_button("Use Template", use_container_width=True):
                    self._show_template_selector(session)
        
        if submit_button and user_message.strip():
            user_msg = user_message.strip()
            
            # Add user message immediately
            session.add_message("user", user_msg)
            
            # Rerun to show user message first
            st.rerun()
        
        if clear_button:
            session.clear_conversation()
            session.current_schema = None
            st.rerun()
    
    def _render_schema_interface(self, session: SchemaSession) -> None:
        """Render the schema editing interface."""
        st.subheader("📋 Current Schema")
        
        if session.current_schema:
            # Schema editor
            templates = self.processor.get_schema_examples() if self.processor else {}
            updated_schema = render_schema_editor(
                session.current_schema,
                templates,
                on_change=lambda schema: setattr(session, 'current_schema', schema)
            )
            
            if updated_schema != session.current_schema:
                session.current_schema = updated_schema
                st.rerun()
            
            # Schema validation
            if self.processor:
                is_valid, errors = self.processor.validate_schema(session.current_schema)
                if is_valid:
                    st.success("✅ Schema is valid!")
                else:
                    st.error("❌ Schema validation errors:")
                    for error in errors:
                        st.write(f"• {error}")
            
            # Export options
            st.subheader("📥 Export Schema")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Copy to Clipboard", use_container_width=True):
                    st.code(json.dumps(session.current_schema, indent=2))
            with col2:
                if st.button("Download JSON", use_container_width=True):
                    st.download_button(
                        "Download",
                        data=json.dumps(session.current_schema, indent=2),
                        file_name="schema.json",
                        mime="application/json"
                    )
        else:
            render_info_box("No schema created yet. Start a conversation to build one.", "info")
    
    def _process_user_message_async(self, session: SchemaSession, message: str) -> None:
        """Process a user message asynchronously with typing indicator."""
        if not self.processor:
            return
        
        # Show loading indicator
        with st.status("🤖 Assistant is thinking...", expanded=False) as status:
            status.update(label="🧠 Processing your schema request...", state="running")
            
            # Get AI response
            response = self.processor.process_schema_conversation(
                session.conversation_history,
                message
            )
            
            status.update(label="✅ Response ready!", state="complete")
        
        # Add AI response
        session.add_message("assistant", response)
        
        # Check if response contains a schema
        extracted_schema = self.processor.extract_schema_from_response(response)
        if extracted_schema:
            session.current_schema = extracted_schema
        
        # Clear processing flag
        if "processing_schema_message" in st.session_state:
            del st.session_state.processing_schema_message
        
        # Trigger rerun to show assistant response
        st.rerun()
    
    def _process_message(self, session: SchemaSession, message: str) -> None:
        """Process a user message (legacy method)."""
        if not self.processor:
            return
        
        # Add user message
        session.add_message("user", message)
        
        # Get AI response
        response = self.processor.process_schema_conversation(
            session.conversation_history,
            message
        )
        
        # Add AI response
        session.add_message("assistant", response)
        
        # Check if response contains a schema
        extracted_schema = self.processor.extract_schema_from_response(response)
        if extracted_schema:
            session.current_schema = extracted_schema
    
    def _show_template_selector(self, session: SchemaSession) -> None:
        """Show template selection modal."""
        if not self.processor:
            return
            
        st.subheader("📝 Schema Templates")
        templates = self.processor.get_schema_examples()
        
        if templates:
            template_name = st.selectbox("Choose a template:", list(templates.keys()))
            if st.button("Use Template"):
                session.current_schema = templates[template_name].copy()
                session.add_message("assistant", f"Applied template: {template_name}")
                st.rerun()