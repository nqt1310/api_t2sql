from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

# =====================================================
# PARSER: TABLE RETRIEVAL PROMPT
# =====================================================
json_parser = JsonOutputParser()
format_instructions = json_parser.get_format_instructions()

chat_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are an assistant in understanding business requests and table metadata."),
    ("user",
     f"""
     The metadata is provided in the following format for each entry:

     table_name: table_description

     Based on the metadata above, identify all tables that are relevant to the request.

     Output format must be EXACTLY:
     {format_instructions}

     Rules:
     - Example output:
            "danh_sach_bang_lien_quan": ["customers", "orders"]
     - The Json element "danh_sach_bang_lien_quan" must contain a list of table names, always be this string "danh_sach_bang_lien_quan"
     - Only list table names that are explicitly mentioned or clearly implied by the request
     - Output JSON ONLY, if multiple tables, list them all in a JSON array
     - No explanation
     - No markdown
     - Do not hallucinate table names
     Metadata:
     {{context}}
     Question:
     {{question}}
     """)
])

final_prompt = chat_prompt_template

# =====================================================
# PROMPT: SQL GENERATION
# =====================================================
json_parser_output = JsonOutputParser()
format_instructions_sql = json_parser_output.get_format_instructions()

chat_prompt_template_output = ChatPromptTemplate.from_messages([
    ("system", "You are a senior SQL engineer. Your task is to generate SQL queries based on business requirements. You MUST ALWAYS return your answer as valid JSON, nothing else."),
    ("user",
     f"""
====================
TABLE METADATA
====================
{{full_input}}

====================
DATAMODEL
====================
{{datamodel}}

====================
BUSINESS QUESTION
====================
{{query_text}}

====================
DATABASE TYPE
====================
{{backend_db}}

====================
CRITICAL REQUIREMENTS
====================
1. You MUST return ONLY valid JSON format
2. Use ONLY the tables and columns from the datamodel provided above
3. ALWAYS prefix table names with schema (e.g., DATA.PRIM_PARTY, RPT.RPT_CUST_IDENT_DLY)
4. Never use table names without schema prefix
5. Write SQL that is executable on the specified database
6. Do NOT provide any explanation, only the JSON response

====================
RESPONSE FORMAT (STRICT JSON)
====================
Return ONLY this JSON format:

{format_instructions_sql}

Example:
{{"cau_lenh_sql_theo_yeu_cau_nghiep_vu": "SELECT * FROM DATA.PRIM_PARTY WHERE IDENTN_DOC_NBR = '001201015338';"}}

Important: Your ENTIRE response must be ONLY the JSON above, starting with {{ and ending with }}.
Do not include any text before or after the JSON.
Do not include markdown code blocks.
     """)
])

final_prompt_output = chat_prompt_template_output