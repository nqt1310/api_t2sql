# SQL AI Agent - Quick Start Guide

## What Changed?

Your project has been upgraded from a simple RAG-SQL pipeline to a **full-featured AI Agent system**.

### Before (Simple RAG)
```
User Query → RAG Pipeline → SQL → Result
```

### After (AI Agent)
```
User Query → Agent Thinking → RAG → SQL Generation → Validation → Execution → Result
              ↑___ Memory Management ___|
              ↑___ Iterative Refinement ___|
              ↑___ Tool Management ___|
```

## New Components

### 1. **Agent Core** (`base/agent_core.py`)
- `SQLAgent`: Main agent with reasoning and memory
- `AgentMemory`: Tracks conversation history and execution logs
- `AgentState`: Enum for agent states (IDLE, THINKING, EXECUTING, etc.)

### 2. **Agent Runner** (`base/agent_runner.py`)
- `AgentRunner`: Controls agent execution loop
- `AgentOrchestrator`: High-level system coordinator

### 3. **Tool Manager** (`base/tool_manager.py`)
- `Tool`: Individual tool definition
- `ToolManager`: Tool registry and executor
- `ToolFactory`: Creates standard tools

## New Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agent/query` | POST | Run agent with natural language |
| `/agent/status` | GET | Check system health |
| `/agent/tools` | GET | List available tools |
| `/agent/tool` | POST | Call specific tool |
| `/agent/reset` | POST | Clear agent memory |

## 5-Minute Quick Start

### Step 1: Start the Server
```bash
python main_mcp.py
```

You should see:
```
==================================================
SQL AI AGENT STARTED
==================================================
Available Tools: 5
  - generate_sql: Generate SQL from business query using RAG
  - execute_query: Execute SQL and return results
  - validate_sql: Validate syntax and semantics
  - explain_query: Explain what a SQL query does in business terms
  - get_metadata: Retrieve table metadata and schema
==================================================
```

### Step 2: Test Agent Status
```bash
curl http://localhost:8000/agent/status
```

### Step 3: Run a Query
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all customers", "execute": false}'
```

Response:
```json
{
  "success": true,
  "sql": "SELECT * FROM customers",
  "validation": {
    "syntax_valid": true,
    "issues": [],
    "warnings": []
  },
  "thinking": "The user wants to see all customers...",
  "iterations": 1,
  "agent_state": "idle"
}
```

### Step 4: Execute Query and Get Data
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me top 5 customers by revenue", "execute": true, "max_iterations": 3}'
```

## Key Features Explained

### 1. Agent Thinking
The agent analyzes your query before generating SQL:
```
Agent Analysis:
- What tables might be involved?
- What is the user trying to accomplish?
- Are there any constraints or conditions?
```

### 2. Automatic Validation
SQL is validated for:
- Syntax errors
- Missing SELECT/FROM
- Mismatched clauses
- Other common issues

### 3. Iterative Refinement
If SQL fails, the agent automatically:
- Analyzes the error
- Refines the query (up to max_iterations)
- Retries with improved understanding

### 4. Memory Management
The agent remembers:
- Conversation history
- Execution logs
- Tool calls and results
- Errors and warnings

## Usage Examples

### Python Usage
```python
# Start server first: python main_mcp.py
# Then in another terminal:

import requests

# Simple query
response = requests.post('http://localhost:8000/agent/query', json={
    'query': 'Count customers by city',
    'execute': False
})
print(response.json()['sql'])

# Execute and get results
response = requests.post('http://localhost:8000/agent/query', json={
    'query': 'Top 10 products by sales',
    'execute': True,
    'max_iterations': 3
})
data = response.json()
for row in data.get('result', []):
    print(row)
```

### Check Tools
```bash
curl http://localhost:8000/agent/tools | python -m json.tool
```

### Check Memory
```bash
curl http://localhost:8000/agent/status | python -m json.tool
```

Look for `agent_memory` in the response.

### Reset Agent
```bash
curl -X POST http://localhost:8000/agent/reset
```

## Configuration Files

### `.env` (Environment Variables)
```
DB_TYPE=postgresql
DB_HOST=localhost
LLM_MODEL=mistral
```

### `config/settings.py`
Database and model configurations

### `data/datamodel.json`
Schema metadata for RAG

## File Structure

```
api_t2sql/
├── base/
│   ├── agent_core.py      ← NEW: Agent logic
│   ├── agent_runner.py    ← NEW: Agent loop
│   ├── agent_test.py      ← NEW: Test suite
│   ├── tool_manager.py    ← NEW: Tool management
│   ├── rag_core.py        ← EXISTING: RAG pipeline
│   └── ...
├── mcp/
│   ├── server.py          ← UPDATED: New endpoints
│   └── tools.py           ← UPDATED: Tool definitions
├── main_mcp.py            ← UPDATED: Agent setup
├── agent_example.py       ← UPDATED: Examples
├── AGENT_README.md        ← NEW: Full documentation
└── AGENT_QUICKSTART.md    ← NEW: This file
```

## Common Tasks

### Task 1: Generate SQL (Don't Execute)
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your business query", "execute": false}'
```

### Task 2: Generate and Execute SQL
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your business query", "execute": true}'
```

### Task 3: Validate Existing SQL
```bash
curl -X POST http://localhost:8000/agent/tool \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "validate_sql", "params": {"sql": "SELECT * FROM customers"}}'
```

### Task 4: Explain Query
```bash
curl -X POST http://localhost:8000/agent/tool \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "explain_query", "params": {"sql": "SELECT * FROM customers WHERE city='"'"'Hanoi'"'"'"}}'
```

## Troubleshooting

### Issue: "Agent not initialized"
**Solution**: Make sure `python main_mcp.py` is running

### Issue: No SQL generated
**Checks**:
1. Is Ollama running? `curl http://localhost:11434/api/tags`
2. Is database connected? Check logs for connection errors
3. Is FAISS index loaded? Check `faiss_base/index.faiss` exists

### Issue: LLM model not found
**Solution**: 
```bash
ollama pull mistral  # or your model name
```

### Issue: Memory issues after many queries
**Solution**: Reset agent
```bash
curl -X POST http://localhost:8000/agent/reset
```

## Performance Tips

1. **First request slower**: RAG indexing takes time, subsequent requests are faster
2. **Batch queries**: Multiple related queries maintain better context
3. **Set iterations wisely**: 
   - 1 iteration: Fast but less reliable
   - 3 iterations: Good balance
   - 5+ iterations: Very thorough but slower

4. **Monitor logs**: `PYTHONUNBUFFERED=1 python main_mcp.py`

## Next Steps

1. **Test locally**: Run the quick commands above
2. **Integrate with your app**: Use the REST API endpoints
3. **Customize tools**: Add domain-specific tools in `base/tool_manager.py`
4. **Deploy**: Use Docker or your preferred deployment method

## Docker Deployment

The existing `dockerfile` and `docker-compose.yml` still work!

```bash
docker-compose up -d
curl http://localhost:8000/agent/status
```

## Support

For detailed documentation, see:
- [AGENT_README.md](AGENT_README.md) - Complete documentation
- [agent_example.py](agent_example.py) - Code examples
- [base/agent_test.py](base/agent_test.py) - Test examples

## What's Next?

The agent is now ready to:
- ✓ Understand natural language
- ✓ Generate SQL with reasoning
- ✓ Validate and execute queries
- ✓ Learn from failures
- ✓ Manage conversation history

You can now:
- Build UIs that talk to the agent
- Integrate with your applications
- Add custom tools
- Deploy to production
- Scale with your needs

**Happy querying! 🚀**
