"""
BACKUP: Original code from app/api.py
Date: February 3, 2026
Status: DEPRECATED - Use mcp/server.py instead

This was the original FastAPI app before the AI Agent System upgrade.
Kept here for reference only.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from api_t2sql.ignore.functions import get_related_table_metadata, generate_sql_query, execute_query
import os
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    output_file: str = None
    execute_query: bool = False

@app.post("/query")
def query_answer(request: QueryRequest):
    query_text = request.query

    # Step 1: Identify related metadata
    metadata_rows = get_related_table_metadata(query_text)
    if not metadata_rows:
        raise HTTPException(status_code=404, detail="No related table metadata found.")

    # Step 2: Generate SQL
    sql_result = generate_sql_query(query_text)
    cleaned_sql = sql_result.replace("\n", " ").strip()

    # Step 3: If execute_query is True, run and export
    if request.execute_query:
        result = execute_query(cleaned_sql)

        output_file_name = request.output_file or "output.csv"
        df = pd.DataFrame(result)
        df.to_csv(output_file_name, index=False)

        return FileResponse(
            output_file_name,
            media_type='text/csv',
            filename=os.path.basename(output_file_name)
        )
    else:
        return {"SQL query result": cleaned_sql}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
