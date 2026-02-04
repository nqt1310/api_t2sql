import json
import os
import shutil
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
import torch
import unidecode
from config.settings import *

# Setup logging

load_dotenv()




def create_connection(meta_storage):
    if meta_storage == "postgres":
        engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
        return engine.connect()
    elif meta_storage == "oracle":
        engine = create_engine(f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:1521/{DB_NAME}")
        return engine.connect()
    else:
        raise ValueError("Unsupported META_STORAGE type.")

def create_output_connection():
    if OUTPUT_DB_TYPE == "postgres":
        engine = create_engine(f"postgresql+psycopg2://{OUTPUT_DB_USER}:{OUTPUT_DB_PASSWORD}@{OUTPUT_DB_HOST}/{OUTPUT_DB_NAME}")
        return engine.connect()
    elif OUTPUT_DB_TYPE == "oracle":
        engine = create_engine(f"oracle+oracledb://{OUTPUT_DB_USER}:{OUTPUT_DB_PASSWORD}@{OUTPUT_DB_HOST}:1521/{OUTPUT_DB_NAME}")
        return engine.connect()
    else:
        raise ValueError("Unsupported OUTPUT_DB_TYPE.")



conn = create_connection(META_STORAGE)
cursor = conn.connection.cursor() if META_STORAGE == "postgres" else conn.cursor()

output_conn = create_output_connection()

def get_backenddb(cursor):
    if META_STORAGE == "postgres":
        cursor.execute("SELECT DISTINCT backenddb FROM public.metadata_")
    elif META_STORAGE == "oracle":
        cursor.execute("SELECT DISTINCT backenddb FROM metadata_")
    result = cursor.fetchall()
    return result[0] if result else 'PostgreSQL'

backend_db = get_backenddb(cursor)


def fetch_metadata(conn):
    query = "SELECT * FROM public.metadata_" if META_STORAGE == "postgres" else "SELECT * FROM metadata_"
    df = pd.read_sql_query(query, conn)
    return df

df = fetch_metadata(conn)
df["combined_content"] = "Tên bảng: " + df["table_name"] + "\n" + "Mô tả: " + df["table_description"] + "\n"
metadata_loader = DataFrameLoader(df[["table_name", "combined_content"]].drop_duplicates(), page_content_column="combined_content")
documents = metadata_loader.load()

if not documents:
    raise ValueError("No documents found to initialize the vectorstore.")

embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"})
logger.info("Using device: %s", "cuda" if torch.cuda.is_available() else "cpu")


def init_vectorstore(documents, embedding_model, persist_directory, mode="truncate"):
    index_path = os.path.join(persist_directory, "faiss_index")

    if mode == "truncate":
        if os.path.exists(index_path):
            shutil.rmtree(index_path)
        vectorstore = FAISS.from_documents(documents, embedding_model)
        vectorstore.save_local(index_path)
        return vectorstore

    elif mode == "update":
        if os.path.exists(index_path):
            vectorstore = FAISS.load_local(
                index_path,
                embedding_model,
                allow_dangerous_deserialization=True
            )
            vectorstore.add_documents(documents)
            vectorstore.save_local(index_path)
            return vectorstore
        else:
            logger.warning("FAISS index not found at %s. Skipping update.", index_path)
            return False

    else:
        raise ValueError("Only 2 modes are supported: 'truncate' and 'update'.")
    

    
vectorstore = init_vectorstore(documents, embedding_model, CHROMA_PATH, mode=VECTOR_MODE)
retriever = vectorstore.as_retriever(search_kwargs={"k": 20})
llm = Ollama(model=LLM_MODEL, base_url=OLLAMA_API_URL)


response_schemas = [
    ResponseSchema(
        name="Danh sach bang lien quan",
        description="Danh sách các bảng liên quan đến yêu cầu nghiệp vụ, là một list Python. Không bao gồm mô tả hoặc thông tin khác."
    )
]
parser = StructuredOutputParser.from_response_schemas(response_schemas)
chat_prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an assistant in understanding business requests and table metadata."
    ),
    (
        "user",
        "The metadata is provided in the following format for each entry:\n\n"
        "table_name: table_description\n\n"
        "For example:\n"
        "SMY_BRANCH_MTH: Bảng chứa thông tin chi nhánh của MB, tại ngày cuối tháng\n\n"
        "Based on the metadata above, identify all tables that are relevant to the request.\n\n"
        "If metadata is duplicated, return only the tables suitable for the business request.\n"
        "Understand carefully the request then get the related tables from the metadata.\n\n"
        "Output format should be exactly like this:\n"
        "{format_instructions}\n"
        "Do not include any descriptions, explanations, or any other information apart from the table names.\n"
        "Do not return any table not listed in the metadata.\n"
        "Metadata:\n{context}\n"
        "Question:\n{question}"
    )
])
final_prompt = chat_prompt_template.partial(format_instructions=parser.get_format_instructions())


response_schemas_output = [
    ResponseSchema(
        name="Cau lenh SQL theo yeu cau nghiep vu",
        description="SQL Select Statements used to retrieve the data relevant to the business request. The SQL should be syntactically correct and only use the columns provided in the metadata. Do not include any other information or explanations.",
    )
]
parser_output = StructuredOutputParser.from_response_schemas(response_schemas_output)
chat_prompt_template_output = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an assistant in understanding business requests and table metadata."
    ),
    (
        "user",
        "You are a {backend_db} SQL expert. Given the following table metadata and a business request, understand them and generate a syntactically correct SELECT query "
        "to retrieve data relevant to the question. Only use the columns provided in the metadata below; do not query for all columns or include "
        "columns not listed. Use only SELECT queries; do not use "
        "INSERT, UPDATE, DELETE, CREATE, ALTER, or DROP commands.\n\n"
        "The information between the tables, metadata and datamodel is:\n\n"
        "Metadata:\n{full_input}\n\n"
        "The keys relationship between the tables are in the Data Model related to the tables in json: {datamodel}\n"
        "My Question/Business Request is: {query_text}\n\n"
        "Generate the SQL to answer the question. The SQL should be a valid query that can be run on the database.\n\n"
        "If you cannot answer the question, return 'I cannot answer this question. Do not return anything out of the given context in meta, datamodel.'\n"
        "The query MUST include the SCHEMA_NAME of the tables.\n"
        "The table MUST be presented like SCHEMA_NAME.TABLE_NAME.\n"
        "Output format should be exactly like this:\n"
        "{format_instructions}\n"
        "Do not include any descriptions, explanations, or any other information apart from the table names.\n"
        "Do not return any table not listed in the metadata.\n"
    )
])
final_prompt_output = chat_prompt_template_output.partial(format_instructions=parser_output.get_format_instructions())


def get_related_table_metadata(query_text: str):
    retrieved_docs = retriever.invoke(query_text)
    context = "\n".join(doc.page_content for doc in retrieved_docs)
    prompt = final_prompt.format(context=context, question=query_text)
    raw_response = llm.invoke(prompt)
    parsed_result = parser.parse(unidecode.unidecode(raw_response))
    related_tables = parsed_result["Danh sach bang lien quan"]

    cursor.execute(
        f"""
                SELECT TABLE_NAME, TABLE_DESCRIPTION, COLUMN_NAME, DATA_TYPE, DOMAIN, PK, NULLABLE, COLUMN_DESCRIPTION, NOTE, ORS_MAP, BACKENDDB, SCHEMA_NAME
        FROM {"public.metadata_" if META_STORAGE == "postgres" else "metadata_"}
        WHERE TABLE_NAME IN %s
        """,
        (tuple(related_tables),)
    )
    logger.debug("Các bảng có liên quan: %s", related_tables)
    return cursor.fetchall()


def generate_sql_query(query_text: str) -> str:
    table_metadata_list = get_related_table_metadata(query_text)
    if not table_metadata_list:
        return ""

    with open(DATAMODEL_PATH, "r", encoding="utf-8") as f:
        datamodel = json.load(f)

    full_input = ""
    for row in table_metadata_list:
        (table_name, table_description, column_name, data_type, domain, pk,
         nullable, column_description, note, ors_map, backenddb, schema_name) = row
        full_input += (
            f"Table: {table_name}\n"
            f"Description: {table_description}\n"
            f"Column: {column_name}, Data Type: {data_type}, Domain: {domain}, "
            f"Column Description: {column_description}, Note: {note}, Schema: {schema_name}\n\n"
        )

    prompt_text = final_prompt_output.format(
        full_input=full_input,
        datamodel=json.dumps(datamodel, ensure_ascii=False, indent=2),
        query_text=query_text,
        backend_db=backend_db[0]
    )

    try:
        sql_response = llm.invoke(prompt_text)
        parsed_sql = parser_output.parse(unidecode.unidecode(sql_response))
        return parsed_sql["Cau lenh SQL theo yeu cau nghiep vu"]
    except Exception as e:
        logger.error("Failed to parse SQL response: %s", e)
        return "I cannot answer this question."
    
def execute_query(query: str):
    try:
        df = pd.read_sql_query(query, output_conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error("Error executing query: %s", e)
        return {"error": str(e)}