"""
LLM Model Optimizer
Automatically adjusts settings based on model type for better JSON output
"""
import os
from typing import Dict, Optional


class ModelOptimizer:
    """Optimize LLM settings for different models"""
    
    # Recommended settings for Mistral models
    MODEL_CONFIGS = {
        "mistral": {
            "temperature": 0.1,
            "max_tokens": 4096,
            "top_p": 0.95,
            "notes": "Mistral works best with very low temperature (0.1) for consistent JSON output"
        },
        "mistral-nemo": {
            "temperature": 0.1,
            "max_tokens": 4096,
            "top_p": 0.95,
            "notes": "Mistral Nemo is the best variant - excellent at following structured output instructions"
        },
        "mistral-small": {
            "temperature": 0.1,
            "max_tokens": 2048,
            "top_p": 0.9,
            "notes": "Smaller Mistral variant - use lower max_tokens to avoid hallucination"
        },
    }
    
    @classmethod
    def detect_model_type(cls, model_name: str) -> Optional[str]:
        """Detect Mistral model variant from model name"""
        model_lower = model_name.lower()
        
        if "mistral-nemo" in model_lower or "mistralnemo" in model_lower:
            return "mistral-nemo"
        elif "mistral-small" in model_lower or "mistralsmall" in model_lower:
            return "mistral-small"
        elif "mistral" in model_lower:
            return "mistral"
        
        return None
    
    @classmethod
    def get_optimized_config(cls, model_name: str) -> Dict:
        """Get optimized configuration for a model"""
        model_type = cls.detect_model_type(model_name)
        
        if model_type and model_type in cls.MODEL_CONFIGS:
            config = cls.MODEL_CONFIGS[model_type].copy()
            config["detected_type"] = model_type
            return config
        
        # Default config for Mistral if variant not detected
        return {
            "temperature": 0.1,
            "max_tokens": 4096,
            "top_p": 0.95,
            "detected_type": "mistral-default",
            "notes": "Using optimized Mistral default settings - temperature 0.1 for consistent JSON"
        }
    
    @classmethod
    def print_recommendations(cls, model_name: str):
        """Print recommendations for a model"""
        config = cls.get_optimized_config(model_name)
        
        print(f"\nOptimized Settings for: {model_name}")
        print("="*60)
        print(f"Detected Type: {config['detected_type']}")
        print(f"Temperature: {config['temperature']}")
        print(f"Max Tokens: {config['max_tokens']}")
        print(f"Top P: {config.get('top_p', 'N/A')}")
        print(f"\nNotes: {config.get('notes', 'No specific notes')}")
        print("="*60)
        
        print("\nAdd to your .env file:")
        print(f"LLM_TEMPERATURE={config['temperature']}")
        print(f"LLM_MAX_TOKENS={config['max_tokens']}")
    
    @classmethod
    def apply_to_llm(cls, llm, model_name: str):
        """Apply optimized settings to LLM instance"""
        config = cls.get_optimized_config(model_name)
        
        try:
            if hasattr(llm, 'temperature'):
                llm.temperature = config['temperature']
            if hasattr(llm, 'max_tokens'):
                llm.max_tokens = config['max_tokens']
            if hasattr(llm, 'top_p'):
                llm.top_p = config.get('top_p', 0.95)
            
            print(f"✅ Applied optimized settings to LLM")
            return True
        except Exception as e:
            print(f"⚠️  Could not apply settings: {e}")
            return False


def main():
    """Test the optimizer"""
    import sys
    
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
    else:
        # Try to get from environment
        from config.settings import LLM_PROVIDER, OLLAMA_MODEL, CHATGPT_MODEL
        
        if LLM_PROVIDER == "ollama":
            model_name = OLLAMA_MODEL
        elif LLM_PROVIDER == "chatgpt":
            model_name = CHATGPT_MODEL
        else:
            print("Usage: python model_optimizer.py <model_name>")
            print("Or set LLM_PROVIDER in .env")
            return
    
    ModelOptimizer.print_recommendations(model_name)


if __name__ == "__main__":
    main()
