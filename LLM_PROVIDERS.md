# LLM Providers Configuration Guide

This project supports three different LLM providers for SQL query generation:

## Supported Providers

### 1. **Ollama** (Default)
- **Type**: Local LLM inference server
- **Setup**: Download and run Ollama from [ollama.com](https://ollama.com)
- **Best For**: Local development, privacy-focused use cases
- **Cost**: Free (runs locally)

#### Installation:
```bash
# Download from https://ollama.com
# Or use Docker:
docker run -d --name ollama -p 11434:11434 ollama/ollama

# Pull a model
ollama pull mistral-nemo:latest
```

#### Configuration (.env):
```env
LLM_PROVIDER=ollama
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=mistral-nemo:latest
```

#### Usage:
```python
from base.llm_factory import LLMFactory

llm = LLMFactory.create_llm(
    provider="ollama",
    model_name="mistral-nemo:latest",
    api_url="http://localhost:11434"
)
```

---

### 2. **ChatGPT (OpenAI)**
- **Type**: Cloud-based API (requires internet)
- **Setup**: Get API key from [OpenAI Platform](https://platform.openai.com/account/api-keys)
- **Best For**: Production use, high-quality responses
- **Cost**: Pay-per-use (see [pricing](https://openai.com/pricing))

#### Installation:
```bash
pip install langchain-openai
```

#### Configuration (.env):
```env
LLM_PROVIDER=chatgpt
OPENAI_API_KEY=sk-your-api-key-here
CHATGPT_MODEL=gpt-4
```

Available models:
- `gpt-4` - Most capable, recommended for complex queries
- `gpt-4-turbo` - Faster, good balance
- `gpt-3.5-turbo` - Most affordable, faster
- `gpt-4o` - Latest optimized model

#### Usage:
```python
from base.llm_factory import LLMFactory

llm = LLMFactory.create_llm(
    provider="chatgpt",
    model_name="gpt-4",
    api_key="sk-your-api-key-here"
)
```

---

### 3. **vLLM**
- **Type**: High-performance local LLM serving
- **Setup**: Install vLLM and run inference server
- **Best For**: Local deployment, speed-focused, various open models
- **Cost**: Free (runs locally)

#### Installation:
```bash
pip install vllm

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-hf \
    --port 8000
```

#### Or using Docker:
```bash
docker run --rm --gpus all \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-2-7b-hf
```

#### Configuration (.env):
```env
LLM_PROVIDER=vllm
VLLM_API_URL=http://localhost:8000/v1
VLLM_MODEL=meta-llama/Llama-2-7b-hf
```

Available models:
- `meta-llama/Llama-2-7b-hf` - Recommended for most use cases
- `meta-llama/Llama-2-13b-hf` - Larger, better quality
- `mistralai/Mistral-7B-v0.1` - Efficient and fast

#### Usage:
```python
from base.llm_factory import LLMFactory

llm = LLMFactory.create_llm(
    provider="vllm",
    model_name="meta-llama/Llama-2-7b-hf",
    api_url="http://localhost:8000/v1"
)
```

---

## Quick Start Guide

### Step 1: Configure Provider

Edit your `.env` file:

```env
# Choose one provider
LLM_PROVIDER=ollama  # or 'chatgpt' or 'vllm'

# Set temperature (0.0-1.0, lower = more deterministic)
LLM_TEMPERATURE=0.7

# Optional: Set max tokens
# LLM_MAX_TOKENS=2000
```

### Step 2: Set Provider-Specific Config

**For Ollama:**
```env
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=mistral-nemo:latest
```

**For ChatGPT:**
```env
OPENAI_API_KEY=sk-your-key-here
CHATGPT_MODEL=gpt-4
```

**For vLLM:**
```env
VLLM_API_URL=http://localhost:8000/v1
VLLM_MODEL=meta-llama/Llama-2-7b-hf
```

### Step 3: Start Your Provider

**Ollama:**
```bash
ollama serve
# In another terminal:
ollama pull mistral-nemo:latest
```

**ChatGPT:**
No setup needed, just set your API key.

**vLLM:**
```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-hf \
    --port 8000
```

### Step 4: Run Application

```bash
python main_mcp.py
```

The application will automatically initialize the LLM based on your `LLM_PROVIDER` setting.

---

## Comparing Providers

| Feature | Ollama | ChatGPT | vLLM |
|---------|--------|---------|------|
| Local/Cloud | Local | Cloud | Local |
| Setup Difficulty | Easy | Very Easy | Medium |
| Cost | Free | Pay-per-use | Free |
| Internet Required | No | Yes | No |
| Quality | Good | Excellent | Good |
| Speed | Fast | Medium | Very Fast |
| Privacy | Excellent | None | Excellent |
| GPU Required | Recommended | No | Yes |

---

## Troubleshooting

### Ollama
```
Error: Failed to connect to Ollama at http://localhost:11434
→ Make sure Ollama is running with: ollama serve
→ Check that it's accessible on the specified port
```

### ChatGPT
```
Error: Invalid API key
→ Get a valid API key from: https://platform.openai.com/account/api-keys
→ Make sure OPENAI_API_KEY environment variable is set correctly
→ Check you have billing enabled in your OpenAI account
```

### vLLM
```
Error: Failed to connect to vLLM at http://localhost:8000/v1
→ Make sure vLLM server is running on the specified port
→ Check your GPU has enough VRAM for the model
→ Try a smaller model if you have memory issues
```

---

## Advanced Configuration

### Custom Temperature & Max Tokens

```env
LLM_TEMPERATURE=0.5       # Lower = more deterministic (0.0-1.0)
LLM_MAX_TOKENS=1000       # Max output length
```

### Running Multiple Providers

You can have multiple providers configured at once and switch by changing `LLM_PROVIDER`:

```env
# Main setting (what to use)
LLM_PROVIDER=ollama

# Ollama config (always have this)
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=mistral-nemo:latest

# ChatGPT config (optional backup)
OPENAI_API_KEY=sk-your-key-here
CHATGPT_MODEL=gpt-4

# vLLM config (optional backup)
VLLM_API_URL=http://localhost:8000/v1
VLLM_MODEL=meta-llama/Llama-2-7b-hf
```

Then switch providers by changing just the `LLM_PROVIDER` line.

---

## Examples

See `llm_provider_examples.py` for complete working examples:

```bash
python llm_provider_examples.py
```

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Ensure your provider is running and accessible
4. Try the example script: `python llm_provider_examples.py`
