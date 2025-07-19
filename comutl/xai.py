"""
xAI LLM implementation
"""

from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class XaiLLM(BaseLLM):
    """xAI LLM implementation using OpenAI-compatible API"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is required for xAI. Install with: pip install openai")
        
        # Default model and temperature
        self.model = kwargs.get('model', 'grok-4-latest')
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 4096)
        
        # xAI uses OpenAI-compatible API with different base URL
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using xAI Grok"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert developer who carefully modifies code according to instructions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error communicating with xAI: {e}")
            return ""
    
    @property
    def model_name(self) -> str:
        return "xAI Grok"
    
    @property
    def required_env_vars(self) -> list:
        return ["XAI_API_KEY"]

