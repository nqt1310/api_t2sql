# SQL AI Agent

A sophisticated AI agent that converts natural language business queries into SQL queries with reasoning, validation, and execution capabilities.

## Features

### 🤖 Agent Architecture
- **Multi-step Reasoning**: Agent thinks through queries before executing
- **Tool Management**: Extensible tool system with built-in SQL tools
- **Memory Management**: Maintains conversation history and execution logs
- **Iterative Refinement**: Automatically refines queries on failure (up to 3+ iterations)
- **State Management**: Tracks agent and runner states for debugging

### 🔧 Built-in Tools
1. **generate_sql** - Convert natural language to SQL using RAG
2. **execute_query** - Execute SQL and return results
3. **validate_sql** - Validate syntax and semantics
4. **explain_query** - Explain SQL in business terms
5. **get_metadata** - Retrieve table metadata and schema

### 📊 Capabilities
- Natural language to SQL conversion via RAG
- Automatic SQL validation
- Query execution with result formatting
- Multi-iteration refinement on failures
- Comprehensive logging and debugging

## Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Start the Agent Server
```bash
python main_mcp.py
```

This will:
- Initialize the RAG pipeline
- Setup the SQL Agent
- Create the Agent Orchestrator
- Start the FastAPI server on `http://localhost:8000`

### 3. Use the Agent

#### Via REST API

**Generate SQL and execute:**
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d {
    "query": "Show me all customers in Hanoi",
    "execute": true,
    "max_iterations": 3
  }
```

**Check agent status:**
```bash
curl http://localhost:8000/agent/status
```

**List available tools:**
```bash
curl http://localhost:8000/agent/tools
```

#### Via Python

```python
from base.agent_runner import AgentOrchestrator
from base.rag_core import RAGSQLPipeline

# Assuming orchestrator is initialized
result = agent_orchestrator.process_query(
    "Show me all customers in Hanoi",
    execute=True,
    max_iterations=3
)

print(f"SQL: {result['sql']}")
print(f"Results: {result['result']}")
```

## API Endpoints

### Agent Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/query` | POST | Run agent with natural language query |
| `/agent/status` | GET | Get system status and available tools |
| `/agent/tools` | GET | List all available agent tools |
| `/agent/tool` | POST | Call specific tool directly |
| `/agent/reset` | POST | Reset agent state and memory |

### Legacy Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp` | GET | Get manifest with all tools |
| `/mcp/call` | POST | Call tool (legacy) |

## Response Format

### Successful Response
```json
{
  "success": true,
  "sql": "SELECT * FROM customers WHERE city = 'Ha Noi'",
  "validation": {
    "syntax_valid": true,
    "issues": [],
    "warnings": []
  },
  "result": [
    {"id": 1, "name": "Customer 1", "city": "Ha Noi"},
    {"id": 2, "name": "Customer 2", "city": "Ha Noi"}
  ],
  "thinking": "The user wants to see customers...",
  "executed": true,
  "iterations": 1,
  "agent_state": "idle",
  "agent_memory": {
    "message_count": 2,
    "execution_history_count": 1,
    "last_execution": {...}
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Could not generate valid SQL after multiple attempts",
  "iterations": 3,
  "logs": [...]
}
```

## Agent Architecture Details

### SQLAgent
Core agent class that:
- Processes natural language queries
- Maintains conversation memory
- Manages agent state (IDLE, THINKING, EXECUTING, COMPLETED, ERROR)
- Thinks through queries before execution
- Validates SQL before execution

**Key Methods:**
- `execute(query, execute)` - Main execution method
- `think(query)` - Analyze and reason about the query
- `validate_sql(sql)` - Check SQL syntax and semantics
- `execute_query(sql)` - Run SQL query
- `explain_query(sql)` - Explain what SQL does
- `get_memory()` - Get memory summary
- `reset()` - Clear agent state

### AgentRunner
Manages the agentic loop with:
- Iterative query refinement
- Tool execution coordination
- Execution logging
- State management (READY, RUNNING, PAUSED, STOPPED)

**Key Methods:**
- `run(query, execute, max_iterations)` - Run agent loop
- `setup_tools()` - Initialize available tools
- `pause()` / `resume()` / `stop()` - Control execution
- `get_status()` - Get runner status
- `get_logs()` - Get execution history

### ToolManager
Manages agent tools with:
- Tool registration and unregistration
- Tool execution with validation
- Schema management

**Key Methods:**
- `register_tool(tool)` - Add new tool
- `execute_tool(name, **kwargs)` - Execute tool
- `list_tools()` - Get available tools

### AgentOrchestrator
High-level orchestrator that:
- Sets up agent, runner, and tools
- Coordinates the complete workflow
- Manages system status

**Key Methods:**
- `process_query(query, execute, max_iterations)` - Process query
- `get_available_tools()` - List tools
- `get_system_status()` - Get full status
- `reset()` - Reset everything

## Configuration

### Environment Variables (.env)
```
DB_TYPE=postgresql
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

LLM_MODEL=mistral  # or your Ollama model
OLLAMA_API_URL=http://localhost:11434

EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
DATAMODEL_PATH=data/datamodel.json
CHROMA_PATH=chroma_store
META_STORAGE=postgres
```

## Examples

### Example 1: Simple Query
```python
result = agent_orchestrator.process_query(
    "Show me all customers",
    execute=False
)
print(result['sql'])
```

### Example 2: Execute and Get Data
```python
result = agent_orchestrator.process_query(
    "What is the total sales by region?",
    execute=True,
    max_iterations=3
)
for row in result['result']:
    print(row)
```

### Example 3: Direct Tool Usage
```python
from base.tool_manager import ToolFactory

# Get metadata for a query
metadata = agent_orchestrator.tool_manager.execute_tool(
    "get_metadata",
    query_text="customers and sales"
)
```

### Example 4: Check System Status
```python
status = agent_orchestrator.get_system_status()
print(f"Runner State: {status['runner']['state']}")
print(f"Available Tools: {status['tools']['available']}")
print(f"Agent Memory: {status['agent']['memory']}")
```

## Logging

The agent provides comprehensive logging at INFO level. Set `PYTHONUNBUFFERED=1` to see real-time logs:

```bash
PYTHONUNBUFFERED=1 python main_mcp.py
```

## File Structure

```
api_t2sql/
├── base/
│   ├── agent_core.py          # SQLAgent and AgentMemory
│   ├── agent_runner.py        # AgentRunner and AgentOrchestrator
│   ├── tool_manager.py        # Tool management
│   ├── rag_core.py            # RAG pipeline (existing)
│   └── ...
├── mcp/
│   ├── server.py              # FastAPI server (updated)
│   └── tools.py               # Tool definitions (updated)
├── main_mcp.py                # Entry point (updated)
├── agent_example.py           # Example usage
└── requirements.txt
```

## Extending the Agent

### Add a New Tool
```python
from base.tool_manager import Tool, ToolManager

def my_custom_function(param1, param2):
    return f"Result: {param1} + {param2}"

# Create tool
custom_tool = Tool(
    name="my_tool",
    description="Does something custom",
    func=my_custom_function,
    input_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "string"}
        },
        "required": ["param1", "param2"]
    },
    required_params=["param1", "param2"]
)

# Register tool
orchestrator.tool_manager.register_tool(custom_tool)
```

## Troubleshooting

### Agent not generating valid SQL
- Check LLM model availability: `curl http://localhost:11434/api/tags`
- Verify RAG retriever is working: Check `base/vector_store_manager.py`
- Enable debug logging for detailed error messages

### Tools not available
- Verify `setup_tools()` is called in AgentRunner
- Check tool registration in `agent_runner.py`

### Memory issues
- Clear agent memory: `agent_orchestrator.reset()`
- Adjust `max_messages` in AgentMemory (default: 50)

## Performance Tips

1. **Optimize retriever**: Adjust `k=20` in main_mcp.py based on your needs
2. **Batch queries**: Process multiple queries sequentially to maintain context
3. **Use max_iterations**: Set to 1-2 for faster responses if stability is good
4. **Monitor memory**: Check `agent_memory` in responses
5. **Cache embeddings**: FAISS index is pre-computed, enable persistence

## Security Considerations

1. **Query Validation**: All SQL is validated before execution
2. **Parameter Binding**: Use parameterized queries to prevent SQL injection
3. **Access Control**: Add authentication to FastAPI endpoints if needed
4. **Rate Limiting**: Consider adding rate limiting for production use
5. **Logging**: Be careful with logging sensitive data

## Future Enhancements

- [ ] Multi-turn conversation with context
- [ ] Query optimization suggestions
- [ ] Cost estimation for queries
- [ ] Query result caching
- [ ] Support for complex joins and subqueries
- [ ] Natural language explanations of query results
- [ ] Interactive query refinement UI
- [ ] Database-specific optimizations

## Contributing

To contribute improvements:
1. Test your changes with `agent_example.py`
2. Ensure logging is added for debugging
3. Update documentation
4. Add tool tests if adding new tools

## License

See LICENSE file for details
