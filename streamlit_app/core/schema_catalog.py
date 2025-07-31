"""
Schema Catalog Manager - handles schema and prompt storage/retrieval.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class SchemaTemplate:
    """Schema template with metadata."""
    name: str
    description: str
    schema: Dict[str, Any]
    prompt: str
    created_at: str
    updated_at: str
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchemaTemplate':
        return cls(**data)


class SchemaCatalog:
    """Manages schema templates and prompts with file-based storage."""
    
    def __init__(self, schemas_dir: str = "schemas", prompts_dir: str = "prompts"):
        self.schemas_dir = Path(schemas_dir)
        self.prompts_dir = Path(prompts_dir)
        
        # Create directories if they don't exist
        self.schemas_dir.mkdir(exist_ok=True)
        self.prompts_dir.mkdir(exist_ok=True)
        
        # Load existing templates
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load all schema templates from files."""
        self.templates = {}
        
        for schema_file in self.schemas_dir.glob("*.json"):
            try:
                with open(schema_file, 'r') as f:
                    data = json.load(f)
                    template = SchemaTemplate.from_dict(data)
                    self.templates[template.name] = template
            except Exception as e:
                print(f"Error loading template {schema_file}: {e}")
    
    def get_all_templates(self) -> Dict[str, SchemaTemplate]:
        """Get all available schema templates."""
        return self.templates.copy()
    
    def get_template(self, name: str) -> Optional[SchemaTemplate]:
        """Get a specific template by name."""
        return self.templates.get(name)
    
    def save_template(self, template: SchemaTemplate) -> bool:
        """Save a schema template to file."""
        try:
            # Update timestamp
            template.updated_at = datetime.now().isoformat()
            
            # Save to file
            filename = f"{template.name.replace(' ', '_').lower()}.json"
            filepath = self.schemas_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(template.to_dict(), f, indent=2)
            
            # Update in-memory cache
            self.templates[template.name] = template
            return True
            
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """Delete a schema template."""
        try:
            if name not in self.templates:
                return False
            
            # Delete file
            filename = f"{name.replace(' ', '_').lower()}.json"
            filepath = self.schemas_dir / filename
            
            if filepath.exists():
                filepath.unlink()
            
            # Remove from memory
            del self.templates[name]
            return True
            
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
    
    def create_template(
        self, 
        name: str, 
        description: str, 
        schema: Dict[str, Any], 
        prompt: str = "",
        tags: List[str] = None
    ) -> SchemaTemplate:
        """Create a new schema template."""
        now = datetime.now().isoformat()
        
        template = SchemaTemplate(
            name=name,
            description=description,
            schema=schema,
            prompt=prompt,
            created_at=now,
            updated_at=now,
            tags=tags or []
        )
        
        return template
    
    def search_templates(self, query: str) -> List[SchemaTemplate]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for template in self.templates.values():
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower() or
                any(query_lower in tag.lower() for tag in template.tags)):
                results.append(template)
        
        return results
    
    def get_template_names(self) -> List[str]:
        """Get list of all template names."""
        return list(self.templates.keys())
    
    def export_template(self, name: str) -> Optional[str]:
        """Export template as JSON string."""
        template = self.get_template(name)
        if template:
            return json.dumps(template.to_dict(), indent=2)
        return None
    
    def import_template(self, json_data: str) -> bool:
        """Import template from JSON string."""
        try:
            data = json.loads(json_data)
            template = SchemaTemplate.from_dict(data)
            return self.save_template(template)
        except Exception as e:
            print(f"Error importing template: {e}")
            return False
    
    def initialize_default_templates(self) -> None:
        """Create some default templates if none exist."""
        if not self.templates:
            # Web scraping template
            web_template = self.create_template(
                name="Web Scraping",
                description="General web content scraping schema",
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Page or article title"},
                        "url": {"type": "string", "format": "uri", "description": "Source URL"},
                        "content": {"type": "string", "description": "Main content or summary"},
                        "author": {"type": "string", "description": "Content author if available"},
                        "date": {"type": "string", "description": "Publication date"},
                        "relevance": {"type": "number", "minimum": 0, "maximum": 10}
                    },
                    "required": ["title", "url", "content"]
                },
                prompt="Extract web content including title, URL, main content, author, publication date, and assess relevance on a scale of 0-10.",
                tags=["web", "scraping", "general"]
            )
            
            # News article template
            news_template = self.create_template(
                name="News Articles",
                description="Schema for news article extraction",
                schema={
                    "type": "object",
                    "properties": {
                        "headline": {"type": "string"},
                        "url": {"type": "string", "format": "uri"},
                        "summary": {"type": "string"},
                        "publication": {"type": "string"},
                        "publish_date": {"type": "string", "format": "date"},
                        "category": {"type": "string"},
                        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]}
                    },
                    "required": ["headline", "url", "summary"]
                },
                prompt="Extract news articles with headline, URL, summary, publication name, publish date, category, and sentiment analysis.",
                tags=["news", "articles", "media"]
            )
            
            # Research papers template
            research_template = self.create_template(
                name="Research Papers",
                description="Academic research paper schema",
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "authors": {"type": "array", "items": {"type": "string"}},
                        "abstract": {"type": "string"},
                        "url": {"type": "string", "format": "uri"},
                        "publication_venue": {"type": "string"},
                        "publication_year": {"type": "integer"},
                        "doi": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "citation_count": {"type": "integer"}
                    },
                    "required": ["title", "authors", "abstract", "url"]
                },
                prompt="Extract academic research papers with title, authors, abstract, publication venue, year, DOI, keywords, and citation count.",
                tags=["academic", "research", "papers"]
            )
            
            # Save default templates
            self.save_template(web_template)
            self.save_template(news_template)
            self.save_template(research_template)