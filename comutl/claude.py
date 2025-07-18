"""
Claude LLM implementation
"""

from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeLLM(BaseLLM):
    """Claude LLM implementation using Anthropic's API"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic is required for Claude. Install with: pip install anthropic")
        
        # Default model and temperature
        self.model = kwargs.get('model', 'claude-3-5-sonnet-20241022')
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 4096)
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using Claude AI"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are an expert developer who carefully modifies code according to instructions.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            print(f"Error communicating with Claude: {e}")
            return ""
    
    @property
    def model_name(self) -> str:
        return "Claude"
    
    @property
    def required_env_vars(self) -> list:
        return ["ANTHROPIC_API_KEY"]
