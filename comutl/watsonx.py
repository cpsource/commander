"""
WatsonX LLM implementation
"""

from typing import Dict, Tuple
from .base_llm import BaseLLM

try:
    from ibm_watsonx_ai.foundation_models import Model
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False


class WatsonxLLM(BaseLLM):
    """WatsonX LLM implementation using IBM's WatsonX AI"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not WATSONX_AVAILABLE:
            raise ImportError("ibm-watsonx-ai is required for WatsonX. Install with: pip install ibm-watsonx-ai")
        
        # Default model and parameters
        self.model_id = kwargs.get('model', 'ibm/granite-13b-chat-v2')
        self.project_id = kwargs.get('project_id', None)
        self.url = kwargs.get('url', 'https://us-south.ml.cloud.ibm.com')
        
        # Check for required project_id
        if not self.project_id:
            raise ValueError("project_id is required for WatsonX")
        
        # Generation parameters
        self.generation_params = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: kwargs.get('max_tokens', 1000),
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
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Process files using WatsonX AI"""
        prompt = self.create_prompt(instructions, files_data)
        
        # Add system message to prompt for WatsonX
        full_prompt = f"""You are an expert developer who carefully modifies code according to instructions.

{prompt}"""
        
        try:
            response = self.model.generate_text(prompt=full_prompt)
            return response
            
        except Exception as e:
            print(f"Error communicating with WatsonX: {e}")
            return ""
    
    @property
    def model_name(self) -> str:
        return "WatsonX"
    
    @property
    def required_env_vars(self) -> list:
        return ["WATSONX_API_KEY", "WATSONX_PROJECT_ID"]

