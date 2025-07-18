"""
Gemini LLM implementation
"""

from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class GeminiLLM(BaseLLM):
    """Gemini LLM implementation using LangChain"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain_google_genai is required for Gemini. Install with: pip install langchain-google-genai")
        
        # Default model and temperature
        model = kwargs.get('model', 'gemini-2.0-flash-exp')
        temperature = kwargs.get('temperature', 0.1)
        
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature
        )
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using Gemini AI"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            messages = [
                SystemMessage(content="You are an expert developer who carefully modifies code according to instructions."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            return ""
    
    @property
    def model_name(self) -> str:
        return "Gemini"
    
    @property
    def required_env_vars(self) -> list:
        return ["GOOGLE_API_KEY"]
