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
    ("system", "You are a senior SQL engineer."),
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
     DATABASE
     ====================
     {{backend_db}}

     ====================
     OUTPUT FORMAT (STRICT JSON)
     ====================
     Return ONLY valid JSON in the following format:

     {format_instructions_sql}

     Rules for YOUR ANSWER:
     - Example output:
            "cau_lenh_sql_theo_yeu_cau_nghiep_vu": "SELECT * FROM customers WHERE country = 'USA';"
     - The JSON element must be named "cau_lenh_sql_theo_yeu_cau_nghiep_vu"
     - SQL must be compatible with the specified database type
     - SQL must be executable
     - YOU DO NOT NEED TO EXPLAIN OR PROVIDE ANYTHING ELSE BUT THE SQL USE FOR THE TASK, YOUR ANSWER need to return the SQL query in the specified JSON format
     - Only answer the questions asked according with the provided information
     """)
])

final_prompt_output = chat_prompt_template_output