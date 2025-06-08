import json
import os
# import re
import shutil
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
import oracledb
import logging
import torch

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

load_dotenv()


# Load environment variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH")
DATAMODEL_PATH = os.getenv("DATAMODEL_PATH")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
CHROMA_PATH = os.getenv("CHROMA_PATH")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
LLM_MODEL = os.getenv("LLM_MODEL")
VECTOR_MODE = os.getenv("VECTOR_MODE")
META_STORAGE = os.getenv("META_STORAGE")
DSN = f"{DB_HOST}:1521/{DB_NAME}"




def create_connection(meta_storage):
    if meta_storage == "postgres":
        return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
    elif meta_storage == "oracle":
        return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DSN)
    else:
        raise ValueError("Unsupported META_STORAGE type.")

def fetch_metadata(conn):
    query = "SELECT * FROM metadata_"
    df = pd.read_sql_query(query, conn)
    return df

conn = create_connection(META_STORAGE)
cursor = conn.cursor()

def get_backenddb(cursor):
    cursor.execute("SELECT DISTINCT backenddb FROM public.metadata_")
    result = cursor.fetchall()
    return result[0] if result else 'PostgreSQL'

backend_db = get_backenddb(cursor)

df = fetch_metadata(conn)
df["combined_content"] = "Tên bảng: " + df["table_name"] + "\n" + "Mô tả: " + df["table_description"] + "\n"
metadata_loader = DataFrameLoader(df[["table_name", "combined_content"]].drop_duplicates(), page_content_column="combined_content")
documents = metadata_loader.load()
embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"})

def init_vectorstore(documents, embedding_model, persist_directory, mode="truncate"):
    if mode == "truncate":
        if os.path.exists(persist_directory):
            shutil.rmtree(persist_directory)
        return Chroma.from_documents(documents, embedding=embedding_model, persist_directory=persist_directory)
    elif mode == "update":
        if os.path.exists(persist_directory):
            vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)
            vectorstore.add_documents(documents)
        else:
            vectorstore = Chroma.from_documents(documents, embedding=embedding_model, persist_directory=persist_directory)
        return vectorstore
    else:
        raise ValueError("Only 2 modes are supported: 'truncate' and 'update'.")

vectorstore = init_vectorstore(documents, embedding_model, CHROMA_PATH, mode=VECTOR_MODE)
retriever = vectorstore.as_retriever(search_kwargs={"k": 20})
llm = Ollama(model=LLM_MODEL, base_url=OLLAMA_API_URL)

# Prompt & parser for table detection
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
        "‼️ **Return only the table names** as a Python list. The output may include one or more tables.\n"
        "If metadata is duplicated, return only the tables suitable for the business request.\n"
        "Understand carefully the request then get the related tables from the metadata.\n\n"
        "Output format should be exactly like this:\n"
        "{format_instructions}\n"
        "If no tables match, return an empty list: []\n"
        "Do not include any descriptions, explanations, or any other information apart from the table names.\n"
        "Do not return any table not listed in the metadata.\n"
        "Metadata:\n{context}\n"
        "Question:\n{question}"
    )
])
final_prompt = chat_prompt_template.partial(format_instructions=parser.get_format_instructions())

# SQL generation prompt & parser
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
        "You are a {backend_db} SQL expert. Given the following table metadata and a business request, understand them and generate a syntactically correct SELECT query "
        "to retrieve data relevant to the question. Only use the columns provided in the metadata below; do not query for all columns or include "
        "columns not listed. If the question involves 'today', use date('now') to get the current date. Use only SELECT queries; do not use "
        "INSERT, UPDATE, DELETE, CREATE, ALTER, or DROP commands.\n\n"
        "The information between the tables, metadata and datamodel is:\n\n"
        "Metadata:\n{full_input}\n\n"
        "The keys relationship between the tables are in the Data Model related to the tables in json: {datamodel}\n"
        "My Question/Business Request is: {query_text}\n\n"
        "Generate the SQL to answer the question. The SQL should be a valid query that can be run on the database.\n\n"
        "If you cannot answer the question, return 'I cannot answer this question. Do not return anything out of the given context in meta, datamodel.'\n"
        "Output format should be exactly like this:\n"
        "{format_instructions}\n"
        "If no tables match, return an empty list: []\n"
        "Do not include any descriptions, explanations, or any other information apart from the table names.\n"
        "Do not return any table not listed in the metadata.\n"
    )
])

final_prompt_output = chat_prompt_template_output.partial(format_instructions=parser_output.get_format_instructions())

def get_related_table_metadata(query_text: str):
    logger.info("Getting related table metadata for query: %s", query_text)
    retrieved_docs = retriever.invoke(query_text)
    context = "\n".join(doc.page_content for doc in retrieved_docs)
    prompt = final_prompt.format(context=context, question=query_text)
    raw_response = llm.invoke(prompt)
    parsed_result = parser.parse(raw_response)
    related_tables = parsed_result["Danh sach bang lien quan"]

    cursor.execute(
        """
        SELECT TABLE_NAME, TABLE_DESCRIPTION, COLUMN_NAME, DATA_TYPE, DOMAIN, PK, NULLABLE, COLUMN_DESCRIPTION, NOTE, ORS_MAP, BACKENDDB, SCHEMA_NAME
        FROM public.metadata_
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
            f"Table: {table_name}\nDescription: {table_description}\nColumn: {column_name}, Data Type: {data_type}, Domain: {domain}, Column Description: {column_description}, Note: {note}, Schema: {schema_name}\n\n"
        )
    final_prompt_output = chat_prompt_template_output.partial(format_instructions=parser_output.get_format_instructions())
    prompt_text = final_prompt_output.format(
        full_input=full_input,
        datamodel=json.dumps(datamodel, ensure_ascii=False, indent=2),
        query_text=query_text, 
        backend_db=backend_db[0]
    )
    sql_response = llm.invoke(prompt_text)
    parsed_sql = parser_output.parse(sql_response)
    return parsed_sql["Cau lenh SQL theo yeu cau nghiep vu"]