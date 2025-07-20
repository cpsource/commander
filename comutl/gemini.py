"""
Gemini LLM implementation with metadata capture
"""

import time
from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class GeminiLLM(BaseLLM):
    """Gemini LLM implementation using LangChain with metadata capture"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain_google_genai is required for Gemini. Install with: pip install langchain-google-genai")
        
        # Default model and temperature
        self.model_name_str = kwargs.get('model', 'gemini-2.0-flash-exp')
        temperature = kwargs.get('temperature', 0.1)
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name_str,
            google_api_key=api_key,
            temperature=temperature
        )
    
    def _extract_metadata_from_response(self, response) -> Dict:
        """Extract metadata from Gemini API response"""
        metadata = {
            "provider": "google",
            "model": self.model_name_str,
            "timestamp": time.time(),
        }
        
        print(f"🔍 DEBUG: Response type: {type(response)}")
        print(f"🔍 DEBUG: Response attributes: {dir(response)}")
        
        # Try to extract usage information from LangChain response
        # LangChain may store this in response_metadata or usage_metadata
        usage_info = None
        
        if hasattr(response, 'response_metadata'):
            print(f"🔍 DEBUG: Response metadata: {response.response_metadata}")
            usage_info = response.response_metadata.get('usage_metadata') or response.response_metadata.get('usage')
        
        if hasattr(response, 'usage_metadata'):
            print(f"🔍 DEBUG: Usage metadata: {response.usage_metadata}")
            usage_info = response.usage_metadata
            
        if hasattr(response, 'usage'):
            print(f"🔍 DEBUG: Usage: {response.usage}")
            usage_info = response.usage
        
        # Try different possible attribute names for usage data
        for attr_name in ['token_usage', 'llm_output', 'generation_info']:
            if hasattr(response, attr_name):
                attr_value = getattr(response, attr_name)
                print(f"🔍 DEBUG: {attr_name}: {attr_value}")
                if attr_value and isinstance(attr_value, dict):
                    usage_info = usage_info or attr_value.get('usage') or attr_value.get('token_usage')
        
        if usage_info:
            print(f"🔍 DEBUG: Found usage info: {usage_info}")
            print(f"🔍 DEBUG: Usage info type: {type(usage_info)}")
            
            # Handle different formats of usage data
            input_tokens = 0
            output_tokens = 0
            total_tokens = 0
            
            if isinstance(usage_info, dict):
                # Dictionary format
                input_tokens = usage_info.get('prompt_tokens', 0) or usage_info.get('input_tokens', 0)
                output_tokens = usage_info.get('completion_tokens', 0) or usage_info.get('output_tokens', 0) or usage_info.get('candidates_token_count', 0)
                total_tokens = usage_info.get('total_tokens', input_tokens + output_tokens)
            else:
                # Object format
                input_tokens = getattr(usage_info, 'prompt_tokens', 0) or getattr(usage_info, 'input_tokens', 0)
                output_tokens = getattr(usage_info, 'completion_tokens', 0) or getattr(usage_info, 'output_tokens', 0) or getattr(usage_info, 'candidates_token_count', 0)
                total_tokens = getattr(usage_info, 'total_tokens', input_tokens + output_tokens)
            
            metadata.update({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            })
            
            print(f"🔍 DEBUG: Extracted tokens - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
            
            # Calculate cost estimates (Gemini 2.0 Flash pricing)
            # Gemini 2.0 Flash is free for now, but using estimated pricing for when it becomes paid
            input_cost_per_token = 0.075 / 1000000  # Estimated $0.075 per million input tokens
            output_cost_per_token = 0.30 / 1000000   # Estimated $0.30 per million output tokens
            
            input_cost = input_tokens * input_cost_per_token
            output_cost = output_tokens * output_cost_per_token
            total_cost = input_cost + output_cost
            
            metadata.update({
                "estimated_cost_usd": round(total_cost, 6),
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
                "note": "Gemini 2.0 Flash is currently free - costs are estimates for future pricing"
            })
            
            print(f"🔍 DEBUG: Calculated costs - Input: ${input_cost:.6f}, Output: ${output_cost:.6f}, Total: ${total_cost:.6f}")
        else:
            print("🔍 DEBUG: No usage information found in response")
        
        # Extract other response metadata
        if hasattr(response, 'id'):
            metadata["response_id"] = response.id
            
        if hasattr(response, 'response_metadata') and response.response_metadata:
            metadata["response_metadata"] = response.response_metadata
            
        print(f"🔍 DEBUG: Final metadata: {metadata}")
        return metadata
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using Gemini AI with metadata capture"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            print(f"🤖 Processing with Gemini ({self.model_name_str})...")
            start_time = time.time()
            
            messages = [
                SystemMessage(content="You are an expert developer who carefully modifies code according to instructions."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
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
                cost = self.last_response_metadata['estimated_cost_usd']
                if cost > 0:
                    print(f"💰 Estimated cost: ${cost:.6f}")
                else:
                    print(f"💰 Cost: FREE (Gemini 2.0 Flash is currently free)")
            
            return response.content
            
        except Exception as e:
            print(f"❌ Error communicating with Gemini: {e}")
            import traceback
            print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
            return ""
    
    @property
    def model_name(self) -> str:
        return f"Gemini ({self.model_name_str})"
    
    @property
    def required_env_vars(self) -> list:
        return ["GOOGLE_API_KEY"]

