"""
LLM Factory - Initialize different LLM providers (Ollama, ChatGPT, vLLM)
"""
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    OLLAMA = "ollama"
    CHATGPT = "chatgpt"
    VLLM = "vllm"


class LLMFactory:
    """Factory for creating LLM instances based on provider type"""
    
    @staticmethod
    def create_llm(
        provider: str,
        model_name: str,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Create LLM instance based on provider
        
        Args:
            provider: LLM provider ('ollama', 'chatgpt', 'vllm')
            model_name: Model name to use
            api_key: API key (required for ChatGPT)
            api_url: API URL (required for Ollama and vLLM)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments
            
        Returns:
            LLM instance compatible with LangChain
            
        Raises:
            ValueError: If provider is not supported or required params are missing
        """
        provider = provider.lower()
        
        if provider == LLMProvider.OLLAMA.value:
            return LLMFactory._create_ollama(model_name, api_url, temperature, max_tokens, **kwargs)
        
        elif provider == LLMProvider.CHATGPT.value:
            return LLMFactory._create_chatgpt(model_name, api_key, temperature, max_tokens, **kwargs)
        
        elif provider == LLMProvider.VLLM.value:
            return LLMFactory._create_vllm(model_name, api_url, temperature, max_tokens, **kwargs)
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {', '.join([p.value for p in LLMProvider])}")
    
    @staticmethod
    def _create_ollama(model_name: str, api_url: str, temperature: float, max_tokens: Optional[int], **kwargs):
        """Create Ollama LLM instance"""
        if not api_url:
            raise ValueError("api_url is required for Ollama provider")
        
        try:
            from langchain_community.llms import Ollama
            
            logger.info(f"Initializing Ollama LLM: {model_name} at {api_url}")
            
            llm_kwargs = {
                "model": model_name,
                "base_url": api_url,
                "temperature": temperature,
            }
            
            if max_tokens:
                llm_kwargs["num_predict"] = max_tokens
            
            llm_kwargs.update(kwargs)
            
            return Ollama(**llm_kwargs)
        
        except ImportError as e:
            raise ImportError("Failed to import Ollama from langchain_community") from e
    
    @staticmethod
    def _create_chatgpt(model_name: str, api_key: str, temperature: float, max_tokens: Optional[int], **kwargs):
        """Create ChatGPT (OpenAI) LLM instance"""
        if not api_key:
            raise ValueError("api_key is required for ChatGPT provider")
        
        try:
            from langchain_openai import ChatOpenAI
            
            logger.info(f"Initializing ChatGPT LLM: {model_name}")
            
            llm_kwargs = {
                "model": model_name,
                "api_key": api_key,
                "temperature": temperature,
            }
            
            if max_tokens:
                llm_kwargs["max_tokens"] = max_tokens
            
            llm_kwargs.update(kwargs)
            
            return ChatOpenAI(**llm_kwargs)
        
        except ImportError as e:
            raise ImportError("Failed to import ChatOpenAI from langchain_openai. Install with: pip install langchain-openai") from e
    
    @staticmethod
    def _create_vllm(model_name: str, api_url: str, temperature: float, max_tokens: Optional[int], **kwargs):
        """Create vLLM LLM instance"""
        if not api_url:
            raise ValueError("api_url is required for vLLM provider")
        
        try:
            from langchain_community.llms import VLLMOpenAI
            
            logger.info(f"Initializing vLLM: {model_name} at {api_url}")
            
            llm_kwargs = {
                "model": model_name,
                "openai_api_base": api_url,
                "openai_api_key": "EMPTY",  # vLLM usually doesn't require real API key
                "temperature": temperature,
            }
            
            if max_tokens:
                llm_kwargs["max_tokens"] = max_tokens
            
            llm_kwargs.update(kwargs)
            
            return VLLMOpenAI(**llm_kwargs)
        
        except ImportError as e:
            raise ImportError("Failed to import VLLMOpenAI from langchain_community. Install with: pip install langchain") from e


def get_llm_provider_info() -> dict:
    """Get information about available LLM providers"""
    return {
        "ollama": {
            "name": "Ollama",
            "description": "Local LLM inference server",
            "required_params": ["api_url", "model_name"],
            "optional_params": ["temperature", "max_tokens"],
            "default_model": "mistral-nemo:latest",
            "default_api_url": "http://localhost:11434"
        },
        "chatgpt": {
            "name": "OpenAI ChatGPT",
            "description": "OpenAI's GPT models via API",
            "required_params": ["api_key", "model_name"],
            "optional_params": ["temperature", "max_tokens"],
            "default_model": "gpt-4",
            "note": "Requires valid OpenAI API key"
        },
        "vllm": {
            "name": "vLLM",
            "description": "High-throughput and memory-efficient LLM serving engine",
            "required_params": ["api_url", "model_name"],
            "optional_params": ["temperature", "max_tokens"],
            "default_model": "meta-llama/Llama-2-7b-hf",
            "default_api_url": "http://localhost:8000/v1"
        }
    }
