import json
import logging
import re
import unidecode
from langchain_core.output_parsers import JsonOutputParser


def extract_table_names_from_sql(sql_text: str) -> list:
    """
    Extract table names from SQL query using regex.
    Handles: SELECT ... FROM table_name [schema.table_name] WHERE ...
    """
    tables = []
    # Pattern to match table names after FROM clause
    # Matches: FROM schema.table, FROM table, FROM SCHEMA.TABLE
    pattern = r'FROM\s+([\w.]+)'
    matches = re.findall(pattern, sql_text, re.IGNORECASE)
    for match in matches:
        # Handle SCHEMA.TABLE format
        table = match.split('.')[-1] if '.' in match else match
        if table and table.upper() not in ['WHERE', 'GROUP', 'ORDER', 'LIMIT']:
            tables.append(table.upper())
    return list(set(tables))  # Remove duplicates


def extract_json_from_text(text: str, for_tables: bool = False) -> dict:
    """
    Aggressively extract JSON from text.
    For tables: returns {"danh_sach_bang_lien_quan": [...]}
    For SQL: returns {"cau_lenh_sql_theo_yeu_cau_nghiep_vu": ...}
    """
    if not text:
        return {}
    
    # Normalize
    text = unidecode.unidecode(text).strip()
    
    # Remove common LLM artifacts
    text = text.replace("```json", "").replace("```", "").strip()
    
    # First try: Direct JSON parse
    try:
        parsed = json.loads(text)
        logging.info(f"[JSON PARSED] {parsed}")
        return parsed
    except json.JSONDecodeError as e:
        logging.debug(f"[JSON PARSE FAILED] {e}")
    except Exception as e:
        logging.debug(f"[JSON PARSE ERROR] {e}")
    
    # Second try: Fix common JSON issues (single quotes, missing quotes)
    try:
        # Replace single quotes with double quotes
        fixed_text = text.replace("'", '"')
        parsed = json.loads(fixed_text)
        logging.info(f"[JSON PARSED WITH FIX] {parsed}")
        return parsed
    except Exception:
        pass
    
    # Third try: Find JSON object in text using regex
    json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
    for match in reversed(json_matches):  # Try from end to start
        try:
            parsed = json.loads(match)
            if "cau_lenh_sql_theo_yeu_cau_nghiep_vu" in parsed or "danh_sach_bang_lien_quan" in parsed:
                logging.info(f"[JSON FROM TEXT] {parsed}")
                return parsed
        except Exception:
            pass
    
    # Fourth try: If for_tables=True and LLM returned SQL, extract table names
    if for_tables and 'SELECT' in text.upper():
        tables = extract_table_names_from_sql(text)
        if tables:
            result = {"danh_sach_bang_lien_quan": tables}
            logging.info(f"[TABLES FROM SQL] {result}")
            return result
    
    # Fifth try: Extract raw SQL and wrap it (for SQL generation, not table retrieval)
    if not for_tables:
        sql_match = re.search(
            r'(SELECT\s+.*?(?:FROM|WHERE|GROUP BY|ORDER BY|LIMIT|;|$))',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if sql_match:
            sql = sql_match.group(1).strip()
            if sql.endswith(';'):
                sql = sql[:-1].strip()
            logging.info(f"[EXTRACTED RAW SQL] {sql}")
            return {"cau_lenh_sql_theo_yeu_cau_nghiep_vu": sql}
    
    logging.error(f"[NO JSON/SQL EXTRACTED] from: {text[:200]}")
    return {}

class RAGSQLPipeline:
    def __init__(
        self,
        llm,
        retriever,
        datamodel_path,
        backend_db,
        cursor,
        output_conn,
        final_prompt,
        final_prompt_output,
        meta_storage="postgres",
    ):
        self.llm = llm
        self.retriever = retriever
        self.datamodel_path = datamodel_path
        self.backend_db = backend_db
        self.cursor = cursor
        self.output_conn = output_conn
        self.final_prompt = final_prompt
        self.final_prompt_output = final_prompt_output
        self.meta_storage = meta_storage

        # =====================================================
        # PARSERS (JsonOutputParser của LangChain)
        # =====================================================
        self.parser = JsonOutputParser()
        self.parser_output = JsonOutputParser()

    # =====================================================
    # STEP 1: GET RELATED TABLES
    # =====================================================
    def get_related_table_metadata(self, query_text: str):
        docs = self.retriever.invoke(query_text)
        context = "\n".join(d.page_content for d in docs)

        prompt = self.final_prompt.format(
            context=context,
            question=query_text,
        )

        raw = self.llm.invoke(prompt)
        raw = unidecode.unidecode(raw)
        logging.info("[TABLE RETRIEVAL RAW OUTPUT] %s", raw[:300])

        tables = []
        try:
            parsed = self.parser.parse(raw)
            logging.info("[PARSED JSON] %s", parsed)
            
            # Defensive: check if parsed is dict and has the key
            if isinstance(parsed, dict):
                tables = parsed.get("danh_sach_bang_lien_quan", [])
            elif isinstance(parsed, list):
                # If LLM returned just a list, use it directly
                tables = parsed
            elif isinstance(parsed, str):
                # If LLM returned just a string (table name), wrap it
                tables = [parsed]
            else:
                logging.error("[UNEXPECTED PARSE TYPE] %s", type(parsed))
                
        except Exception as e:
            logging.error("[TABLE PARSE ERROR] %s", e)
            
            # Special case: If raw output is just a table name (no JSON at all)
            if raw and not any(char in raw for char in ['{', '[', 'SELECT']):
                # Might be just "PRIM_PARTY" or similar
                potential_table = raw.strip().strip('"').strip("'")
                if potential_table and potential_table.replace('_', '').replace('.', '').isalnum():
                    logging.info(f"[DETECTED RAW TABLE NAME] {potential_table}")
                    tables = [potential_table]
            
            # Try aggressive extraction if no table detected yet
            if not tables:
                try:
                    parsed = extract_json_from_text(raw, for_tables=True)
                    logging.info("[EXTRACTED JSON] %s", parsed)
                    
                    if isinstance(parsed, dict):
                        tables = parsed.get("danh_sach_bang_lien_quan", [])
                    elif isinstance(parsed, list):
                        tables = parsed
                        
                    if tables:
                        logging.info("[TABLE EXTRACTED] %s", tables)
                except Exception as e2:
                    logging.error("[TABLE EXTRACTION FAILED] %s", e2)
                    logging.error("[RAW OUTPUT] %s", raw)
                    return []

        # Validate tables is a list
        if not isinstance(tables, list):
            logging.error("[TABLES NOT A LIST] Got: %s (type: %s)", tables, type(tables))
            return []
            
        if not tables:
            logging.warning("[NO TABLES FOUND] Query: %s", query_text)
            return []

        # Build WHERE condition with SCHEMA_NAME.TABLE_NAME
        placeholders = ",".join(["%s"] * len(tables))
        query = f"""
            SELECT TABLE_NAME, TABLE_DESCRIPTION, COLUMN_NAME, DATA_TYPE, DOMAIN,
                   PK, NULLABLE, COLUMN_DESCRIPTION, NOTE, ORS_MAP,
                   BACKENDDB, SCHEMA_NAME
            FROM {"public.metadata" if self.meta_storage == "postgres" else "metadata"}
            WHERE (SCHEMA_NAME || '.' || TABLE_NAME) IN ({placeholders})
               OR TABLE_NAME IN ({placeholders})
        """
        self.cursor.execute(query, tuple(tables) + tuple(tables))

        return self.cursor.fetchall()

    # =====================================================
    # STEP 2: GENERATE SQL
    # =====================================================
    def generate_sql_query(self, query_text: str, retry_count: int = 0) -> str:
        rows = self.get_related_table_metadata(query_text)
        if not rows:
            logging.warning("[NO METADATA] No table metadata found for query")
            return ""

        with open(self.datamodel_path, "r", encoding="utf-8") as f:
            datamodel = json.load(f)

        full_input = ""
        for r in rows:
            table, desc, col, dtype, domain, *_, schema = r
            full_input += (
                f"Table: {table}\n"
                f"Description: {desc}\n"
                f"Column: {col}, Type: {dtype}, Domain: {domain}, Schema: {schema}\n\n"
            )

        prompt = self.final_prompt_output.format(
            full_input=full_input,
            datamodel=json.dumps(datamodel, ensure_ascii=False),
            query_text=query_text,
            backend_db=self.backend_db[0],
        )

        # Try 1: Use piped chain
        try:
            chain = prompt | self.llm | self.parser_output
            parsed = chain.invoke({})
            logging.info("[SQL CHAIN PARSED] Type: %s, Value: %s", type(parsed), str(parsed)[:200])
            
            # Defensive: ensure parsed is dict
            if isinstance(parsed, dict):
                sql = parsed.get("cau_lenh_sql_theo_yeu_cau_nghiep_vu", "")
            elif isinstance(parsed, str):
                # LLM returned raw SQL string
                sql = parsed
            else:
                logging.error("[UNEXPECTED SQL PARSE TYPE] %s", type(parsed))
                sql = ""
                
            if sql:
                logging.info("[GENERATED SQL] %s", sql)
                return sql
        except Exception as e:
            logging.error("[SQL CHAIN PARSE ERROR] %s", e)
        
        # Try 2: Direct invoke with aggressive extraction
        try:
            raw_output = self.llm.invoke(prompt)
            logging.info("[RAW LLM OUTPUT] %s", raw_output[:500])
            
            # Try aggressive JSON extraction
            parsed = extract_json_from_text(raw_output, for_tables=False)
            logging.info("[EXTRACTED PARSED] Type: %s, Value: %s", type(parsed), str(parsed)[:200])
            
            if isinstance(parsed, dict):
                sql = parsed.get("cau_lenh_sql_theo_yeu_cau_nghiep_vu", "")
            elif isinstance(parsed, str):
                sql = parsed
            else:
                sql = ""
            
            if sql:
                logging.info("[EXTRACTED SQL] %s", sql)
                return sql
        except Exception as e2:
            logging.error("[SQL FALLBACK PARSE ERROR] %s", e2)
        
        # Try 3: Simplified prompt (for Mistral)
        if retry_count < 1:
            logging.warning("[RETRY WITH SIMPLIFIED PROMPT]")
            try:
                simple_prompt = f"""Generate SQL query.

Tables:
{full_input[:1000]}

Query: {query_text}

Output JSON:
{{"cau_lenh_sql_theo_yeu_cau_nghiep_vu": "SELECT * FROM SCHEMA.TABLE"}}

Your response:
"""
                raw_output = self.llm.invoke(simple_prompt)
                logging.info("[RETRY RAW OUTPUT] %s", raw_output[:500])
                
                parsed = extract_json_from_text(raw_output, for_tables=False)
                
                if isinstance(parsed, dict):
                    sql = parsed.get("cau_lenh_sql_theo_yeu_cau_nghiep_vu", "")
                elif isinstance(parsed, str):
                    sql = parsed
                else:
                    sql = ""
                
                if sql:
                    logging.info("[RETRY EXTRACTED SQL] %s", sql)
                    return sql
            except Exception as e3:
                logging.error("[RETRY ERROR] %s", e3)
        
        logging.error("[ALL ATTEMPTS FAILED] Could not generate SQL")
        return ""