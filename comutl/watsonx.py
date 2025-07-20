"""
WatsonX LLM implementation with metadata capture
"""

import time
from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    from ibm_watsonx_ai.foundation_models import Model
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False


class WatsonxLLM(BaseLLM):
    """WatsonX LLM implementation using IBM's WatsonX AI with metadata capture"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not WATSONX_AVAILABLE:
            raise ImportError("ibm-watsonx-ai is required for WatsonX. Install with: pip install ibm-watsonx-ai")
        
        # Updated to use a supported model
        self.model_id = kwargs.get('model', 'ibm/granite-3-8b-instruct')
        self.project_id = kwargs.get('project_id', None)
        self.url = kwargs.get('url', 'https://us-south.ml.cloud.ibm.com')
        
        # Check for required project_id
        if not self.project_id:
            raise ValueError("project_id is required for WatsonX")
        
        # Generation parameters
        self.generation_params = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: kwargs.get('max_tokens', 2048),
            GenParams.MIN_NEW_TOKENS: 1,
            GenParams.TEMPERATURE: kwargs.get('temperature', 0.1),
            GenParams.TOP_K: 50,
            GenParams.TOP_P: 1
        }
        
        # Initialize WatsonX model
        self.model = Model(
            model_id=self.model_id,
            params=self.generation_params,
            credentials={
                "apikey": api_key,
                "url": self.url
            },
            project_id=self.project_id
        )
    
    def _extract_metadata_from_response(self, response, response_details=None) -> Dict:
        """Extract metadata from WatsonX API response"""
        metadata = {
            "provider": "ibm_watsonx",
            "model": self.model_id,
            "timestamp": time.time(),
        }
        
        # WatsonX may provide usage information in different formats
        # Check if response_details contains usage info
        if response_details and isinstance(response_details, dict):
            # Look for token usage in various possible locations
            usage_info = response_details.get('usage') or response_details.get('results', [{}])[0].get('usage')
            
            if usage_info:
                # Extract token counts - WatsonX format may vary
                input_tokens = usage_info.get('prompt_tokens', 0) or usage_info.get('input_tokens', 0)
                output_tokens = usage_info.get('generated_tokens', 0) or usage_info.get('completion_tokens', 0) or usage_info.get('output_tokens', 0)
                total_tokens = usage_info.get('total_tokens', input_tokens + output_tokens)
                
                metadata.update({
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                })
                
                # Calculate cost estimates (WatsonX pricing varies by model)
                # Using estimated pricing for Granite models
                input_cost_per_token = 0.50 / 1000000   # Estimated $0.50 per million input tokens
                output_cost_per_token = 1.50 / 1000000  # Estimated $1.50 per million output tokens
                
                input_cost = input_tokens * input_cost_per_token
                output_cost = output_tokens * output_cost_per_token
                total_cost = input_cost + output_cost
                
                metadata.update({
                    "estimated_cost_usd": round(total_cost, 6),
                    "input_cost_usd": round(input_cost, 6),
                    "output_cost_usd": round(output_cost, 6),
                    "note": "WatsonX pricing varies by model and region - these are estimates"
                })
        
        # Try to estimate tokens from response length if no usage data available
        if 'total_tokens' not in metadata and response:
            estimated_output_tokens = len(response.split()) * 1.3  # Rough estimate
            metadata.update({
                "input_tokens": 0,  # We don't have the input length here
                "output_tokens": int(estimated_output_tokens),
                "total_tokens": int(estimated_output_tokens),
                "token_estimation": "estimated_from_response_length"
            })
        
        return metadata
    
    def create_prompt(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Create a more specific prompt for WatsonX"""
        prompt = f"""You are an expert developer. Follow the instructions precisely and return ONLY the modified files.

CRITICAL INSTRUCTIONS:
- Return ONLY files that need changes
- Use EXACTLY this format for each file:
---filename---
```filetype
file content here
```
- Do NOT include explanations, notes, or placeholder text
- Do NOT add "END" markers or extra commentary

TASK:
{instructions}

FILES TO PROCESS:
"""
        
        for filename, (content, language) in files_data.items():
            if language:
                prompt += f"\n---{filename}---\n```{language}\n{content}\n```\n"
            else:
                prompt += f"\n---{filename}---\n```\n{content}\n```\n"
        
        prompt += """

RESPOND WITH ONLY THE MODIFIED FILES IN THE EXACT FORMAT SHOWN ABOVE.
"""
        
        return prompt
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using WatsonX AI with metadata capture"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            print(f"🤖 Processing with WatsonX ({self.model_id})...")
            start_time = time.time()
            
            # Generate response using WatsonX
            response_obj = self.model.generate_text(prompt=prompt)
            
            end_time = time.time()
            
            # Handle different response formats from WatsonX
            if isinstance(response_obj, dict):
                # WatsonX returned a dictionary with detailed response
                print(f"🔍 DEBUG: WatsonX returned dict response")
                
                # Extract the actual text from results
                results = response_obj.get('results', [])
                if results and len(results) > 0:
                    response_text = results[0].get('generated_text', '')
                else:
                    response_text = str(response_obj)
                
                # Extract usage information from the response
                self.last_response_metadata = self._extract_metadata_from_watsonx_dict(response_obj)
                
            elif isinstance(response_obj, str):
                # Simple string response
                response_text = response_obj
                self.last_response_metadata = self._extract_metadata_from_response(response_text, None)
            else:
                # Unknown format, convert to string
                response_text = str(response_obj)
                self.last_response_metadata = self._extract_metadata_from_response(response_text, None)
            
            # Add timing information
            self.last_response_metadata["response_time_seconds"] = round(end_time - start_time, 3)
            
            # Show useful info
            if 'total_tokens' in self.last_response_metadata:
                print(f"✅ Request successful. Total tokens used: {self.last_response_metadata['total_tokens']:,}")
            if 'estimated_cost_usd' in self.last_response_metadata:
                print(f"💰 Estimated cost: ${self.last_response_metadata['estimated_cost_usd']:.6f}")
            
            return response_text
            
        except Exception as e:
            print(f"❌ Error communicating with WatsonX: {e}")
            import traceback
            print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
            return ""
    
    def _extract_metadata_from_watsonx_dict(self, response_dict: dict) -> Dict:
        """Extract metadata from WatsonX dictionary response"""
        metadata = {
            "provider": "ibm_watsonx",
            "model": self.model_id,
            "timestamp": time.time(),
        }
        
        print(f"🔍 DEBUG: WatsonX response keys: {response_dict.keys()}")
        
        # Extract model information
        if 'model_id' in response_dict:
            metadata["actual_model"] = response_dict['model_id']
        if 'model_version' in response_dict:
            metadata["model_version"] = response_dict['model_version']
        if 'created_at' in response_dict:
            metadata["created_at"] = response_dict['created_at']
        
        # Extract usage information from results
        results = response_dict.get('results', [])
        if results and len(results) > 0:
            result = results[0]
            print(f"🔍 DEBUG: First result: {result}")
            
            input_tokens = result.get('input_token_count', 0)
            output_tokens = result.get('generated_token_count', 0)
            total_tokens = input_tokens + output_tokens
            
            metadata.update({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            })
            
            print(f"🔍 DEBUG: Extracted tokens - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
            
            # Calculate cost estimates (WatsonX pricing varies by model)
            input_cost_per_token = 0.50 / 1000000   # Estimated $0.50 per million input tokens
            output_cost_per_token = 1.50 / 1000000  # Estimated $1.50 per million output tokens
            
            input_cost = input_tokens * input_cost_per_token
            output_cost = output_tokens * output_cost_per_token
            total_cost = input_cost + output_cost
            
            metadata.update({
                "estimated_cost_usd": round(total_cost, 6),
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
            })
            
            print(f"🔍 DEBUG: Calculated costs - Input: ${input_cost:.6f}, Output: ${output_cost:.6f}, Total: ${total_cost:.6f}")
            
            # Extract stop reason
            if 'stop_reason' in result:
                metadata["stop_reason"] = result['stop_reason']
        
        # Extract system warnings/info
        if 'system' in response_dict:
            metadata["system_info"] = response_dict['system']
        
        print(f"🔍 DEBUG: Final metadata: {metadata}")
        return metadata
    
    @property
    def model_name(self) -> str:
        return f"WatsonX ({self.model_id})"
    
    @property
    def required_env_vars(self) -> list:
        return ["WATSONX_API_KEY", "WATSONX_PROJECT_ID"]

