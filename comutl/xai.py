"""
xAI LLM implementation with metadata capture
"""

import time
from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class XaiLLM(BaseLLM):
    """xAI LLM implementation using OpenAI-compatible API with metadata capture"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is required for xAI. Install with: pip install openai")
        
        # Default model and temperature
        self.model = kwargs.get('model', 'grok-4-latest')
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 8192)
        
        # xAI uses OpenAI-compatible API with different base URL
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
    
    def _extract_metadata_from_response(self, response) -> Dict:
        """Extract metadata from xAI API response"""
        metadata = {
            "provider": "xai",
            "model": self.model,
            "timestamp": time.time(),
        }
        
        print(f"🔍 DEBUG: Response type: {type(response)}")
        print(f"🔍 DEBUG: Response attributes: {dir(response)}")
        
        # Extract usage information from OpenAI-compatible response
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"🔍 DEBUG: Usage object: {usage}")
            print(f"🔍 DEBUG: Usage attributes: {dir(usage)}")
            
            # OpenAI format uses prompt_tokens and completion_tokens
            input_tokens = getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'completion_tokens', 0)
            total_tokens = getattr(usage, 'total_tokens', input_tokens + output_tokens)
            
            metadata.update({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            })
            
            print(f"🔍 DEBUG: Extracted tokens - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
            
            # Calculate cost estimates (Grok pricing - estimated)
            # Note: Update these rates when xAI publishes official pricing
            input_cost_per_token = 5.00 / 1000000  # Estimated $5 per million input tokens
            output_cost_per_token = 15.00 / 1000000  # Estimated $15 per million output tokens
            
            input_cost = input_tokens * input_cost_per_token
            output_cost = output_tokens * output_cost_per_token
            total_cost = input_cost + output_cost
            
            metadata.update({
                "estimated_cost_usd": round(total_cost, 6),
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
            })
            
            print(f"🔍 DEBUG: Calculated costs - Input: ${input_cost:.6f}, Output: ${output_cost:.6f}, Total: ${total_cost:.6f}")
        else:
            print("🔍 DEBUG: No usage attribute found in response")
        
        # Extract other response metadata
        if hasattr(response, 'id'):
            metadata["response_id"] = response.id
        
        if hasattr(response, 'model'):
            metadata["actual_model"] = response.model
            
        if hasattr(response, 'created'):
            metadata["created"] = response.created
            
        print(f"🔍 DEBUG: Final metadata: {metadata}")
        return metadata
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using xAI Grok with metadata capture"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            print(f"🤖 Processing with xAI Grok ({self.model})...")
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
            
            # Debug: Print what we captured
            print(f"🔍 DEBUG: Captured metadata keys: {list(self.last_response_metadata.keys())}")
            
            # Show useful info
            if 'total_tokens' in self.last_response_metadata:
                print(f"✅ Request successful. Total tokens used: {self.last_response_metadata['total_tokens']:,}")
            if 'estimated_cost_usd' in self.last_response_metadata:
                print(f"💰 Estimated cost: ${self.last_response_metadata['estimated_cost_usd']:.6f}")
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Error communicating with xAI: {e}")
            return ""
    
    @property
    def model_name(self) -> str:
        return f"xAI Grok ({self.model})"
    
    @property
    def required_env_vars(self) -> list:
        return ["XAI_API_KEY"]

