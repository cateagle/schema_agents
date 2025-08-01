"""
Production-ready unified chat component for the Streamlit app.
Clean implementation with buttons rendered outside chat messages.
"""

import streamlit as st
import re
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from enum import Enum


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatButton:
    key: str
    label: str
    icon: str = ""
    help: str = ""
    type: str = "secondary"
    callback: Optional[Callable[[str, Dict], None]] = None


@dataclass
class ChatMessage:
    role: MessageRole
    content: str
    buttons: List[ChatButton] = field(default_factory=list)


@dataclass
class UnifiedChatConfig:
    """Configuration for the unified chat component."""
    chat_key: str
    title: str = ""
    description: str = ""
    placeholder: str = "Type your message..."
    message_cleaner: Optional[Callable[[str], str]] = None
    assistant_buttons: List[ChatButton] = field(default_factory=list)
    max_messages: Optional[int] = None


def clean_llm_message(content: str) -> str:
    """Clean LLM response artifacts."""
    # Remove common artifacts
    content = re.sub(r'<\|endoftext\|>', '', content)
    content = re.sub(r'<\|assistant\|>', '', content)
    content = re.sub(r'<\|user\|>', '', content)
    
    # Remove multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()


class UnifiedChatComponent:
    """Production-ready unified chat component."""
    
    def __init__(self, config: UnifiedChatConfig):
        self.config = config
        
        # Session state keys
        self.messages_key = f"{config.chat_key}_messages"
        self.processing_key = f"{config.chat_key}_processing"
        
        # Initialize session state
        if self.messages_key not in st.session_state:
            st.session_state[self.messages_key] = []
        if self.processing_key not in st.session_state:
            st.session_state[self.processing_key] = False
    
    def add_message(self, role: MessageRole, content: str):
        """Add a message to the chat."""
        # Clean assistant messages
        if role == MessageRole.ASSISTANT and self.config.message_cleaner:
            content = self.config.message_cleaner(content)
        
        # Create message with configured buttons for assistant
        buttons = self.config.assistant_buttons.copy() if role == MessageRole.ASSISTANT else []
        
        message = ChatMessage(role=role, content=content, buttons=buttons)
        st.session_state[self.messages_key].append(message)
    
    def get_messages(self) -> List[ChatMessage]:
        """Get messages to display."""
        messages = st.session_state[self.messages_key]
        if self.config.max_messages and len(messages) > self.config.max_messages:
            return messages[-self.config.max_messages:]
        return messages
    
    def clear_messages(self):
        """Clear all messages."""
        st.session_state[self.messages_key] = []
    
    def is_processing(self) -> bool:
        """Check if currently processing."""
        return st.session_state.get(self.processing_key, False)
    
    def set_processing(self, processing: bool):
        """Set processing state."""
        st.session_state[self.processing_key] = processing
    
    def render_buttons_outside_chat(self):
        """Render action buttons for the last assistant message outside the chat."""
        messages = self.get_messages()
        if not messages:
            return
        
        # Find last assistant message
        last_assistant_msg = None
        last_assistant_index = -1
        for i in reversed(range(len(messages))):
            if messages[i].role == MessageRole.ASSISTANT:
                last_assistant_msg = messages[i]
                last_assistant_index = i
                break
        
        if last_assistant_msg and last_assistant_msg.buttons:
            st.markdown("### Actions")
            cols = st.columns(len(last_assistant_msg.buttons))
            
            for i, (button, col) in enumerate(zip(last_assistant_msg.buttons, cols)):
                with col:
                    btn_key = f"{self.config.chat_key}_action_{last_assistant_index}_{button.key}"
                    btn_label = f"{button.icon} {button.label}" if button.icon else button.label
                    
                    if st.button(
                        btn_label,
                        key=btn_key,
                        help=button.help,
                        type=button.type,
                        use_container_width=True
                    ):
                        if button.callback:
                            button_data = {"message_index": last_assistant_index, "button": button}
                            button.callback(last_assistant_msg.content, button_data)
    
    def render(self, llm_callback: Optional[Callable[[str], str]] = None):
        """Render the complete chat interface."""
        # Title and description
        if self.config.title:
            st.subheader(self.config.title)
        if self.config.description:
            st.markdown(f"*{self.config.description}*")
        
        # Messages
        messages = self.get_messages()
        
        # Show message limit info
        if self.config.max_messages and len(st.session_state[self.messages_key]) > self.config.max_messages:
            st.info(f"Showing last {self.config.max_messages} messages")
        
        # Display messages
        for message in messages:
            with st.chat_message(message.role.value):
                st.markdown(message.content)
        
        # Show thinking indicator
        if self.is_processing():
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    st.write("")
        
        # Render action buttons outside chat
        self.render_buttons_outside_chat()
        
        # Input area
        user_input = st.chat_input(
            placeholder=self.config.placeholder,
            key=f"{self.config.chat_key}_input"
        )
        
        # Handle user input
        if user_input:
            # Add user message immediately
            self.add_message(MessageRole.USER, user_input)
            
            # Start processing if LLM callback provided
            if llm_callback:
                self.set_processing(True)
            
            st.rerun()
        
        # Process LLM response
        if self.is_processing() and llm_callback:
            # Get last user message from ALL messages (not limited)
            all_messages = st.session_state[self.messages_key]
            # Use value comparison instead of enum comparison for session state safety
            user_messages = [m for m in all_messages if m.role.value == MessageRole.USER.value]
            
            if user_messages:
                last_user_msg = user_messages[-1].content
                
                try:
                    # Generate response
                    response = llm_callback(last_user_msg)
                    
                    # Add assistant response
                    self.add_message(MessageRole.ASSISTANT, response)
                    
                    # Stop processing
                    self.set_processing(False)
                    
                except Exception as e:
                    # Error handling
                    self.add_message(MessageRole.ASSISTANT, f"Error: {str(e)}")
                    self.set_processing(False)
                
                st.rerun()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", key=f"{self.config.chat_key}_clear"):
            self.clear_messages()
            st.rerun()


# Factory functions for different chat types
def create_schema_builder_chat(
    chat_key: str = "schema_builder",
    on_export_schema: Optional[Callable[[str, Dict], None]] = None
) -> UnifiedChatComponent:
    """Create a schema builder chat with export button only."""
    
    def default_export(content: str, data: Dict):
        st.toast("📥 Schema export triggered!")
        if on_export_schema:
            on_export_schema(content, data)
    
    config = UnifiedChatConfig(
        chat_key=chat_key,
        title="",
        description="",
        placeholder="Describe the data structure you need...",
        message_cleaner=clean_llm_message,
        assistant_buttons=[
            ChatButton("export", "Export Schema", "📥", "Export schema as JSON", "primary", default_export)
        ]
    )
    
    return UnifiedChatComponent(config)


def create_research_chat(
    chat_key: str = "research_assistant",
    on_start_research: Optional[Callable[[str, Dict], None]] = None
) -> UnifiedChatComponent:
    """Create a research assistant chat with start research button only."""
    
    def default_start_research(content: str, data: Dict):
        st.toast("🔍 Research started!")
        if on_start_research:
            on_start_research(content, data)
    
    config = UnifiedChatConfig(
        chat_key=chat_key,
        title="",
        description="",
        placeholder="Describe what you want to research...",
        message_cleaner=clean_llm_message,
        assistant_buttons=[
            ChatButton("start_research", "Start Research", "🔍", "Execute research plan", "primary", default_start_research)
        ]
    )
    
    return UnifiedChatComponent(config)