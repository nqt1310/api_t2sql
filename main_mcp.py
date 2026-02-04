import uvicorn
import torch
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from base.db import DBConnection
from base.vector_store_manager import DataLoader
from base.vector_store_manager import VectorStoreManager
from base.llm_factory import LLMFactory, get_llm_provider_info
import mcp.server as mcp_server
from base.db import DBConnection
from base.queries import DBQuery
from base.vector_store_manager import VectorStoreManager
from base.rag_core import RAGSQLPipeline
from base.agent_core import SQLAgent
from base.agent_runner import AgentOrchestrator
from base.prompt_temp import final_prompt, final_prompt_output
from config.settings import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = DBConnection(
         db_type=DB_TYPE,
        db_name=DB_NAME,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
       port=DB_PORT,
    )

df = db.exec_query_df(DBQuery.get_full_meta())
dataloader = DataLoader(df)

# ===== DB =====
metadata_db = DBConnection(DB_TYPE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
_, cursor = metadata_db.get_raw_cursor()

output_db = DBConnection(
    OUTPUT_DB_TYPE,
    OUTPUT_DB_NAME,
    OUTPUT_DB_USER,
    OUTPUT_DB_PASSWORD,
    OUTPUT_DB_HOST,
    5432,
)
output_conn = output_db.engine

# ===== MODELS =====
embedding = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
)

# ===== LLM INITIALIZATION =====
logger.info(f"Initializing LLM with provider: {LLM_PROVIDER}")

try:
    if LLM_PROVIDER == "ollama":
        llm = LLMFactory.create_llm(
            provider="ollama",
            model_name=OLLAMA_MODEL,
            api_url=OLLAMA_API_URL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
        logger.info(f"✓ Ollama LLM initialized: {OLLAMA_MODEL}")
        
    elif LLM_PROVIDER == "chatgpt":
        llm = LLMFactory.create_llm(
            provider="chatgpt",
            model_name=CHATGPT_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
        logger.info(f"✓ ChatGPT LLM initialized: {CHATGPT_MODEL}")
        
    elif LLM_PROVIDER == "vllm":
        llm = LLMFactory.create_llm(
            provider="vllm",
            model_name=VLLM_MODEL,
            api_url=VLLM_API_URL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
        logger.info(f"✓ vLLM initialized: {VLLM_MODEL}")
        
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
        
except Exception as e:
    logger.error(f"Failed to initialize LLM: {str(e)}")
    logger.error("Available providers:")
    for provider, info in get_llm_provider_info().items():
        logger.error(f"  - {provider}: {info['description']}")
    raise

# ===== VECTOR STORE =====
vector_manager = VectorStoreManager(
    persist_dir=CHROMA_PATH,
    embedding=embedding,
    documents_loader=dataloader
)

retriever = vector_manager.get_retriever(
    k=20
)

# ===== PIPELINE =====
pipeline = RAGSQLPipeline(
    llm=llm,
    retriever=retriever,
    datamodel_path=DATAMODEL_PATH,
    backend_db=("PostgreSQL",),
    cursor=cursor,
    output_conn=output_conn,
    final_prompt=final_prompt,
    final_prompt_output=final_prompt_output,
    meta_storage=META_STORAGE
)

# ===== AGENT ORCHESTRATOR =====
agent_orchestrator = AgentOrchestrator(pipeline, llm)

mcp_server.rag_pipeline = pipeline
mcp_server.agent_orchestrator = agent_orchestrator

mcp_server.inject_agent(agent_orchestrator)  # Inject agent into server

if __name__ == "__main__":
    print("=" * 60)
    print("SQL AI AGENT STARTED")
    print("=" * 60)
    print(f"Available Tools: {len(agent_orchestrator.get_available_tools())}")
    for tool in agent_orchestrator.get_available_tools():
        print(f"  - {tool['name']}: {tool['description']}")
    print("=" * 60)
    
    uvicorn.run(mcp_server.app, host="0.0.0.0", port=8000)


