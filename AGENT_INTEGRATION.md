# AI Agent System - Integration Guide

## Overview

Your project is now an **AI Agent System** that can:
- Understand natural language business queries
- Generate SQL with reasoning and validation
- Execute queries and return formatted results
- Learn from failures and refine queries
- Maintain memory and execution history

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        REST API Endpoints                        │
│  /agent/query, /agent/status, /agent/tools, /agent/tool, etc.   │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│                    FastAPI Server (mcp/server.py)               │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│                AgentOrchestrator (base/agent_runner.py)          │
│  Coordinates: Agent + Runner + Tools                            │
└────────────┬────────────────────────────────────────────────────┘
             │
     ┌───────┴───────┐
     │               │
┌────▼─────┐  ┌──────▼──────┐
│  Agent   │  │ ToolManager │
│(Thinking)│  │(Execution)  │
└────┬─────┘  └──────┬──────┘
     │               │
┌────▼───────────────▼─────────────────────────────────────────┐
│                    RAG Pipeline                              │
│          (SQL Generation + Database Access)                  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. SQLAgent (`base/agent_core.py`)

**Responsibilities:**
- Process natural language queries
- Maintain conversation memory
- Think through queries before execution
- Validate and explain SQL

**Key States:**
- `IDLE`: Ready for queries
- `THINKING`: Analyzing query
- `EXECUTING`: Running tools
- `COMPLETED`: Successfully finished
- `ERROR`: Failed execution

**Memory Management:**
- Stores messages (conversation history)
- Tracks execution history
- Maintains context
- Auto-clears old messages (default: 50 message limit)

### 2. AgentRunner (`base/agent_runner.py`)

**Responsibilities:**
- Run agent in a loop (agentic loop)
- Manage iterative refinement
- Control execution flow
- Log all operations

**States:**
- `READY`: Ready to run
- `RUNNING`: Currently executing
- `PAUSED`: Paused by user
- `STOPPED`: Stopped by user

**Iterations:**
- Automatically retries on failure
- Refines queries based on errors
- Respects max_iterations limit

### 3. ToolManager (`base/tool_manager.py`)

**Tools Provided:**
1. `generate_sql` - Convert natural language to SQL
2. `execute_query` - Run SQL and get results
3. `validate_sql` - Check SQL syntax/semantics
4. `explain_query` - Explain what SQL does
5. `get_metadata` - Get table schemas

**Tool Execution:**
- Validates required parameters
- Handles errors gracefully
- Logs all tool calls
- Returns formatted results

## Integration Points

### 1. Python Code Integration

```python
from main_mcp import agent_orchestrator

# Simple usage
result = agent_orchestrator.process_query(
    query="Show me all customers",
    execute=True
)

if result['success']:
    print(f"SQL: {result['sql']}")
    print(f"Data: {result['result']}")
else:
    print(f"Error: {result['error']}")
```

### 2. REST API Integration

**Endpoint:** `POST /agent/query`

```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d {
    "query": "Show me top customers",
    "execute": true,
    "max_iterations": 3
  }
```

### 3. Microservices Integration

```python
import httpx

async def query_agent(business_query: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://agent-service/agent/query",
            json={"query": business_query, "execute": True}
        )
        return response.json()
```

### 4. Custom Tool Integration

```python
from base.tool_manager import Tool, ToolFactory

# Create custom tool
def my_function(param):
    return f"Result: {param}"

custom_tool = Tool(
    name="my_tool",
    description="My custom tool",
    func=my_function,
    input_schema={...},
    required_params=["param"]
)

# Register
agent_orchestrator.tool_manager.register_tool(custom_tool)

# Use via API
curl -X POST http://localhost:8000/agent/tool \
  -d '{"tool_name": "my_tool", "params": {"param": "value"}}'
```

## Data Flow

### Single Query Flow

```
1. User sends query
   ↓
2. Agent receives query → adds to memory
   ↓
3. Agent THINKS → analyzes query intent
   ↓
4. Agent calls ToolManager to GENERATE_SQL
   ↓
5. RAG Pipeline generates SQL
   ↓
6. Agent VALIDATES SQL
   ↓
7. Agent optionally EXECUTES SQL
   ↓
8. Agent adds result to memory
   ↓
9. Return response with SQL + validation + optional results
```

### Iterative Refinement Flow

```
Iteration 1:
  Query → Think → Generate SQL → Validate
  ↓ (Failed)
  Analyze Error → Refine Query
  
Iteration 2:
  Refined Query → Think → Generate SQL → Validate
  ↓ (Failed)
  Analyze Error → Refine Query
  
Iteration 3:
  Refined Query → Think → Generate SQL → Validate
  ✓ Success! Return results
```

## Response Structure

### Success Response
```json
{
  "success": true,
  "sql": "SELECT * FROM customers WHERE city = 'Hanoi'",
  "validation": {
    "syntax_valid": true,
    "issues": [],
    "warnings": []
  },
  "result": [
    {"id": 1, "name": "John", "city": "Hanoi"}
  ],
  "thinking": "User wants customers from Hanoi...",
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
  "error": "Could not generate valid SQL",
  "iterations": 3,
  "logs": [
    {"iteration": 1, "status": "error", "error": "..."},
    {"iteration": 2, "status": "error", "error": "..."},
    {"iteration": 3, "status": "error", "error": "..."}
  ]
}
```

## Configuration

### Environment Variables
```bash
# Database
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password

# LLM
LLM_MODEL=mistral
OLLAMA_API_URL=http://localhost:11434

# Embeddings
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Paths
DATAMODEL_PATH=data/datamodel.json
CHROMA_PATH=chroma_store
META_STORAGE=postgres
```

### Python Configuration
Edit `config/settings.py` to change:
- Agent max iterations
- Memory size
- Tool timeout
- Logging level

## Performance Optimization

### 1. Query Performance
```python
# Reduce retriever K value for faster results
retriever = vector_manager.get_retriever(k=5)  # Was 20

# Reduce max iterations for known good cases
result = agent_orchestrator.process_query(
    query,
    max_iterations=1  # Fast path
)
```

### 2. Memory Management
```python
# Clear memory periodically
if len(agent.memory.messages) > 100:
    agent.reset()

# Or limit message count
from base.agent_core import AgentMemory
memory = AgentMemory(max_messages=20)
```

### 3. Caching
```python
# Cache SQL generation results
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query: str):
    return agent_orchestrator.process_query(query)
```

## Debugging

### Enable Verbose Logging
```bash
PYTHONUNBUFFERED=1 python main_mcp.py
```

### Check Agent State
```bash
curl http://localhost:8000/agent/status | python -m json.tool
```

### View Execution History
```bash
# In Python
logs = agent_orchestrator.runner.get_logs()
for log in logs:
    print(log)
```

### Test Tools Directly
```bash
curl -X POST http://localhost:8000/agent/tool \
  -H "Content-Type: application/json" \
  -d {
    "tool_name": "validate_sql",
    "params": {"sql": "SELECT * FROM customers"}
  }
```

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Database connection tested
- [ ] LLM model available (Ollama running)
- [ ] FAISS index loaded
- [ ] API endpoints responding
- [ ] Tools registered and functional
- [ ] Agent memory management working
- [ ] Error handling in place
- [ ] Logging configured
- [ ] Rate limiting enabled (if needed)

## Scaling Considerations

### Single Instance
- Suitable for: Development, testing, small deployments
- Max queries/sec: ~5-10
- Memory: 2GB minimum

### Multi-Instance (Load Balanced)
- Share database and embeddings
- Separate agent memory per instance
- Consider caching layer

```
    ┌─────────────────┐
    │  Load Balancer  │
    └────────┬────────┘
    ┌────────┴────────┐
    │        │        │
 ┌──▼─┐  ┌──▼─┐  ┌──▼─┐
 │Inst1│  │Inst2│  │Inst3│
 └──┬──┘  └──┬──┘  └──┬──┘
    └────────┴────────┘
         │
    ┌────▼────────┐
    │  Database   │
    │  Embeddings │
    └─────────────┘
```

### Kubernetes Deployment
See `k8s/` directory for:
- Deployment configuration
- Service definition
- ConfigMap setup

## Monitoring

### Key Metrics
- Agent query success rate
- Average SQL generation time
- Tool execution times
- Memory usage
- Error frequency

### Log Aggregation
Send logs to:
- ELK Stack
- Splunk
- CloudWatch
- Datadog

### Health Check
```bash
curl http://localhost:8000/agent/status
```

## Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent returns empty SQL | LLM not connected | Check Ollama: `curl localhost:11434/api/tags` |
| Database errors | Connection failed | Verify DB credentials in `.env` |
| Slow responses | K value too high | Reduce retriever K parameter |
| Memory leaks | Messages not clearing | Call `agent_orchestrator.reset()` |
| Tool not found | Not registered | Check `agent_runner.setup_tools()` |

## File Reference

| File | Purpose | Modified |
|------|---------|----------|
| `base/agent_core.py` | SQLAgent implementation | NEW |
| `base/agent_runner.py` | Agent execution loop | NEW |
| `base/tool_manager.py` | Tool management | NEW |
| `base/agent_test.py` | Test suite | NEW |
| `base/rag_core.py` | RAG pipeline | Unchanged |
| `mcp/server.py` | FastAPI endpoints | UPDATED |
| `mcp/tools.py` | Tool definitions | UPDATED |
| `main_mcp.py` | Entry point | UPDATED |

## Next Steps

1. **Test the agent**: Follow AGENT_QUICKSTART.md
2. **Integrate with your app**: Use REST API
3. **Add custom tools**: Extend tool_manager.py
4. **Deploy**: Use Docker or your platform
5. **Monitor**: Set up logging and metrics
6. **Optimize**: Tune parameters for your use case

## Support & Resources

- **Documentation**: AGENT_README.md
- **Quick Start**: AGENT_QUICKSTART.md
- **Examples**: agent_example.py
- **Tests**: base/agent_test.py
- **API**: http://localhost:8000/docs (Swagger)

---

**Your AI Agent System is ready to go! 🚀**
