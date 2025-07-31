"""
Schema Catalog UI component for managing schema templates and prompts.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional, List

from streamlit_app.core.schema_catalog import SchemaCatalog, SchemaTemplate
from streamlit_app.ui.base_components import render_info_box


class SchemaCatalogUI:
    """UI component for managing schema catalog."""
    
    def __init__(self, schemas_dir: str = "schemas", prompts_dir: str = "prompts"):
        self.catalog = SchemaCatalog(schemas_dir, prompts_dir)
        
        # Initialize default templates if none exist
        if not self.catalog.get_all_templates():
            self.catalog.initialize_default_templates()
    
    def render(self) -> Optional[Dict[str, Any]]:
        """Render the schema catalog interface."""
        st.header("📚 Schema Catalog")
        st.markdown("Manage your schema templates and prompts.")
        
        # Action tabs
        tab1, tab2, tab3 = st.tabs(["📋 Browse", "➕ Create", "⚙️ Manage"])
        
        selected_schema = None
        
        with tab1:
            selected_schema = self._render_browse_tab()
        
        with tab2:
            self._render_create_tab()
        
        with tab3:
            self._render_manage_tab()
        
        return selected_schema
    
    def _render_browse_tab(self) -> Optional[Dict[str, Any]]:
        """Render the browse templates tab."""
        templates = self.catalog.get_all_templates()
        
        if not templates:
            render_info_box("No templates available. Create one in the 'Create' tab.", "info")
            return None
        
        # Search functionality
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search templates:", placeholder="Search by name, description, or tags")
        with col2:
            if st.button("Clear", use_container_width=True):
                st.rerun()
        
        # Filter templates
        if search_query:
            filtered_templates = self.catalog.search_templates(search_query)
        else:
            filtered_templates = list(templates.values())
        
        if not filtered_templates:
            render_info_box("No templates match your search.", "warning")
            return None
        
        # Display templates
        selected_template = None
        
        for template in filtered_templates:
            with st.expander(f"📋 {template.name}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:** {template.description}")
                    if template.tags:
                        tags_str = " ".join([f"`{tag}`" for tag in template.tags])
                        st.markdown(f"**Tags:** {tags_str}")
                    st.markdown(f"**Updated:** {template.updated_at[:10]}")
                    
                    # Show schema preview
                    with st.expander("🔍 Schema Preview"):
                        st.json(template.schema)
                    
                    # Show prompt
                    if template.prompt:
                        with st.expander("💬 Prompt"):
                            st.text_area("Prompt content:", value=template.prompt, disabled=True, key=f"prompt_preview_{template.name}", label_visibility="collapsed")
                
                with col2:
                    if st.button("Use This Schema", key=f"use_{template.name}", use_container_width=True):
                        selected_template = template.schema
                        st.success(f"Selected: {template.name}")
                    
                    if st.button("Edit", key=f"edit_{template.name}", use_container_width=True):
                        st.session_state[f"edit_template_{template.name}"] = True
                        st.rerun()
                    
                    if st.button("Copy JSON", key=f"copy_{template.name}", use_container_width=True):
                        st.code(json.dumps(template.schema, indent=2))
        
        return selected_template
    
    def _render_create_tab(self) -> None:
        """Render the create new template tab."""
        st.subheader("➕ Create New Schema Template")
        
        with st.form("create_template_form"):
            # Basic info
            name = st.text_input("Template Name:", placeholder="e.g., Product Reviews")
            description = st.text_area("Description:", placeholder="Describe what this schema is for...")
            
            # Tags
            tags_input = st.text_input("Tags (comma-separated):", placeholder="web, reviews, products")
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
            
            # Schema creation method
            schema_method = st.radio(
                "Schema Creation Method:",
                ["Manual JSON", "Form Builder", "From Example"]
            )
            
            schema = None
            
            if schema_method == "Manual JSON":
                schema_json = st.text_area(
                    "JSON Schema:",
                    value='{\n  "type": "object",\n  "properties": {\n    "title": {"type": "string"}\n  },\n  "required": ["title"]\n}',
                    height=200
                )
                try:
                    schema = json.loads(schema_json)
                except json.JSONDecodeError:
                    st.error("Invalid JSON schema")
                    schema = None
            
            elif schema_method == "Form Builder":
                schema = self._render_form_builder()
            
            elif schema_method == "From Example":
                example_data = st.text_area(
                    "Example Data (JSON):",
                    placeholder='{"title": "Sample Title", "rating": 5, "review": "Great product!"}',
                    height=100
                )
                if example_data and st.button("Generate Schema from Example"):
                    try:
                        data = json.loads(example_data)
                        schema = self._generate_schema_from_example(data)
                        st.json(schema)
                    except json.JSONDecodeError:
                        st.error("Invalid JSON example")
            
            # Prompt
            prompt = st.text_area(
                "Research Prompt:",
                placeholder="Describe how agents should extract data using this schema...",
                height=100
            )
            
            # Submit
            if st.form_submit_button("Create Template", use_container_width=True):
                if not name:
                    st.error("Template name is required")
                elif not schema:
                    st.error("Valid schema is required")
                else:
                    template = self.catalog.create_template(
                        name=name,
                        description=description,
                        schema=schema,
                        prompt=prompt,
                        tags=tags
                    )
                    
                    if self.catalog.save_template(template):
                        st.success(f"Template '{name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to save template")
    
    def _render_manage_tab(self) -> None:
        """Render the manage templates tab."""
        st.subheader("⚙️ Manage Templates")
        
        templates = self.catalog.get_all_templates()
        
        if not templates:
            render_info_box("No templates to manage.", "info")
            return
        
        # Template selector
        template_names = list(templates.keys())
        selected_name = st.selectbox("Select template to manage:", template_names)
        
        if not selected_name:
            return
        
        template = templates[selected_name]
        
        # Check for edit mode
        edit_key = f"edit_template_{selected_name}"
        in_edit_mode = st.session_state.get(edit_key, False)
        
        if in_edit_mode:
            self._render_edit_template(template, edit_key)
        else:
            self._render_template_details(template, selected_name)
    
    def _render_edit_template(self, template: SchemaTemplate, edit_key: str) -> None:
        """Render template editing interface."""
        st.subheader(f"✏️ Editing: {template.name}")
        
        with st.form("edit_template_form"):
            # Editable fields
            new_description = st.text_area("Description:", value=template.description)
            new_tags = st.text_input("Tags:", value=", ".join(template.tags))
            new_schema_json = st.text_area(
                "Schema (JSON):",
                value=json.dumps(template.schema, indent=2),
                height=300
            )
            new_prompt = st.text_area("Prompt:", value=template.prompt, height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Save Changes", use_container_width=True):
                    try:
                        new_schema = json.loads(new_schema_json)
                        new_tags_list = [tag.strip() for tag in new_tags.split(",") if tag.strip()]
                        
                        # Update template
                        template.description = new_description
                        template.schema = new_schema
                        template.prompt = new_prompt
                        template.tags = new_tags_list
                        
                        if self.catalog.save_template(template):
                            st.success("Template updated successfully!")
                            st.session_state[edit_key] = False
                            st.rerun()
                        else:
                            st.error("Failed to save changes")
                            
                    except json.JSONDecodeError:
                        st.error("Invalid JSON schema")
            
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state[edit_key] = False
                    st.rerun()
    
    def _render_template_details(self, template: SchemaTemplate, template_name: str) -> None:
        """Render template details and actions."""
        # Template info
        st.markdown(f"**Description:** {template.description}")
        st.markdown(f"**Tags:** {', '.join(template.tags) if template.tags else 'None'}")
        st.markdown(f"**Created:** {template.created_at[:10]}")
        st.markdown(f"**Updated:** {template.updated_at[:10]}")
        
        # Schema display
        st.subheader("Schema")
        st.json(template.schema)
        
        # Prompt display
        if template.prompt:
            st.subheader("Prompt")
            st.text_area("Prompt content:", value=template.prompt, disabled=True, height=100, label_visibility="collapsed")
        
        # Actions
        st.subheader("Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Edit", use_container_width=True):
                st.session_state[f"edit_template_{template_name}"] = True
                st.rerun()
        
        with col2:
            if st.button("Export", use_container_width=True):
                export_data = self.catalog.export_template(template_name)
                if export_data:
                    st.download_button(
                        "Download JSON",
                        data=export_data,
                        file_name=f"{template_name.replace(' ', '_').lower()}.json",
                        mime="application/json"
                    )
        
        with col3:
            if st.button("Duplicate", use_container_width=True):
                new_name = f"{template_name} (Copy)"
                new_template = self.catalog.create_template(
                    name=new_name,
                    description=template.description,
                    schema=template.schema.copy(),
                    prompt=template.prompt,
                    tags=template.tags.copy()
                )
                if self.catalog.save_template(new_template):
                    st.success(f"Template duplicated as '{new_name}'")
                    st.rerun()
        
        with col4:
            if st.button("Delete", use_container_width=True, type="secondary"):
                if st.session_state.get(f"confirm_delete_{template_name}", False):
                    if self.catalog.delete_template(template_name):
                        st.success("Template deleted")
                        st.rerun()
                    else:
                        st.error("Failed to delete template")
                else:
                    st.session_state[f"confirm_delete_{template_name}"] = True
                    st.warning("Click again to confirm deletion")
    
    def _render_form_builder(self) -> Optional[Dict[str, Any]]:
        """Render form-based schema builder."""
        st.markdown("**Form Builder** (Basic implementation)")
        
        # Initialize schema structure
        if 'form_schema' not in st.session_state:
            st.session_state.form_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        schema = st.session_state.form_schema
        
        # Add field interface
        st.markdown("**Add Field:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            field_name = st.text_input("Field Name:", key="new_field_name")
        with col2:
            field_type = st.selectbox("Type:", ["string", "number", "integer", "boolean", "array"], key="new_field_type")
        with col3:
            if st.button("Add Field") and field_name:
                schema["properties"][field_name] = {"type": field_type}
                if field_type == "array":
                    schema["properties"][field_name]["items"] = {"type": "string"}
                st.rerun()
        
        # Display current fields
        if schema["properties"]:
            st.markdown("**Current Fields:**")
            for field_name, field_def in schema["properties"].items():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(field_name)
                with col2:
                    st.write(field_def["type"])
                with col3:
                    if st.button("Remove", key=f"remove_{field_name}"):
                        del schema["properties"][field_name]
                        if field_name in schema["required"]:
                            schema["required"].remove(field_name)
                        st.rerun()
        
        return schema if schema["properties"] else None
    
    def _generate_schema_from_example(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a JSON schema from example data."""
        def get_type(value):
            if isinstance(value, str):
                return "string"
            elif isinstance(value, int):
                return "integer"
            elif isinstance(value, float):
                return "number"
            elif isinstance(value, bool):
                return "boolean"
            elif isinstance(value, list):
                return "array"
            elif isinstance(value, dict):
                return "object"
            else:
                return "string"
        
        properties = {}
        required = []
        
        for key, value in data.items():
            field_type = get_type(value)
            properties[key] = {"type": field_type}
            
            if field_type == "array" and value:
                # Infer array item type from first element
                item_type = get_type(value[0])
                properties[key]["items"] = {"type": item_type}
            
            # Mark as required (you might want to make this configurable)
            required.append(key)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }