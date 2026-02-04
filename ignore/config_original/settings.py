

import os
import dotenv

dotenv.load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "postgres")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH")
DATAMODEL_PATH = os.getenv("DATAMODEL_PATH")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
CHROMA_PATH = os.getenv("CHROMA_PATH", "default_chroma_path")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "default_embedding_model")
LLM_MODEL = os.getenv("LLM_MODEL", "default_llm_model")
VECTOR_MODE = os.getenv("VECTOR_MODE", "default_vector_mode")
META_STORAGE = os.getenv("META_STORAGE", "postgres")
OUTPUT_DB_TYPE = os.getenv("OUTPUT_DB_TYPE", "postgres")
OUTPUT_DB_NAME = os.getenv("OUTPUT_DB_NAME", "postgres")
OUTPUT_DB_USER = os.getenv("OUTPUT_DB_USER", "postgres")
OUTPUT_DB_PASSWORD = os.getenv("OUTPUT_DB_PASSWORD", "thangcoi123")
OUTPUT_DB_HOST = os.getenv("OUTPUT_DB_HOST", "host.docker.internal")