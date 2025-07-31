"""
LLM service abstraction for the Streamlit application using agent system.
"""

from typing import Dict, Any, List, Optional
from agent_system.llm_apis import OpenRouterLLMApi
from agent_system.core import Message


class LLMService:
    """Service for managing LLM interactions using agent system."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._llm_cache = {}
    
    def get_llm_api(self, model: str, temperature: float = 0.3) -> OpenRouterLLMApi:
        """Get or create LLM API instance with caching."""
        cache_key = f"{model}_{temperature}"
        
        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = OpenRouterLLMApi({
                "api_key": self.api_key,
                "model": model,
                "temperature": temperature
            })
        
        return self._llm_cache[cache_key]
    
    def chat_completion(
        self, 
        messages: List[tuple[str, str]], 
        model: str, 
        temperature: float = 0.3
    ) -> str:
        """Perform chat completion with the specified model using agent system."""
        try:
            llm_api = self.get_llm_api(model, temperature)
            
            # Convert tuple messages to Message objects
            conversation = []
            for role, content in messages:
                # Map langchain roles to agent system roles
                if role in ["human", "user"]:
                    role = "user"
                elif role in ["ai", "assistant"]:
                    role = "assistant"
                elif role == "system":
                    role = "system"
                
                conversation.append(Message(role=role, content=content))
            
            response = llm_api.chat_completion(conversation)
            return response.content.strip()
        except Exception as e:
            raise Exception(f"LLM chat completion failed: {str(e)}")
    
    def simple_completion(self, prompt: str, model: str, temperature: float = 0.3) -> str:
        """Simple completion for single prompts."""
        return self.chat_completion([("user", prompt)], model, temperature)
    
    def validate_api_key(self) -> tuple[bool, str]:
        """Validate the API key by making a simple request."""
        try:
            response = self.simple_completion(
                "Hello, respond with 'OK' if you can read this.",
                "anthropic/claude-3-haiku",
                0.1
            )
            return True, "API key is valid"
        except Exception as e:
            return False, f"API key validation failed: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """Get list of available models (placeholder - would need actual API call)."""
        return [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-3.5-turbo",
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "mistralai/mixtral-8x7b-instruct",
            "mistralai/mistral-7b-instruct"
        ]
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4