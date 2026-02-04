"""
LLM Provider Configuration Guide

This example shows how to configure and use different LLM providers
with the SQL Agent system.
"""

from base.llm_factory import LLMFactory, get_llm_provider_info
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_provider_info():
    """Print available LLM providers and their configurations"""
    print("\n" + "="*80)
    print("AVAILABLE LLM PROVIDERS")
    print("="*80)
    
    providers_info = get_llm_provider_info()
    
    for provider_name, info in providers_info.items():
        print(f"\n{info['name']} ({provider_name})")
        print("-" * 40)
        print(f"Description: {info['description']}")
        print(f"Required params: {', '.join(info['required_params'])}")
        print(f"Optional params: {', '.join(info['optional_params'])}")
        print(f"Default model: {info['default_model']}")
        if 'default_api_url' in info:
            print(f"Default API URL: {info['default_api_url']}")
        if 'note' in info:
            print(f"Note: {info['note']}")


def example_ollama():
    """Example: Using Ollama LLM provider"""
    print("\n" + "="*80)
    print("EXAMPLE 1: OLLAMA")
    print("="*80)
    print("""
    # Make sure Ollama is running:
    # $ ollama serve
    
    # In .env or code:
    LLM_PROVIDER=ollama
    OLLAMA_API_URL=http://localhost:11434
    OLLAMA_MODEL=mistral-nemo:latest
    """)
    
    try:
        llm = LLMFactory.create_llm(
            provider="ollama",
            model_name="mistral-nemo:latest",
            api_url="http://localhost:11434",
            temperature=0.7
        )
        print("\n✓ Ollama LLM initialized successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("Make sure Ollama is running on http://localhost:11434")


def example_chatgpt():
    """Example: Using ChatGPT (OpenAI) LLM provider"""
    print("\n" + "="*80)
    print("EXAMPLE 2: CHATGPT (OpenAI)")
    print("="*80)
    print("""
    # Get your API key from: https://platform.openai.com/account/api-keys
    
    # In .env:
    LLM_PROVIDER=chatgpt
    OPENAI_API_KEY=sk-your-api-key-here
    CHATGPT_MODEL=gpt-4
    # or: gpt-4-turbo, gpt-3.5-turbo
    """)
    
    try:
        llm = LLMFactory.create_llm(
            provider="chatgpt",
            model_name="gpt-4",
            api_key="sk-your-api-key-here",  # Replace with real key
            temperature=0.7
        )
        print("\n✓ ChatGPT LLM initialized successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("Make sure you have a valid OpenAI API key set in OPENAI_API_KEY")


def example_vllm():
    """Example: Using vLLM provider"""
    print("\n" + "="*80)
    print("EXAMPLE 3: VLLM")
    print("="*80)
    print("""
    # Make sure vLLM server is running:
    # $ python -m vllm.entrypoints.openai.api_server \\
    #     --model meta-llama/Llama-2-7b-hf \\
    #     --port 8000
    
    # In .env:
    LLM_PROVIDER=vllm
    VLLM_API_URL=http://localhost:8000/v1
    VLLM_MODEL=meta-llama/Llama-2-7b-hf
    """)
    
    try:
        llm = LLMFactory.create_llm(
            provider="vllm",
            model_name="meta-llama/Llama-2-7b-hf",
            api_url="http://localhost:8000/v1",
            temperature=0.7
        )
        print("\n✓ vLLM initialized successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("Make sure vLLM server is running on http://localhost:8000/v1")


def main():
    """Run all examples"""
    print_provider_info()
    
    print("\n" + "="*80)
    print("SETUP INSTRUCTIONS")
    print("="*80)
    
    example_ollama()
    example_chatgpt()
    example_vllm()
    
    print("\n" + "="*80)
    print("SWITCHING PROVIDERS")
    print("="*80)
    print("""
    To switch between providers, simply change the LLM_PROVIDER in .env:
    
    1. For Ollama (default):
       LLM_PROVIDER=ollama
       
    2. For ChatGPT:
       LLM_PROVIDER=chatgpt
       
    3. For vLLM:
       LLM_PROVIDER=vllm
    
    Then set the corresponding provider-specific configuration variables
    as shown in the examples above.
    """)


if __name__ == "__main__":
    main()
