"""
Claude LLM implementation with metadata capture
"""

import time
from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeLLM(BaseLLM):
    """Claude LLM implementation using Anthropic's API with metadata capture"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic is required for Claude. Install with: pip install anthropic")
        
        # Default model and temperature
        self.model = kwargs.get('model', 'claude-sonnet-4-20250514')
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 8192)
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def _extract_metadata_from_response(self, message) -> Dict:
        """Extract metadata from Claude API response"""
        metadata = {
            "provider": "anthropic",
            "model": self.model,
            "timestamp": time.time(),
        }
        
        # Extract usage information
        if hasattr(message, 'usage') and message.usage:
            usage = message.usage
            
            input_tokens = getattr(usage, 'input_tokens', 0)
            output_tokens = getattr(usage, 'output_tokens', 0)
            total_tokens = input_tokens + output_tokens
            
            metadata.update({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            })
            
            # Calculate cost estimates (Claude Sonnet 4 pricing)
            input_cost_per_token = 3.00 / 1000000  # $3 per million input tokens
            output_cost_per_token = 15.00 / 1000000  # $15 per million output tokens
            
            input_cost = input_tokens * input_cost_per_token
            output_cost = output_tokens * output_cost_per_token
            total_cost = input_cost + output_cost
            
            metadata.update({
                "estimated_cost_usd": round(total_cost, 6),
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
            })
        
        # Extract other response metadata
        if hasattr(message, 'id'):
            metadata["response_id"] = message.id
        
        if hasattr(message, 'model'):
            metadata["actual_model"] = message.model
            
        if hasattr(message, 'stop_reason'):
            metadata["stop_reason"] = message.stop_reason
            
        return metadata
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using Claude AI with metadata capture"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            print(f"🤖 Processing with Claude ({self.model})...")
            start_time = time.time()
            
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
            
            end_time = time.time()
            
            # Extract and store metadata
            self.last_response_metadata = self._extract_metadata_from_response(message)
            self.last_response_metadata["response_time_seconds"] = round(end_time - start_time, 3)
            
            # Show useful info
            if 'total_tokens' in self.last_response_metadata:
                print(f"✅ Request successful. Total tokens used: {self.last_response_metadata['total_tokens']:,}")
            if 'estimated_cost_usd' in self.last_response_metadata:
                print(f"💰 Estimated cost: ${self.last_response_metadata['estimated_cost_usd']:.6f}")
            
            return message.content[0].text
            
        except Exception as e:
            print(f"❌ Error communicating with Claude: {e}")
            return ""
    
    @property
    def model_name(self) -> str:
        return f"Claude ({self.model})"
    
    @property
    def required_env_vars(self) -> list:
        return ["ANTHROPIC_API_KEY"]

