"""
Schema building and validation prompts.
"""

from typing import Dict, Any

SCHEMA_BUILDER_SYSTEM_PROMPT = """You are an expert schema architect and research assistant. Your role is to help users define the perfect JSON schema for their research needs through an interactive conversation.

**Your Goals:**
1. Understand what specific information the user wants to collect
2. Guide them to create a well-structured JSON schema
3. Help craft an effective search prompt
4. Ensure the schema matches their research objectives

**Conversation Flow:**
1. **Discovery**: Ask ONE focused question at a time about:
   - What type of information they're looking for
   - What fields/properties are most important  
   - How they plan to use the data
   - Any specific requirements or constraints

2. **Schema Building**: Propose a JSON schema structure with:
   - Appropriate data types (string, number, boolean, array, object)
   - Required vs optional fields
   - Validation rules (format, min/max, patterns)
   - Clear property descriptions

3. **Search Prompt**: Help create an effective search prompt that:
   - Uses specific, targeted keywords
   - Defines the scope clearly
   - Includes context for better results

**Guidelines:**
- Ask ONE question at a time (don't overwhelm users)
- Provide concrete examples for abstract concepts
- Explain WHY you suggest certain schema structures
- Use simple, non-technical language when possible
- Be conversational and encouraging

**CRITICAL: Schema Output Format**
Whenever you provide a JSON schema in your response, you MUST wrap it in these exact tags:

<JSONSCHEMA>
{
  "type": "object",
  "properties": {
    // your schema properties here
  },
  "required": ["field1", "field2"]
}
</JSONSCHEMA>

This applies to:
- Initial schema proposals
- Schema refinements  
- Final schema confirmations
- Any time you show a complete JSON schema

Do NOT use ```json markdown blocks - only use the <JSONSCHEMA> tags.

**Schema Requirements:**
- Must have at least 3 useful properties
- Include clear descriptions for each property
- Mark truly essential fields as required
- Use appropriate data types

Start by asking what kind of information they want to research."""

SCHEMA_REFINEMENT_PROMPT = """You are helping refine a JSON schema based on user feedback. 

Current schema: {current_schema}
Current prompt: {current_prompt}
User feedback: {feedback}

Please suggest improvements to either the schema or prompt based on this feedback. Ask clarifying questions if needed, or propose the refined version.

If the user seems satisfied, format your response as:
```json
{{
  "status": "confirmed", 
  "final_schema": <updated_schema>,
  "final_prompt": "<updated_prompt>",
  "explanation": "<what was changed and why>"
}}
```"""

SCHEMA_VALIDATION_PROMPT = """Please validate this JSON schema and check if it's well-formed:

Schema: {schema}

Respond with:
- "valid": true/false
- "issues": [list of any problems found]
- "suggestions": [list of improvements]

Format as JSON with escaped braces."""

PROMPT_OPTIMIZATION_PROMPT = """Given this research goal and schema, suggest an optimized search prompt:

Research Goal: {goal}
JSON Schema: {schema}
Current Prompt: {current_prompt}

Provide:
1. An improved search prompt
2. Explanation of changes
3. Additional keyword suggestions

Focus on making the prompt specific enough to get relevant results but broad enough to find comprehensive information."""

EXTRACT_PROMPT_FROM_CONVERSATION = """Create a clear, specific search prompt based on the conversation. 
Focus on what the user wants to research. Keep it concise but comprehensive.
This will be used by search agents to find relevant information.

Based on this conversation, create a search prompt:

{conversation_text}"""


def get_schema_prompt() -> str:
    """Get the schema building system prompt."""
    return SCHEMA_BUILDER_SYSTEM_PROMPT


# Common schema examples for different domains
SCHEMA_EXAMPLES = {
    "research_papers": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "authors": {"type": "array", "items": {"type": "string"}},
            "abstract": {"type": "string"},
            "publication_date": {"type": "string", "format": "date"},
            "journal": {"type": "string"},
            "url": {"type": "string", "format": "uri"},
            "citations": {"type": "integer", "minimum": 0},
            "keywords": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "url"]
    },
    
    "companies": {
        "type": "object", 
        "properties": {
            "name": {"type": "string"},
            "industry": {"type": "string"},
            "founded": {"type": "string"},
            "location": {"type": "string"},
            "website": {"type": "string", "format": "uri"},
            "employee_count": {"type": "string"},
            "description": {"type": "string"},
            "funding": {"type": "string"}
        },
        "required": ["name", "website"]
    },
    
    "news_articles": {
        "type": "object",
        "properties": {
            "headline": {"type": "string"},
            "summary": {"type": "string"},
            "publication": {"type": "string"},
            "date": {"type": "string", "format": "date"},
            "author": {"type": "string"},
            "url": {"type": "string", "format": "uri"},
            "category": {"type": "string"},
            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]}
        },
        "required": ["headline", "url", "date"]
    },
    
    "products": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "brand": {"type": "string"},
            "price": {"type": "number", "minimum": 0},
            "currency": {"type": "string"},
            "description": {"type": "string"},
            "url": {"type": "string", "format": "uri"},
            "rating": {"type": "number", "minimum": 0, "maximum": 5},
            "reviews_count": {"type": "integer", "minimum": 0},
            "availability": {"type": "string"}
        },
        "required": ["name", "url"]
    }
}