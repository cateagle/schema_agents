"""
Reusable UI components for the Streamlit application.
"""

import streamlit as st
import json
from typing import List, Dict, Any, Optional, Callable
from streamlit_app.utils.formatting import (
    format_results_for_display, 
    create_results_summary_table,
    format_execution_time,
    format_agent_status
)


def render_action_buttons(
    buttons: List[Dict[str, Any]], 
    columns: int = 4
) -> Optional[str]:
    """
    Render a row of action buttons.
    
    Args:
        buttons: List of button configs with 'label', 'key', 'disabled', 'help' keys
        columns: Number of columns to arrange buttons in
    
    Returns:
        Key of the clicked button, or None
    """
    if not buttons:
        return None
    
    # Create columns
    cols = st.columns(columns)
    clicked_button = None
    
    for i, button_config in enumerate(buttons):
        col_index = i % columns
        with cols[col_index]:
            if st.button(
                button_config.get('label', f'Button {i}'),
                key=button_config.get('key', f'btn_{i}'),
                disabled=button_config.get('disabled', False),
                help=button_config.get('help')
            ):
                clicked_button = button_config.get('key', f'btn_{i}')
    
    return clicked_button


def render_chat_message(message: Dict[str, str], message_type: str = "assistant") -> None:
    """
    Render a single chat message with modern speech bubble styling.
    
    Args:
        message: Message dict with 'role' and 'content' keys
        message_type: Type for styling ('user', 'assistant', 'system')
    """
    role = message.get('role', 'assistant')
    content = message.get('content', '')
    
    # CSS for speech bubbles with enhanced styling
    chat_css = """
    <style>
    .chat-container {
        margin: 15px 0;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        animation: fadeIn 0.3s ease-in-out;
    }
    .chat-container.user {
        flex-direction: row-reverse;
    }
    .chat-content-wrapper {
        display: flex;
        flex-direction: column;
        max-width: 75%;
    }
    .chat-bubble {
        max-width: 75%;
        padding: 14px 18px;
        border-radius: 20px;
        font-size: 14px;
        line-height: 1.5;
        word-wrap: break-word;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    .chat-bubble:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .chat-bubble.user {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        border-bottom-right-radius: 6px;
    }
    .chat-bubble.user::after {
        content: '';
        position: absolute;
        right: -8px;
        bottom: 6px;
        width: 0;
        height: 0;
        border: 8px solid transparent;
        border-left-color: #0056b3;
        border-right: 0;
        border-bottom: 0;
    }
    .chat-bubble.assistant {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        color: #333;
        border: 1px solid #dee2e6;
        border-bottom-left-radius: 6px;
    }
    .chat-bubble.assistant::after {
        content: '';
        position: absolute;
        left: -8px;
        bottom: 6px;
        width: 0;
        height: 0;
        border: 8px solid transparent;
        border-right-color: #e9ecef;
        border-left: 0;
        border-bottom: 0;
    }
    .chat-bubble.system {
        background: linear-gradient(135deg, #28a745, #1e7e34);
        color: white;
        border-radius: 12px;
        font-size: 12px;
        opacity: 0.9;
        text-align: center;
        margin: 0 auto;
        max-width: 90%;
    }
    .chat-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }
    .chat-avatar:hover {
        transform: scale(1.05);
    }
    .chat-avatar.user {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
    }
    .chat-avatar.assistant {
        background: linear-gradient(135deg, #6f42c1, #563d7c);
        color: white;
    }
    .chat-avatar.system {
        background: linear-gradient(135deg, #28a745, #1e7e34);
        color: white;
        font-size: 14px;
    }
    .chat-timestamp {
        font-size: 11px;
        color: #666;
        margin-top: 6px;
        text-align: center;
        opacity: 0.7;
    }
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 15px 0;
        animation: fadeIn 0.3s ease-in-out;
    }
    .typing-dots {
        display: flex;
        gap: 4px;
        padding: 14px 18px;
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border: 1px solid #dee2e6;
        border-radius: 20px;
        border-bottom-left-radius: 6px;
    }
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #6c757d;
        animation: typingDot 1.4s infinite ease-in-out;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes typingDot {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    </style>
    """
    
    # Only inject CSS once
    if 'chat_css_injected' not in st.session_state:
        st.markdown(chat_css, unsafe_allow_html=True)
        st.session_state.chat_css_injected = True
    
    if role == 'user':
        avatar_emoji = "👤"
        bubble_class = "user"
        container_class = "user"
    elif role == 'system':
        avatar_emoji = "🔒"
        bubble_class = "system"  
        container_class = "assistant"
    else:
        avatar_emoji = "🤖"
        bubble_class = "assistant"
        container_class = "assistant"
    
    # Simple approach: use columns for layout, preserve markdown
    if role == 'user':
        # User messages - right aligned
        _, col_content = st.columns([1, 4])
        with col_content:
            # Add avatar and bubble styling with simple HTML + markdown
            st.markdown(f"""
            <div style="display: flex; flex-direction: row-reverse; align-items: flex-start; gap: 10px; margin: 15px 0;">
                <div class="chat-avatar {bubble_class}">{avatar_emoji}</div>
                <div class="chat-bubble {bubble_class}" style="max-width: 100%;">
            """, unsafe_allow_html=True)
            
            # Let Streamlit handle the markdown content
            st.markdown(content)
            
            st.markdown('</div></div>', unsafe_allow_html=True)
    else:
        # Assistant messages - left aligned
        col_content, _ = st.columns([4, 1])
        with col_content:
            st.markdown(f"""
            <div style="display: flex; align-items: flex-start; gap: 10px; margin: 15px 0;">
                <div class="chat-avatar {bubble_class}">{avatar_emoji}</div>
                <div class="chat-bubble {bubble_class}" style="max-width: 100%;">
            """, unsafe_allow_html=True)
            
            # Let Streamlit handle the markdown content
            st.markdown(content)
            
            st.markdown('</div></div>', unsafe_allow_html=True)


def render_typing_indicator() -> None:
    """Render a typing indicator for the assistant."""
    # CSS should already be injected by render_chat_message
    typing_html = """
    <div class="typing-indicator">
        <div class="chat-avatar assistant">
            🤖
        </div>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """
    st.markdown(typing_html, unsafe_allow_html=True)


def render_progress_tracker(
    current_step: int, 
    total_steps: int, 
    step_names: List[str],
    show_percentage: bool = True
) -> None:
    """
    Render progress tracker.
    
    Args:
        current_step: Current step number (1-indexed)
        total_steps: Total number of steps
        step_names: Names of each step
        show_percentage: Whether to show percentage
    """
    if total_steps == 0:
        return
    
    progress_percentage = (current_step - 1) / total_steps
    
    if show_percentage:
        st.progress(progress_percentage, text=f"Step {current_step} of {total_steps} ({progress_percentage:.0%})")
    else:
        st.progress(progress_percentage)
    
    # Show step indicators
    if step_names and len(step_names) >= total_steps:
        cols = st.columns(total_steps)
        for i, (col, step_name) in enumerate(zip(cols, step_names[:total_steps]), 1):
            with col:
                if i < current_step:
                    st.success(f"✅ {step_name}")
                elif i == current_step:
                    st.info(f"🔄 {step_name}")
                else:
                    st.write(f"⏳ {step_name}")


def render_schema_editor(
    current_schema: Dict[str, Any], 
    templates: Dict[str, Dict],
    on_change: Optional[Callable[[Dict], None]] = None
) -> Dict[str, Any]:
    """
    Render schema editor with templates.
    
    Args:
        current_schema: Current schema to edit
        templates: Available schema templates
        on_change: Callback when schema changes
    
    Returns:
        Updated schema
    """
    st.subheader("JSON Schema Editor")
    
    # Template selector
    if templates:
        template_names = ["Current Schema"] + list(templates.keys())
        selected_template = st.selectbox(
            "Choose a template:", 
            template_names,
            help="Select a predefined template or keep your current schema"
        )
        
        if selected_template != "Current Schema" and selected_template in templates:
            current_schema = templates[selected_template].copy()
            if on_change:
                on_change(current_schema)
    
    # Schema editor
    schema_json = json.dumps(current_schema, indent=2)
    edited_schema_json = st.text_area(
        "JSON Schema:",
        value=schema_json,
        height=300,
        help="Edit your JSON schema here. Make sure it's valid JSON."
    )
    
    # Validate and parse
    try:
        edited_schema = json.loads(edited_schema_json)
        
        # Basic validation
        if not isinstance(edited_schema, dict):
            st.error("Schema must be a JSON object")
            return current_schema
        
        if "type" not in edited_schema:
            st.warning("Schema should have a 'type' field")
        
        if "properties" not in edited_schema:
            st.warning("Schema should have a 'properties' field")
        
        return edited_schema
        
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {str(e)}")
        return current_schema


def render_results_display(
    results: List[Dict[str, Any]], 
    display_mode: str = "formatted",
    max_display: int = 10
) -> None:
    """
    Render research results in different display modes.
    
    Args:
        results: List of result dictionaries
        display_mode: Display mode ('formatted', 'table', 'json', 'raw')
        max_display: Maximum number of results to display
    """
    if not results:
        st.info("No results to display")
        return
    
    # Display mode selector
    col1, col2 = st.columns([3, 1])
    with col2:
        display_mode = st.selectbox(
            "Display Mode:",
            ["formatted", "table", "json", "raw"],
            index=0 if display_mode == "formatted" else ["formatted", "table", "json", "raw"].index(display_mode)
        )
    
    with col1:
        st.write(f"**{len(results)} results found**")
    
    # Display results based on mode
    if display_mode == "formatted":
        formatted_text = format_results_for_display(results, max_display)
        st.markdown(formatted_text)
        
    elif display_mode == "table":
        create_results_summary_table(results[:max_display])
        
    elif display_mode == "json":
        display_results = results[:max_display]
        st.json(display_results)
        
    elif display_mode == "raw":
        for i, result in enumerate(results[:max_display], 1):
            with st.expander(f"Result {i}"):
                st.write(result)
    
    # Show pagination info
    if len(results) > max_display:
        st.info(f"Showing {max_display} of {len(results)} results")


def render_config_panel(
    config: Dict[str, Any], 
    available_models: List[str],
    on_update: Optional[Callable[[Dict], None]] = None
) -> Dict[str, Any]:
    """
    Render configuration panel.
    
    Args:
        config: Current configuration
        available_models: Available model options
        on_update: Callback when config updates
    
    Returns:
        Updated configuration
    """
    st.subheader("Configuration")
    
    updated_config = config.copy()
    
    # API Configuration
    st.markdown("**API Settings**")
    api_key = st.text_input(
        "OpenRouter API Key:",
        value=config.get('openrouter_api_key', ''),
        type='password',
        help="Your OpenRouter API key for accessing LLM models"
    )
    updated_config['openrouter_api_key'] = api_key
    
    # Model Configuration
    st.markdown("**Model Settings**")
    col1, col2 = st.columns(2)
    
    with col1:
        conversation_model = st.selectbox(
            "Conversation Model:",
            available_models,
            index=available_models.index(config.get('conversation_model', available_models[0])) 
            if config.get('conversation_model') in available_models else 0
        )
        updated_config['conversation_model'] = conversation_model
    
    with col2:
        agent_model = st.selectbox(
            "Agent Model:",
            available_models,
            index=available_models.index(config.get('agent_model', available_models[0])) 
            if config.get('agent_model') in available_models else 0
        )
        updated_config['agent_model'] = agent_model
    
    # Agent Configuration
    st.markdown("**Research Settings**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_agents = st.slider(
            "Number of Agents:",
            min_value=1,
            max_value=10,
            value=config.get('num_agents', 3),
            help="Number of research agents to run in parallel"
        )
        updated_config['num_agents'] = num_agents
    
    with col2:
        max_results = st.slider(
            "Max Results per Agent:",
            min_value=1,
            max_value=50,
            value=config.get('max_results_per_agent', 10),
            help="Maximum results each agent should find"
        )
        updated_config['max_results_per_agent'] = max_results
    
    with col3:
        timeout = st.slider(
            "Agent Timeout (seconds):",
            min_value=10,
            max_value=600,
            value=config.get('agent_timeout', 300),
            help="Maximum time each agent can run"
        )
        updated_config['agent_timeout'] = timeout
    
    # Notify callback if config changed
    if on_update and updated_config != config:
        on_update(updated_config)
    
    return updated_config


def render_status_card(
    title: str, 
    status: str, 
    details: Optional[Dict[str, Any]] = None,
    show_details: bool = False
) -> None:
    """
    Render a status card with optional details.
    
    Args:
        title: Card title
        status: Status text
        details: Optional details dictionary
        show_details: Whether to show details by default
    """
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**{title}**")
            st.markdown(format_agent_status(status))
        
        with col2:
            if details:
                execution_time = details.get('execution_time', 0)
                if execution_time > 0:
                    st.metric("Time", format_execution_time(execution_time))
        
        if details and show_details:
            with st.expander("Details"):
                for key, value in details.items():
                    if key != 'execution_time':  # Already shown above
                        formatted_key = key.replace('_', ' ').title()
                        st.write(f"**{formatted_key}**: {value}")


def render_conversation_display(
    conversation: List[Dict[str, str]], 
    max_messages: int = 10
) -> None:
    """
    Render conversation history.
    
    Args:
        conversation: List of conversation messages
        max_messages: Maximum messages to display
    """
    if not conversation:
        st.info("No conversation history")
        return
    
    st.subheader("Conversation History")
    
    # Show recent messages
    recent_messages = conversation[-max_messages:] if len(conversation) > max_messages else conversation
    
    if len(conversation) > max_messages:
        st.info(f"Showing last {max_messages} of {len(conversation)} messages")
    
    for message in recent_messages:
        render_chat_message(message)
    
    # Option to show all messages
    if len(conversation) > max_messages:
        if st.button("Show All Messages"):
            st.write("**Full Conversation:**")
            for message in conversation:
                render_chat_message(message)


def render_info_box(message: str, box_type: str = "info") -> None:
    """
    Render an information box.
    
    Args:
        message: Message to display
        box_type: Type of box ('info', 'success', 'warning', 'error')
    """
    if box_type == "info":
        st.info(message)
    elif box_type == "success":
        st.success(message)
    elif box_type == "warning":
        st.warning(message)
    elif box_type == "error":
        st.error(message)
    else:
        st.info(message)