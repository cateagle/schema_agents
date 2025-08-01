"""
Production-ready chat component factory for the Streamlit app.
Provides reusable, configurable chat interfaces with consistent styling and behavior.
"""

import streamlit as st
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Protocol
from enum import Enum
from datetime import datetime
import uuid
import re
import json


class MessageRole(Enum):
    """Standard message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ActionButton:
    """Configuration for message action buttons."""
    key: str
    label: str
    icon: str = ""
    help: str = ""
    type: str = "secondary"  # primary, secondary
    callback: Optional[Callable[[Any], None]] = None
    visible_condition: Optional[Callable[[Any], bool]] = None


@dataclass
class ChatMessage:
    """A chat message with metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    actions: List[ActionButton] = field(default_factory=list)
    cleaned_content: Optional[str] = None


class MessageCleanerProtocol(Protocol):
    """Protocol for message cleaning functions."""
    def __call__(self, content: str) -> str: ...


@dataclass
class ChatConfig:
    """Configuration for a chat interface."""
    # Basic settings
    key: str
    title: str
    description: str = ""
    
    # Message handling
    message_cleaner: Optional[MessageCleanerProtocol] = None
    max_messages: Optional[int] = None
    
    # UI settings
    placeholder_text: str = "Type your message..."
    input_height: int = 80
    show_timestamp: bool = False
    enable_markdown: bool = True
    show_thinking_indicator: bool = True
    
    # Action buttons
    assistant_actions: List[ActionButton] = field(default_factory=list)
    
    # Callbacks
    on_message_submit: Optional[Callable[[str], None]] = None
    on_clear: Optional[Callable[[], None]] = None


class DefaultMessageCleaner:
    """Default message cleaning implementation."""
    
    @staticmethod
    def clean(content: str) -> str:
        """Remove common LLM artifacts and clean formatting."""
        # Remove multiple consecutive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove common artifacts
        artifacts = [
            r'<\|endoftext\|>',
            r'<\|assistant\|>',
            r'<\|system\|>',
            r'<\|user\|>',
            r'<\|im_start\|>',
            r'<\|im_end\|>',
            r'^\s*Assistant:\s*',
            r'^\s*Human:\s*',
        ]
        
        for artifact in artifacts:
            content = re.sub(artifact, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up whitespace
        content = content.strip()
        
        return content
    
    @staticmethod
    def format_json_blocks(content: str) -> str:
        """Ensure JSON blocks are properly formatted in markdown."""
        def format_json_match(match):
            json_str = match.group(1)
            try:
                parsed = json.loads(json_str)
                pretty = json.dumps(parsed, indent=2)
                return f"\n```json\n{pretty}\n```\n"
            except:
                return match.group(0)
        
        # Look for JSON-like structures
        json_pattern = r'(?:^|\n)(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})(?:\n|$)'
        content = re.sub(json_pattern, format_json_match, content, flags=re.MULTILINE | re.DOTALL)
        
        return content


class ChatInterface:
    """Reusable chat interface component."""
    
    def __init__(self, config: ChatConfig):
        self.config = config
        
        # Session state keys
        self._messages_key = f"{config.key}_messages"
        self._processing_key = f"{config.key}_processing"
        self._input_key = f"{config.key}_input"
        
        # Initialize session state
        if self._messages_key not in st.session_state:
            st.session_state[self._messages_key] = []
        if self._processing_key not in st.session_state:
            st.session_state[self._processing_key] = False
    
    @property
    def messages(self) -> List[ChatMessage]:
        """Get all messages."""
        return st.session_state[self._messages_key]
    
    @property
    def is_processing(self) -> bool:
        """Check if currently processing a message."""
        return st.session_state[self._processing_key]
    
    @is_processing.setter
    def is_processing(self, value: bool):
        """Set processing state."""
        st.session_state[self._processing_key] = value
    
    def add_message(self, role: MessageRole, content: str, 
                   metadata: Optional[Dict] = None, actions: Optional[List[ActionButton]] = None) -> ChatMessage:
        """Add a message to the chat."""
        # Create message
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {},
            actions=actions or []
        )
        
        # Clean content if assistant message
        if role == MessageRole.ASSISTANT and self.config.message_cleaner:
            message.cleaned_content = self.config.message_cleaner(content)
        
        # Add default actions for assistant messages
        if role == MessageRole.ASSISTANT and not message.actions:
            message.actions = self.config.assistant_actions.copy()
        
        # Add to session state
        st.session_state[self._messages_key].append(message)
        
        return message
    
    def clear_messages(self):
        """Clear all messages."""
        st.session_state[self._messages_key] = []
        if self.config.on_clear:
            self.config.on_clear()
    
    def get_visible_messages(self) -> List[ChatMessage]:
        """Get messages to display (respecting max_messages)."""
        messages = self.messages
        if self.config.max_messages and len(messages) > self.config.max_messages:
            return messages[-self.config.max_messages:]
        return messages
    
    def render_message(self, message: ChatMessage):
        """Render a single message."""
        with st.chat_message(message.role.value):
            # Display content
            content = message.cleaned_content or message.content
            if self.config.enable_markdown:
                st.markdown(content)
            else:
                st.text(content)
            
            # Show timestamp if enabled
            if self.config.show_timestamp:
                st.caption(f"{message.timestamp.strftime('%I:%M %p')}")
            
            # Render action buttons
            if message.actions:
                cols = st.columns(len(message.actions))
                for idx, (action, col) in enumerate(zip(message.actions, cols)):
                    # Check visibility condition
                    if action.visible_condition and not action.visible_condition(message):
                        continue
                    
                    with col:
                        btn_label = f"{action.icon} {action.label}" if action.icon else action.label
                        btn_key = f"{self.config.key}_action_{message.id}_{action.key}"
                        
                        if st.button(
                            btn_label,
                            key=btn_key,
                            help=action.help,
                            type=action.type,
                            use_container_width=True
                        ):
                            if action.callback:
                                action.callback(message)
    
    def render_thinking_indicator(self):
        """Render thinking/loading indicator."""
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                st.empty()  # Placeholder to show spinner
    
    def render_input_area(self):
        """Render the message input area."""
        with st.container():
            col1, col2 = st.columns([6, 1])
            
            with col1:
                # Use regular text input with Enter key submission
                user_input = st.chat_input(
                    placeholder=self.config.placeholder_text,
                    key=f"{self.config.key}_chat_input"
                )
            
            with col2:
                if st.button("Clear", key=f"{self.config.key}_clear_btn", use_container_width=True):
                    self.clear_messages()
                    st.rerun()
            
            return user_input
    
    def render(self, process_message: Optional[Callable[[str], str]] = None):
        """
        Render the complete chat interface.
        
        Args:
            process_message: Optional callback to process user messages and generate responses
        """
        # Display title and description
        if self.config.title:
            st.subheader(self.config.title)
        if self.config.description:
            st.markdown(f"*{self.config.description}*")
        
        # Message display area
        messages_container = st.container()
        
        with messages_container:
            # Show existing messages
            visible_messages = self.get_visible_messages()
            
            # Show truncation notice
            if self.config.max_messages and len(self.messages) > self.config.max_messages:
                st.info(f"Showing last {self.config.max_messages} messages")
            
            # Render each message
            for message in visible_messages:
                self.render_message(message)
            
            # Show thinking indicator if processing
            if self.is_processing and self.config.show_thinking_indicator:
                self.render_thinking_indicator()
        
        # Input area
        user_input = self.render_input_area()
        
        # Handle user input
        if user_input:
            # Add user message
            self.add_message(MessageRole.USER, user_input)
            
            # Call submit callback if provided
            if self.config.on_message_submit:
                self.config.on_message_submit(user_input)
            
            # Process message if callback provided
            if process_message:
                self.is_processing = True
                st.rerun()
        
        # Process pending message
        if self.is_processing and process_message:
            # Get last user message
            user_messages = [m for m in self.messages if m.role == MessageRole.USER]
            if user_messages:
                last_user_msg = user_messages[-1]
                
                # Generate response
                response = process_message(last_user_msg.content)
                
                # Add assistant message
                self.add_message(MessageRole.ASSISTANT, response)
                
                # Clear processing flag
                self.is_processing = False
                
                # Rerun to show response
                st.rerun()


class ChatFactory:
    """Factory for creating pre-configured chat interfaces."""
    
    @staticmethod
    def create_schema_builder_chat(
        key: str = "schema_builder",
        on_schema_extract: Optional[Callable[[Dict], None]] = None
    ) -> ChatInterface:
        """Create a chat interface for schema building."""
        
        def extract_schema_action(message: ChatMessage):
            """Extract schema from message."""
            # Look for JSON in the message
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            matches = re.findall(json_pattern, message.content, re.MULTILINE)
            
            if matches:
                try:
                    schema = json.loads(matches[0])
                    if on_schema_extract:
                        on_schema_extract(schema)
                    st.success("✅ Schema extracted successfully!")
                except json.JSONDecodeError:
                    st.error("Failed to parse JSON schema")
            else:
                st.warning("No JSON schema found in message")
        
        config = ChatConfig(
            key=key,
            title="🏗️ Schema Builder",
            description="Build JSON schemas through natural conversation",
            message_cleaner=DefaultMessageCleaner.clean,
            placeholder_text="Describe the data structure you need...",
            assistant_actions=[
                ActionButton(
                    key="extract",
                    label="Extract Schema",
                    icon="📋",
                    help="Extract JSON schema from this message",
                    callback=extract_schema_action,
                    visible_condition=lambda m: "```json" in m.content
                ),
                ActionButton(
                    key="copy",
                    label="Copy",
                    icon="📄",
                    help="Copy message to clipboard",
                    callback=lambda m: st.toast("Copied to clipboard!", icon="✅")
                )
            ]
        )
        
        return ChatInterface(config)
    
    @staticmethod
    def create_research_chat(
        key: str = "research_chat",
        on_start_research: Optional[Callable[[str], None]] = None
    ) -> ChatInterface:
        """Create a chat interface for research planning."""
        
        def start_research_action(message: ChatMessage):
            """Start research based on plan."""
            if on_start_research:
                on_start_research(message.content)
            st.success("🔍 Research started!")
        
        config = ChatConfig(
            key=key,
            title="🔍 Research Assistant",
            description="Plan and execute research tasks",
            message_cleaner=DefaultMessageCleaner.clean,
            placeholder_text="Describe what you want to research...",
            show_timestamp=True,
            assistant_actions=[
                ActionButton(
                    key="start",
                    label="Start Research",
                    icon="🔍",
                    help="Execute research based on this plan",
                    type="primary",
                    callback=start_research_action
                ),
                ActionButton(
                    key="refine",
                    label="Refine Plan",
                    icon="🔧",
                    help="Refine the research approach",
                    callback=lambda m: st.info("Refining research plan...")
                )
            ]
        )
        
        return ChatInterface(config)
    
    @staticmethod
    def create_analysis_chat(
        key: str = "analysis_chat"
    ) -> ChatInterface:
        """Create a chat interface for data analysis."""
        
        config = ChatConfig(
            key=key,
            title="📊 Analysis Assistant",
            description="Analyze and interpret your data",
            message_cleaner=DefaultMessageCleaner.clean,
            placeholder_text="Ask questions about your data...",
            enable_markdown=True,
            assistant_actions=[
                ActionButton(
                    key="visualize",
                    label="Visualize",
                    icon="📈",
                    help="Create visualization from this analysis",
                    callback=lambda m: st.info("Creating visualization...")
                ),
                ActionButton(
                    key="export",
                    label="Export",
                    icon="📥",
                    help="Export analysis results",
                    callback=lambda m: st.info("Exporting analysis...")
                )
            ]
        )
        
        return ChatInterface(config)