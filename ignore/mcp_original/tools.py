RAG_SQL_TOOL = {
    "name": "rag_sql",
    "description": "Generate SQL from business query using RAG over metadata",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "execute": {"type": "boolean", "default": False},
        },
        "required": ["query"],
    },
}

AGENT_TOOLS = [
    {
        "name": "agent_query",
        "description": "Process query through AI agent with reasoning, tool calling, and iteration",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language business query"
                },
                "execute": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to execute the generated SQL"
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 3,
                    "description": "Maximum iterations for agent loop"
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "generate_sql",
        "description": "Generate SQL query from business requirements using RAG",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language business query"
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "execute_query",
        "description": "Execute SQL query and return results",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL query to execute"
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "validate_sql",
        "description": "Validate SQL query syntax and semantics",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL query to validate"
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "explain_query",
        "description": "Explain what a SQL query does in business terms",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL query to explain"
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "get_metadata",
        "description": "Retrieve table metadata and schema information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_text": {
                    "type": "string",
                    "description": "Query to find related metadata"
                }
            },
            "required": ["query_text"],
        },
    },
]
