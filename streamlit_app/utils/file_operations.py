"""
File operations utilities for the Streamlit application.
"""

import os
import json
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


def save_research_session(
    session_data: Dict[str, Any], 
    filename: Optional[str] = None
) -> Tuple[bool, str]:
    """Save research session to file."""
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_session_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs("saved_sessions", exist_ok=True)
        filepath = os.path.join("saved_sessions", filename)
        
        # Add metadata
        session_with_metadata = {
            "saved_at": datetime.now().isoformat(),
            "version": "1.0",
            "session_data": session_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_with_metadata, f, indent=2, ensure_ascii=False)
        
        return True, filepath
        
    except Exception as e:
        return False, f"Error saving session: {str(e)}"


def load_research_session(filepath: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Load research session from file."""
    try:
        if not os.path.exists(filepath):
            return False, None, "File not found"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract session data
        if isinstance(data, dict) and "session_data" in data:
            return True, data["session_data"], "Session loaded successfully"
        else:
            # Legacy format - assume the whole file is session data
            return True, data, "Session loaded successfully (legacy format)"
        
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON file: {str(e)}"
    except Exception as e:
        return False, None, f"Error loading session: {str(e)}"


def list_saved_sessions(directory: str = "saved_sessions") -> List[Dict[str, Any]]:
    """List all saved research sessions."""
    sessions = []
    
    if not os.path.exists(directory):
        return sessions
    
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                filepath = os.path.join(directory, filename)
                try:
                    # Get file stats
                    stat = os.stat(filepath)
                    created_at = datetime.fromtimestamp(stat.st_ctime)
                    modified_at = datetime.fromtimestamp(stat.st_mtime)
                    file_size = stat.st_size
                    
                    # Try to read basic info from file
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    session_info = {
                        "filename": filename,
                        "filepath": filepath,
                        "created_at": created_at.isoformat(),
                        "modified_at": modified_at.isoformat(),
                        "file_size": file_size,
                        "has_results": False,
                        "query": "Unknown"
                    }
                    
                    # Extract additional info if available
                    if isinstance(data, dict):
                        if "session_data" in data:
                            session_data = data["session_data"]
                        else:
                            session_data = data
                        
                        # Extract query and results info
                        if "query" in session_data:
                            session_info["query"] = session_data["query"]
                        
                        if "search_results" in session_data and session_data["search_results"]:
                            session_info["has_results"] = True
                            session_info["num_results"] = len(session_data["search_results"])
                    
                    sessions.append(session_info)
                    
                except Exception as e:
                    # If we can't read the file, still include basic info
                    sessions.append({
                        "filename": filename,
                        "filepath": filepath,
                        "error": str(e),
                        "query": "Error reading file"
                    })
        
        # Sort by modified date, newest first
        sessions.sort(key=lambda x: x.get("modified_at", ""), reverse=True)
        
    except Exception as e:
        pass  # Return empty list if directory can't be read
    
    return sessions


def export_results_to_file(
    results: List[Dict[str, Any]], 
    format_type: str, 
    filename: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str]:
    """Export results to file in specified format."""
    try:
        from streamlit_app.services.export_service import ExportService
        
        # Generate filename if not provided
        if filename is None:
            query = metadata.get("query", "research") if metadata else "research"
            filename = ExportService.get_filename_for_export(query, format_type)
        
        # Ensure exports directory exists
        os.makedirs("exports", exist_ok=True)
        filepath = os.path.join("exports", filename)
        
        # Generate content based on format
        if format_type == "json":
            content = ExportService.export_to_json(results, metadata)
        elif format_type == "csv":
            content = ExportService.export_to_csv(results)
        elif format_type == "markdown":
            title = metadata.get("query", "Research Results") if metadata else "Research Results"
            content = ExportService.export_to_markdown(results, title, metadata)
        else:
            return False, f"Unsupported format: {format_type}"
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, filepath
        
    except Exception as e:
        return False, f"Error exporting to file: {str(e)}"


def create_temporary_file(content: str, suffix: str = ".txt") -> str:
    """Create a temporary file with the given content."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name
    except Exception as e:
        raise Exception(f"Error creating temporary file: {str(e)}")


def cleanup_temporary_files(filepaths: List[str]) -> None:
    """Clean up temporary files."""
    for filepath in filepaths:
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass  # Ignore cleanup errors


def get_file_size_human_readable(size_bytes: int) -> str:
    """Convert file size to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_file_path(filepath: str) -> Tuple[bool, str]:
    """Validate file path for security."""
    try:
        # Normalize path
        normalized_path = os.path.normpath(filepath)
        
        # Check for path traversal attempts
        if ".." in normalized_path:
            return False, "Path traversal not allowed"
        
        # Check if path is absolute (might be problematic)
        if os.path.isabs(normalized_path):
            return False, "Absolute paths not recommended"
        
        # Check for valid characters (basic check)
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in normalized_path for char in invalid_chars):
            return False, "Invalid characters in path"
        
        return True, "Path is valid"
        
    except Exception as e:
        return False, f"Error validating path: {str(e)}"


def ensure_directory_exists(directory: str) -> bool:
    """Ensure directory exists, create if it doesn't."""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception:
        return False