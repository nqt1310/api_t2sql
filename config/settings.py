

import os
import dotenv

dotenv.load_dotenv()

# ===== DATABASE =====
DB_TYPE = os.getenv("DB_TYPE", "postgres")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH")
DATAMODEL_PATH = os.getenv("DATAMODEL_PATH")

# ===== OUTPUT DATABASE =====
OUTPUT_DB_TYPE = os.getenv("OUTPUT_DB_TYPE", "postgres")
OUTPUT_DB_NAME = os.getenv("OUTPUT_DB_NAME", "postgres")
OUTPUT_DB_USER = os.getenv("OUTPUT_DB_USER", "postgres")
OUTPUT_DB_PASSWORD = os.getenv("OUTPUT_DB_PASSWORD", "thangcoi123")
OUTPUT_DB_HOST = os.getenv("OUTPUT_DB_HOST", "host.docker.internal")
META_STORAGE = os.getenv("META_STORAGE", "postgres")

# ===== EMBEDDING & VECTOR STORE =====
CHROMA_PATH = os.getenv("CHROMA_PATH", "default_chroma_path")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "default_embedding_model")
VECTOR_MODE = os.getenv("VECTOR_MODE", "default_vector_mode")

# ===== LLM CONFIGURATION =====
# Choose LLM provider: 'ollama', 'chatgpt', or 'vllm'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "default_llm_model")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = os.getenv("LLM_MAX_TOKENS")
if LLM_MAX_TOKENS:
    LLM_MAX_TOKENS = int(LLM_MAX_TOKENS)

# ===== OLLAMA CONFIGURATION =====
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral-nemo:latest")

# ===== CHATGPT CONFIGURATION =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHATGPT_MODEL = os.getenv("CHATGPT_MODEL", "gpt-4")

# ===== VLLM CONFIGURATION =====
VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "meta-llama/Llama-2-7b-hf")