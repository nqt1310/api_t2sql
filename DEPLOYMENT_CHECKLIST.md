# AI Agent System - Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Quality
- [x] All new files created and formatted
- [x] Code follows Python best practices
- [x] Type hints included
- [x] Error handling comprehensive
- [x] Logging implemented throughout
- [x] Documentation complete

### ✅ Dependencies
- [x] No new external dependencies
- [x] Uses existing: langchain, langchain_community, fastapi, torch
- [x] requirements.txt unchanged
- [x] Compatible with Python 3.8+

### ✅ Backward Compatibility
- [x] Existing endpoints still work (/mcp/call)
- [x] Legacy RAG pipeline unchanged
- [x] Database connections preserved
- [x] Docker setup compatible

---

## Local Testing Checklist

### 1. Environment Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file configured with database credentials
- [ ] Ollama service running: `ollama serve`
- [ ] Database service running

### 2. Verify Installation
```bash
# Check Python version
python --version

# Verify key packages
python -c "import langchain; import fastapi; import torch; print('OK')"

# Check Ollama availability
curl http://localhost:11434/api/tags
```

### 3. Start Agent Server
```bash
# Terminal 1: Start the agent
PYTHONUNBUFFERED=1 python main_mcp.py

# Should see:
# ==================================================
# SQL AI AGENT STARTED
# ==================================================
# Available Tools: 5
# ...
```

### 4. Test Agent Status
```bash
# Terminal 2: Check if server is running
curl http://localhost:8000/agent/status | python -m json.tool

# Expected response: System status with tools and agent state
```

### 5. Test Simple Query
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all customers",
    "execute": false,
    "max_iterations": 1
  }' | python -m json.tool

# Expected: SQL query generated successfully
```

### 6. Test with Execution
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Count customers by city",
    "execute": true,
    "max_iterations": 1
  }' | python -m json.tool

# Expected: SQL query + results from database
```

### 7. Test Available Tools
```bash
curl http://localhost:8000/agent/tools | python -m json.tool

# Expected: List of 6 tools
# - agent_query
# - generate_sql
# - execute_query
# - validate_sql
# - explain_query
# - get_metadata
```

### 8. Test Tool Execution
```bash
curl -X POST http://localhost:8000/agent/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "validate_sql",
    "params": {"sql": "SELECT * FROM customers"}
  }' | python -m json.tool

# Expected: Validation result
```

### 9. Test Reset
```bash
curl -X POST http://localhost:8000/agent/reset

# Expected: {"success": true, "message": "Agent reset successfully"}
```

### 10. Run Test Suite
```bash
python -c "
from main_mcp import agent_orchestrator
from base.agent_test import run_tests
run_tests(agent_orchestrator)
"

# Expected: All 8 tests pass
```

---

## Docker Testing Checklist

### 1. Build Docker Image
```bash
docker build -t api-t2sql:agent -f dockerfile .

# Verify build succeeded
docker images | grep api-t2sql
```

### 2. Run Docker Container
```bash
docker-compose up -d

# Check logs
docker-compose logs -f api_t2sql

# Should see: "SQL AI AGENT STARTED"
```

### 3. Test Docker Container
```bash
# Test from host
curl http://localhost:8000/agent/status

# Or from inside container
docker exec api_t2sql_1 curl http://localhost:8000/agent/status
```

### 4. Stop Docker
```bash
docker-compose down

# Verify stopped
docker ps | grep api-t2sql
```

---

## Performance Verification

### 1. Response Time Baseline
```bash
# Time a simple query
time curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all customers", "execute": false}' \
  > /dev/null 2>&1

# Expected: 500-1000ms for first query
```

### 2. Concurrent Request Test
```bash
# Test with multiple simultaneous requests
for i in {1..5}; do
  curl -X POST http://localhost:8000/agent/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Show customers", "execute": false}' \
    > /dev/null 2>&1 &
done
wait

# Monitor CPU and memory usage
```

### 3. Memory Usage Check
```bash
# Before any queries
ps aux | grep python

# After 50 queries
# Check if memory is stable (should not grow unbounded)
```

---

## Logging & Monitoring

### 1. Check Logs
```bash
# In running server logs
# Should see INFO level messages like:
# - Starting agent loop for query: ...
# - Executing tool: generate_sql
# - Agent Analysis: ...
```

### 2. Enable Debug Logging
```python
# In config/settings.py, add:
LOGGING_LEVEL = 'DEBUG'

# Or at runtime:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. Check Error Handling
```bash
# Send invalid request
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": ""}'

# Should return proper error response
# Should not crash server
```

---

## Integration Testing

### 1. Test with Python Client
```python
import requests

response = requests.post(
    'http://localhost:8000/agent/query',
    json={'query': 'Test query', 'execute': False}
)
assert response.status_code == 200
assert 'sql' in response.json()
```

### 2. Test with cURL Scripts
```bash
#!/bin/bash
ENDPOINT="http://localhost:8000/agent/query"

curl -X POST $ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{"query": "Show customers"}'
```

### 3. Test with REST Client
- Import collection into Postman
- Run tests for each endpoint
- Verify response formats

---

## Security Checklist

### 1. Input Validation
- [x] Query input validated
- [x] Tool parameters validated
- [x] SQL injection prevention

### 2. Error Handling
- [x] No sensitive data in error messages
- [x] Proper HTTP status codes
- [x] Exception handling

### 3. Database Security
- [x] Credentials in .env (not in code)
- [x] Connection pooling
- [x] Query timeout protection

### 4. API Security
- [x] Input size limits
- [x] Rate limiting (optional, can add)
- [x] CORS configured (optional, can add)

---

## Production Deployment

### Pre-Production
- [ ] All tests passing locally
- [ ] Docker image builds successfully
- [ ] Environment variables configured
- [ ] Database backup in place
- [ ] Monitoring tools configured
- [ ] Logging aggregation setup

### Staging
- [ ] Deploy to staging environment
- [ ] Run full test suite
- [ ] Performance testing
- [ ] Load testing
- [ ] Security scan

### Production
- [ ] Blue-green deployment prepared
- [ ] Rollback plan ready
- [ ] Monitoring alerts configured
- [ ] Support documentation ready
- [ ] Team trained

---

## Post-Deployment

### 1. Health Check
```bash
# Every minute, verify health
curl -s http://localhost:8000/agent/status | \
  grep -q "state" && echo "Healthy" || echo "Unhealthy"
```

### 2. Monitor Metrics
- Agent query success rate
- Average response time
- Tool execution times
- Error frequency
- Memory usage

### 3. Daily Checks
- [ ] No error spikes in logs
- [ ] Response times within SLA
- [ ] Database connections healthy
- [ ] Model service available

### 4. Weekly Reviews
- [ ] Performance trends
- [ ] Error patterns
- [ ] Resource utilization
- [ ] Tool usage statistics

---

## Rollback Plan

If issues arise in production:

### Step 1: Immediate Response
```bash
# Stop the container
docker-compose down

# Or stop the service
systemctl stop api-t2sql
```

### Step 2: Revert Code
```bash
# Go back to previous version
git revert HEAD
# or
git checkout previous-tag
```

### Step 3: Redeploy
```bash
# Rebuild and restart
docker-compose up -d
# or
systemctl start api-t2sql
```

### Step 4: Verify
```bash
# Health check
curl http://localhost:8000/agent/status

# Query test
curl -X POST http://localhost:8000/agent/query \
  -d '{"query": "Test"}'
```

---

## Known Limitations & Workarounds

### Limitation 1: First Query Slower
**Why:** RAG indexing on first access
**Workaround:** Pre-warm with dummy query on startup
```python
agent_orchestrator.process_query("test", execute=False)
```

### Limitation 2: Memory Growth
**Why:** Conversation history accumulation
**Workaround:** Periodically reset agent
```python
if len(agent.memory.messages) > 100:
    agent_orchestrator.reset()
```

### Limitation 3: LLM Rate Limits
**Why:** Ollama model limitations
**Workaround:** Implement request queuing
```python
import asyncio
queue = asyncio.Queue(maxsize=10)
```

---

## Support & Troubleshooting

### If agent doesn't start:
1. Check logs for errors
2. Verify database connection
3. Check Ollama availability
4. Verify .env variables

### If queries fail:
1. Check agent status
2. Test tools directly
3. Verify database schema
4. Check LLM model

### If performance is slow:
1. Check system resources
2. Reduce retriever K value
3. Reduce max_iterations
4. Check database performance

---

## Success Criteria

✅ All Local Tests Pass
- Agent starts successfully
- All 6 tools available
- Sample queries generate SQL
- Test suite passes 100%

✅ Docker Deployment Works
- Image builds without errors
- Container starts and stays healthy
- API responds to requests
- Tools function correctly

✅ Performance Acceptable
- First query: <2 seconds
- Subsequent queries: <1 second
- Memory stable over time
- No resource leaks

✅ Ready for Production
- Documentation complete
- Monitoring configured
- Logging aggregated
- Rollback plan tested

---

## Deployment Sign-Off

**Project:** api_t2sql AI Agent
**Version:** 2.0.0
**Date:** February 3, 2026

**Checklist Status:**
- Pre-deployment: ✅ Complete
- Local testing: ⏳ In Progress
- Docker testing: ⏳ Pending
- Integration: ⏳ Pending
- Production: ⏳ Pending

**Ready for Deployment?** 
```
Check box when all above are complete:
[ ] All tests passing
[ ] Documentation complete
[ ] Monitoring ready
[ ] Team trained
```

---

**For detailed documentation, see:**
- AGENT_QUICKSTART.md
- AGENT_README.md
- AGENT_INTEGRATION.md
- VISUAL_GUIDE.md
