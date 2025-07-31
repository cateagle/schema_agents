"""
Display formatting utilities for the Streamlit application.
"""

import json
import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime


def format_results_for_display(results: List[Dict[str, Any]], max_display: int = 10) -> str:
    """Format research results for display in the UI."""
    if not results:
        return "No results to display"
    
    # Limit displayed results
    display_results = results[:max_display]
    
    formatted_lines = []
    for i, result in enumerate(display_results, 1):
        formatted_lines.append(f"**Result {i}:**")
        
        # Display key fields first
        priority_fields = ["title", "headline", "name", "url", "summary", "description"]
        displayed_fields = set()
        
        # Show priority fields first
        for field in priority_fields:
            if field in result and result[field]:
                value = str(result[field])
                if field == "url" and value.startswith("http"):
                    formatted_lines.append(f"- **{field.title()}**: [{value}]({value})")
                else:
                    # Truncate long text
                    if len(value) > 200:
                        value = value[:200] + "..."
                    formatted_lines.append(f"- **{field.title()}**: {value}")
                displayed_fields.add(field)
        
        # Show remaining fields
        for field, value in result.items():
            if field not in displayed_fields and value:
                formatted_field = field.replace('_', ' ').title()
                if isinstance(value, (dict, list)):
                    formatted_lines.append(f"- **{formatted_field}**: `{json.dumps(value)}`")
                else:
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    formatted_lines.append(f"- **{formatted_field}**: {value_str}")
        
        formatted_lines.append("")  # Empty line between results
    
    # Add note if there are more results
    if len(results) > max_display:
        formatted_lines.append(f"*... and {len(results) - max_display} more results*")
    
    return "\n".join(formatted_lines)


def create_results_summary_table(results: List[Dict[str, Any]]) -> None:
    """Create a summary table of results in Streamlit."""
    if not results:
        st.info("No results to display")
        return
    
    # Extract common fields
    all_fields = set()
    for result in results:
        all_fields.update(result.keys())
    
    # Priority fields for table display
    priority_fields = ["title", "headline", "name", "url", "summary", "description", "score", "relevance_score"]
    
    # Select fields to display (max 5-6 columns)
    display_fields = []
    for field in priority_fields:
        if field in all_fields:
            display_fields.append(field)
        if len(display_fields) >= 6:
            break
    
    # Add any remaining important fields
    if len(display_fields) < 4:
        for field in sorted(all_fields):
            if field not in display_fields and len(display_fields) < 6:
                display_fields.append(field)
    
    # Create table data
    table_data = []
    for i, result in enumerate(results, 1):
        row = {"#": i}
        for field in display_fields:
            value = result.get(field, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            row[field.replace('_', ' ').title()] = value
        table_data.append(row)
    
    # Display table
    st.dataframe(table_data, use_container_width=True)


def format_json_for_display(data: Dict[str, Any], indent: int = 2) -> str:
    """Format JSON data for pretty display."""
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception as e:
        return f"Error formatting JSON: {str(e)}"


def create_progress_tracker(current_step: int, total_steps: int, step_names: List[str]) -> None:
    """Create a progress tracker in Streamlit."""
    if total_steps == 0:
        return
    
    progress_percentage = (current_step - 1) / total_steps
    st.progress(progress_percentage)
    
    # Show step indicators
    cols = st.columns(total_steps)
    for i, (col, step_name) in enumerate(zip(cols, step_names), 1):
        with col:
            if i < current_step:
                st.success(f"✅ {step_name}")
            elif i == current_step:
                st.info(f"🔄 {step_name}")
            else:
                st.write(f"⏳ {step_name}")


def format_execution_time(seconds: float) -> str:
    """Format execution time in a human-readable way."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"


def create_metric_cards(metrics: Dict[str, Any]) -> None:
    """Create metric cards in Streamlit."""
    if not metrics:
        return
    
    # Organize metrics into columns
    metric_items = list(metrics.items())
    num_cols = min(len(metric_items), 4)
    
    if num_cols > 0:
        cols = st.columns(num_cols)
        
        for i, (key, value) in enumerate(metric_items[:num_cols]):
            with cols[i % num_cols]:
                # Format key
                formatted_key = key.replace('_', ' ').title()
                
                # Format value
                if isinstance(value, float):
                    if 0 <= value <= 1:
                        formatted_value = f"{value:.1%}"
                    else:
                        formatted_value = f"{value:.2f}"
                elif isinstance(value, dict):
                    formatted_value = f"{len(value)} items"
                elif isinstance(value, list):
                    formatted_value = f"{len(value)} items"
                else:
                    formatted_value = str(value)
                
                st.metric(formatted_key, formatted_value)


def generate_search_summary(
    query: str, 
    total_results: int, 
    execution_time: float, 
    agent_count: int
) -> str:
    """Generate a search summary string."""
    time_str = format_execution_time(execution_time)
    
    summary_parts = [
        f"**Search Query**: {query}",
        f"**Total Results**: {total_results}",
        f"**Agents Used**: {agent_count}",
        f"**Execution Time**: {time_str}"
    ]
    
    return " | ".join(summary_parts)


def create_collapsible_json(title: str, data: Dict[str, Any], expanded: bool = False) -> None:
    """Create a collapsible JSON display in Streamlit."""
    with st.expander(title, expanded=expanded):
        st.json(data)


def format_agent_status(status: str) -> str:
    """Format agent status with appropriate emoji."""
    status_map = {
        "completed": "✅ Completed",
        "running": "🔄 Running",
        "failed": "❌ Failed", 
        "timeout": "⏰ Timeout",
        "pending": "⏳ Pending",
        "cancelled": "🚫 Cancelled"
    }
    
    return status_map.get(status.lower(), f"❓ {status.title()}")


def create_copy_button(text: str, button_text: str = "Copy to Clipboard") -> bool:
    """Create a copy to clipboard button (placeholder - actual implementation would need JS)."""
    # This is a placeholder - actual clipboard functionality requires custom JS component
    if st.button(button_text):
        st.success("Content copied to clipboard! (Feature requires custom JS component)")
        return True
    return False


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Format timestamp for display."""
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def create_download_button(
    data: str, 
    filename: str, 
    mime_type: str = "text/plain",
    button_text: str = "Download"
) -> None:
    """Create a download button in Streamlit."""
    st.download_button(
        label=button_text,
        data=data,
        file_name=filename,
        mime=mime_type
    )