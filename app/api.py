
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.functions import get_related_table_metadata, generate_sql_query

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str

@app.post("/query")
def query_answer(request: QueryRequest):
    query_text = request.query

    # Hàm get_related_table_metadata
    metadata_rows = get_related_table_metadata(query_text)
    if not metadata_rows:
        raise HTTPException(status_code=404, detail="No related table metadata found.")

    # Hàm generate_sql_query
    sql_result = generate_sql_query(query_text)

    # Bỏ kí tự xuống dòng do cấu hình của SwaggerUI
    cleaned_sql = sql_result.replace("\n", " ").strip()
    return {'SQL query result': cleaned_sql}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
