"""
Base LLM class that defines the interface for all LLM providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple


class BaseLLM(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize the LLM with API key and optional parameters"""
        self.api_key = api_key
        self.kwargs = kwargs
    
    @abstractmethod
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """
        Process files according to instructions
        
        Args:
            instructions: The processing instructions
            files_data: Dict mapping filename to (content, language) tuples
            
        Returns:
            The AI model's response as a string
        """
        pass
    
    def create_prompt(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Create a comprehensive prompt for the LLM"""
        prompt = f"""You are a skilled developer tasked with modifying multiple files according to specific instructions.

INSTRUCTIONS:
{instructions}

FILES TO PROCESS:
"""
        
        for filename, (content, language) in files_data.items():
            if language:
                prompt += f"\n---{filename}---\n```{language}\n{content}\n```\n"
            else:
                prompt += f"\n---{filename}---\n```\n{content}\n```\n"
        
        prompt += """

RESPONSE FORMAT:
For any files you wish to return in your reply, they must have this format:

---<full-file-spec>---
```<filetype>
< file contents here >
```

Only return files that need to be changed. If a file doesn't need modification, don't include it in your response.
Ensure all code is syntactically correct and follows best practices for the respective language.
"""
        
        return prompt
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the model being used"""
        pass
    
    @property
    @abstractmethod
    def required_env_vars(self) -> list:
        """Return list of required environment variables"""
        pass

