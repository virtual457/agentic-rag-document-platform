"""
LLM Adapter - Google Gemini using NEW SDK with Smart Model Routing
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import json
import time

from .model_config import ModelConfig


class LLMAdapter(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7, task: str = "general") -> str:
        """Generate text from prompt
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            task: Task type for model selection ('generation', 'evaluation', etc.)
        """
        pass
    
    @abstractmethod
    def generate_json(self, prompt: str, max_tokens: int = 4000, task: str = "general") -> Dict[str, Any]:
        """Generate structured JSON from prompt
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            task: Task type for model selection
        """
        pass


class GeminiAdapter(LLMAdapter):
    """Google Gemini adapter using NEW google-genai SDK"""
    
    def __init__(self, api_key: Optional[str] = None):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError(
                "google-genai not installed. Install with: pip install google-genai"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found")
        
        self.client = genai.Client(api_key=self.api_key)
        self.types = types
    
    def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7, task: str = "general") -> str:
        """Generate text using Gemini with retry logic and smart model routing"""
        
        # Select model based on task
        model = ModelConfig.get_model(task)
        
        # Add token limit instruction to prompt
        prompt_with_limit = f"{prompt}\n\nIMPORTANT: Keep response under {max_tokens} tokens."
        
        max_retries = 3
        retry_delay = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model,  # Smart routing based on task
                    contents=prompt_with_limit,
                    config=self.types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                )
                
                # Check if response is valid
                if not response:
                    raise Exception("No response from API")
                
                print(response)
                
                if not hasattr(response, 'text') or not response.text:
                    raise Exception("Empty response (API may be overloaded)")
                
                return response.text
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # Check if retriable error
                is_retriable = (
                    '503' in error_msg or 
                    'overloaded' in error_msg.lower() or 
                    'unavailable' in error_msg.lower() or
                    'empty response' in error_msg.lower()
                )
                
                if is_retriable and attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"   ⚠️  API issue, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                elif is_retriable:
                    print(f"\n❌ Gemini API failed after {max_retries} attempts.")
                    print("💡 The API is overloaded or unavailable.")
                    print("📝 Wait a few minutes and try again.")
                    raise Exception("API unavailable. Try again later.")
                else:
                    # Non-retriable error
                    print(f"\n❌ API Error: {error_msg}")
                    raise
        
        raise Exception(f"Failed after {max_retries} attempts: {last_error}")
    
    def generate_json(self, prompt: str, max_tokens: int = 4000, task: str = "general") -> Dict[str, Any]:
        """Generate JSON using Gemini with smart model routing"""
        
        json_prompt = f"{prompt}\n\nReturn ONLY valid JSON, no markdown, no explanation. Keep under {max_tokens} tokens."
        
        try:
            response = self.generate(json_prompt, max_tokens, temperature=0, task=task)
            
            if not response:
                raise Exception("Empty response from generate()")
            
            # Clean response
            text = response.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            if not text:
                raise Exception("Empty text after cleaning")
            
            return json.loads(text)
            
        except json.JSONDecodeError as e:
            print(f"\n❌ Failed to parse JSON response")
            print(f"Response was: {response[:200]}")
            raise Exception(f"Invalid JSON: {e}")
        except Exception:
            raise


class MockAdapter(LLMAdapter):
    """Mock adapter for testing"""
    
    def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        return "Mock response"
    
    def generate_json(self, prompt: str, max_tokens: int = 4000) -> Dict[str, Any]:
        return {"mock": "data"}


def create_llm_adapter(provider: str = "gemini", api_key: Optional[str] = None) -> LLMAdapter:
    """Factory function to create LLM adapter"""
    
    if provider == "gemini":
        return GeminiAdapter(api_key)
    elif provider == "mock":
        return MockAdapter()
    else:
        raise ValueError(f"Unknown provider: {provider}")
