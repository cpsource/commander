"""
ChatGPT LLM implementation
"""

from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ChatGPTLLM(BaseLLM):
    """ChatGPT LLM implementation using OpenAI's API"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is required for ChatGPT. Install with: pip install openai")
        
        # Default model and temperature
        self.model = kwargs.get('model', 'gpt-4')
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 4096)
        
        self.client = openai.OpenAI(api_key=api_key)
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using ChatGPT"""
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
            print(f"Error communicating with ChatGPT: {e}")
            return ""
    
    @property
    def model_name(self) -> str:
        return "ChatGPT"
    
    @property
    def required_env_vars(self) -> list:
        return ["OPENAI_API_KEY"]

