"""
ChatGPT LLM implementation with metadata capture
"""

import time
from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ChatGPTLLM(BaseLLM):
    """ChatGPT LLM implementation using OpenAI's API with metadata capture"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is required for ChatGPT. Install with: pip install openai")
        
        # Default model and temperature
        self.model = kwargs.get('model', 'gpt-4o')
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 8192)
        
        self.client = openai.OpenAI(api_key=api_key)
    
    def _extract_metadata_from_response(self, response) -> Dict:
        """Extract metadata from ChatGPT API response"""
        metadata = {
            "provider": "openai",
            "model": self.model,
            "timestamp": time.time(),
        }
        
        # Extract usage information
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            
            input_tokens = getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'completion_tokens', 0)
            total_tokens = getattr(usage, 'total_tokens', input_tokens + output_tokens)
            
            metadata.update({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            })
            
            # Calculate cost estimates (OpenAI GPT-4o pricing)
            if 'gpt-4o' in self.model:
                input_cost_per_token = 2.50 / 1000000   # $2.50 per million input tokens
                output_cost_per_token = 10.00 / 1000000 # $10.00 per million output tokens
            elif 'gpt-4' in self.model:
                input_cost_per_token = 30.00 / 1000000  # $30.00 per million input tokens
                output_cost_per_token = 60.00 / 1000000 # $60.00 per million output tokens
            elif 'gpt-3.5' in self.model:
                input_cost_per_token = 0.50 / 1000000   # $0.50 per million input tokens
                output_cost_per_token = 1.50 / 1000000  # $1.50 per million output tokens
            else:
                # Default to GPT-4o pricing
                input_cost_per_token = 2.50 / 1000000
                output_cost_per_token = 10.00 / 1000000
            
            input_cost = input_tokens * input_cost_per_token
            output_cost = output_tokens * output_cost_per_token
            total_cost = input_cost + output_cost
            
            metadata.update({
                "estimated_cost_usd": round(total_cost, 6),
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
            })
        
        # Extract other response metadata
        if hasattr(response, 'id'):
            metadata["response_id"] = response.id
        
        if hasattr(response, 'model'):
            metadata["actual_model"] = response.model
            
        if hasattr(response, 'created'):
            metadata["created"] = response.created
            
        # Extract choice metadata
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'finish_reason'):
                metadata["finish_reason"] = choice.finish_reason
            
        return metadata
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using ChatGPT with metadata capture"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            print(f"🤖 Processing with ChatGPT ({self.model})...")
            start_time = time.time()
            
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
            
            end_time = time.time()
            
            # Extract and store metadata
            self.last_response_metadata = self._extract_metadata_from_response(response)
            self.last_response_metadata["response_time_seconds"] = round(end_time - start_time, 3)
            
            # Show useful info
            if 'total_tokens' in self.last_response_metadata:
                print(f"✅ Request successful. Total tokens used: {self.last_response_metadata['total_tokens']:,}")
            if 'estimated_cost_usd' in self.last_response_metadata:
                print(f"💰 Estimated cost: ${self.last_response_metadata['estimated_cost_usd']:.6f}")
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Error communicating with ChatGPT: {e}")
            return ""
    
    @property
    def model_name(self) -> str:
        return f"ChatGPT ({self.model})"
    
    @property
    def required_env_vars(self) -> list:
        return ["OPENAI_API_KEY"]

