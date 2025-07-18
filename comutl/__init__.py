"""
comutl - Commander Utility Library
A modular library for different LLM providers
"""

from .base_llm import BaseLLM
from .gemini import GeminiLLM
from .claude import ClaudeLLM
from .chatgpt import ChatGPTLLM
from .xai import XaiLLM
from .watsonx import WatsonxLLM

__version__ = "1.0.0"
__all__ = ["BaseLLM", "GeminiLLM", "ClaudeLLM", "ChatGPTLLM", "XaiLLM", "WatsonxLLM"]

# Model registry for easy lookup
MODEL_REGISTRY = {
    "gemini": GeminiLLM,
    "claude": ClaudeLLM,
    "chatgpt": ChatGPTLLM,
    "xai": XaiLLM,
    "watsonx": WatsonxLLM,
}

def get_llm_class(model_name: str):
    """Get the LLM class for a given model name"""
    if model_name not in MODEL_REGISTRY:
        available_models = ", ".join(MODEL_REGISTRY.keys())
        raise ValueError(f"Model '{model_name}' not found. Available models: {available_models}")
    
    return MODEL_REGISTRY[model_name]

