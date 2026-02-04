import json
import logging
import unidecode
from langchain_core.output_parsers import JsonOutputParser

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
        print(raw)

        try:
            parsed = self.parser.parse(raw)
            tables = parsed.get("danh_sach_bang_lien_quan", [])
        except Exception as e:
            logging.error("[TABLE PARSE ERROR] %s", e)
            logging.error(raw)
            return []

        if not tables:
            return []

        self.cursor.execute(
            f"""
            SELECT TABLE_NAME, TABLE_DESCRIPTION, COLUMN_NAME, DATA_TYPE, DOMAIN,
                   PK, NULLABLE, COLUMN_DESCRIPTION, NOTE, ORS_MAP,
                   BACKENDDB, SCHEMA_NAME
            FROM {"public.metadata" if self.meta_storage == "postgres" else "metadata"}
            WHERE TABLE_NAME IN %s
            """,
            (tuple(tables),),
        )

        return self.cursor.fetchall()

    # =====================================================
    # STEP 2: GENERATE SQL
    # =====================================================
    def generate_sql_query(self, query_text: str) -> str:
        rows = self.get_related_table_metadata(query_text)
        if not rows:
            return ""

        with open(self.datamodel_path, "r", encoding="utf-8") as f:
            datamodel = json.load(f)

        full_input = ""
        for r in rows:
            table, desc, col, dtype, domain, *_ , schema = r
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

        raw_sql = self.llm.invoke(prompt)

        try:
            parsed = self.parser_output.parse(raw_sql)
            logging.info("[GENERATED SQL] %s", parsed.get("cau_lenh_sql_theo_yeu_cau_nghiep_vu", ""))   
            return parsed.get("cau_lenh_sql_theo_yeu_cau_nghiep_vu", "")
        except Exception as e:
            logging.error("[SQL PARSE ERROR] %s", e)
            logging.error(raw_sql)
            return raw_sql