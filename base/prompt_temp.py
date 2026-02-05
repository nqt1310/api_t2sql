from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

# =====================================================
# PARSER: TABLE RETRIEVAL PROMPT
# =====================================================
json_parser = JsonOutputParser()
format_instructions = json_parser.get_format_instructions()

chat_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You identify table names from metadata. Output ONLY JSON array with table names. NO explanations. NO SQL."),
    ("user",
     """
METADATA:
{context}

USER QUERY:
{question}

OUTPUT (JSON only):
{{"danh_sach_bang_lien_quan": ["TABLE1", "TABLE2"]}}

Your response (copy format exactly):
""")

])

final_prompt = chat_prompt_template

# =====================================================
# PROMPT: SQL GENERATION
# =====================================================
json_parser_output = JsonOutputParser()
format_instructions_sql = json_parser_output.get_format_instructions()

chat_prompt_template_output = ChatPromptTemplate.from_messages([
    ("system", "Generate SQL queries. Output ONLY valid JSON. NO explanations."),
    ("user",
     """
TABLES AND COLUMNS:
{full_input}

USER QUERY:
{query_text}

OUTPUT (JSON only):
{{"cau_lenh_sql_theo_yeu_cau_nghiep_vu": "SELECT * FROM SCHEMA.TABLE WHERE condition"}}

Rules:
- Use schema prefix (e.g., DATA.PRIM_PARTY)
- Valid JSON with double quotes
- No text outside JSON

Your response:
""")
])

final_prompt_output = chat_prompt_template_output