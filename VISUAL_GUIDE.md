# AI Agent System - Visual Guide

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          REST API Layer                                 │
│  /agent/query  /agent/status  /agent/tools  /agent/tool  /agent/reset  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│                     FastAPI Server (mcp/server.py)                      │
│  - Routes requests to appropriate handlers                              │
│  - Manages request/response formatting                                  │
│  - Error handling and validation                                        │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│              AgentOrchestrator (base/agent_runner.py)                   │
│  - Coordinates Agent, Runner, and ToolManager                           │
│  - Entry point for query processing                                     │
│  - System status management                                             │
└────────┬──────────────────────────────────────────┬──────────────────┬──┘
         │                                          │                  │
         │                                          │                  │
    ┌────▼──────────┐                   ┌──────────▼──────────┐    ┌──▼──────────┐
    │   SQLAgent    │                   │   AgentRunner      │    │ToolManager  │
    │(Reasoning)    │                   │(Loop Control)      │    │(Execution)  │
    ├───────────────┤                   ├────────────────────┤    ├─────────────┤
    │ think()       │                   │ run()              │    │execute_tool │
    │ execute()     │                   │ pause/resume/stop  │    │register_tool│
    │ validate_sql()│                   │ get_status()       │    │list_tools() │
    │ execute_query │                   │ get_logs()         │    │             │
    │ explain_query │                   │                    │    │ Tools:      │
    │               │                   │                    │    │ - generate_ │
    │ AgentMemory   │                   │ RunnerState:       │    │   sql       │
    │ - messages    │                   │ READY/RUNNING/     │    │ - validate_ │
    │ - history     │                   │ PAUSED/STOPPED     │    │   sql       │
    │ - context     │                   │                    │    │ - execute_  │
    └────┬──────────┘                   └────────────────────┘    │   query     │
         │                                                         │ - explain_  │
         │                                                         │   query     │
         │                                                         │ - get_      │
         │                                                         │   metadata  │
         │                                                         └──┬──────────┘
         │                                                            │
         └────────────────────────────┬─────────────────────────────┘
                                      │
                    ┌─────────────────▼─────────────────┐
                    │  RAG Pipeline (base/rag_core.py)  │
                    │  - Vector retrieval               │
                    │  - LLM prompt engineering         │
                    │  - SQL generation                 │
                    └─────────────────┬─────────────────┘
                                      │
                    ┌─────────────────▼─────────────────┐
                    │  Database Layer (base/db.py)      │
                    │  - Metadata queries               │
                    │  - SQL execution                  │
                    │  - Result formatting              │
                    └───────────────────────────────────┘
```

## Agent Execution Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  1. RECEIVE QUERY                   │
│  - Add to memory                    │
│  - Log request                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. AGENT THINKING                  │
│  - Analyze query intent             │
│  - Identify requirements            │
│  - Plan execution                   │
│  State: THINKING                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. SQL GENERATION                  │
│  - Call generate_sql tool           │
│  - Use RAG retrieval                │
│  - LLM generates SQL                │
│  State: EXECUTING                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. SQL VALIDATION                  │
│  - Call validate_sql tool           │
│  - Check syntax                     │
│  - Report issues/warnings           │
└──────────────┬──────────────────────┘
               │
               ├─── Valid? ──┐
               │             │
              YES            NO
               │             │
               │     ┌───────▼──────────────┐
               │     │ 5a. REFINEMENT       │
               │     │ - Analyze error      │
               │     │ - Retry with hint    │
               │     │ - Max iterations?    │
               │     └─────┬────────────────┘
               │           │
               │      ┌────┴────┐
               │      │         │
               │     YES       NO
               │      │         │
               │      └────┬────┘
               │           │
               │           ▼
               │    ┌──────────────────┐
               │    │ Return Error     │
               │    │ State: ERROR     │
               │    └──────────────────┘
               │
               ▼
        ┌──────────────────────────────────┐
        │ 5b. OPTIONAL EXECUTION           │
        │ - if execute=true                │
        │ - Call execute_query tool        │
        │ - Get results from database      │
        └──────────┬───────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │ 6. PREPARE RESPONSE              │
        │ - Combine all results            │
        │ - Add memory info                │
        │ - Log completion                 │
        │ State: COMPLETED                 │
        └──────────┬───────────────────────┘
                   │
                   ▼
              RETURN RESULT
              - success: true/false
              - sql: generated SQL
              - validation: validation result
              - result: optional query results
              - thinking: analysis
              - agent_memory: memory state
```

## Iterative Refinement Loop

```
┌─────────────────┐
│  Iteration 1    │
├─────────────────┤
│ Query → SQL     │
│ ❌ Failed       │
│ Error: XYZ      │
└────────┬────────┘
         │
    Analyze Error
    └─ "WHERE clause syntax error"
         │
         ▼
┌─────────────────┐
│  Iteration 2    │
├─────────────────┤
│ Refined Query   │
│ → SQL           │
│ ❌ Failed       │
│ Error: ABC      │
└────────┬────────┘
         │
    Analyze Error
    └─ "Table not found"
         │
         ▼
┌─────────────────┐
│  Iteration 3    │
├─────────────────┤
│ Refined Query   │
│ → SQL           │
│ ✅ Success!     │
│ → Execute       │
│ → Return Data   │
└─────────────────┘

Max Iterations Check:
└─ If max_iterations=1: Stop after iteration 1
└─ If max_iterations=3: Can retry up to 3 times ✓
└─ If max_iterations=5: Can retry up to 5 times
```

## Tool Execution Flow

```
Tool Request
    │
    ▼
┌─────────────────────────────────────┐
│  ToolManager.execute_tool()         │
│  - Get tool by name                 │
│  - Validate parameters              │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
 VALID                INVALID
    │                     │
    │                  ┌──▼───────────┐
    │                  │ Return Error  │
    │                  │ Missing param │
    │                  └───────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Tool.execute(**kwargs)             │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    │         (depending on tool)
    │
    ├─ generate_sql ──┐
    │                 ▼
    │         RAG Retrieval
    │         ↓
    │         LLM Call
    │         ↓
    │         Parse SQL
    │
    ├─ validate_sql ─┐
    │                ▼
    │         Check Syntax
    │         ↓
    │         Validate Logic
    │         ↓
    │         Return Report
    │
    ├─ execute_query ┐
    │                ▼
    │         DB Connection
    │         ↓
    │         Run Query
    │         ↓
    │         Format Results
    │
    ├─ explain_query ┐
    │                ▼
    │         LLM Analysis
    │         ↓
    │         Return Explanation
    │
    └─ get_metadata ─┐
                     ▼
             DB Metadata Query
             ↓
             Filter Results
             ↓
             Return Schema Info
```

## State Machines

### Agent State Machine

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
    ╔════════╗
    ║  IDLE  ║ ◄─────────────────┐
    ╚════════╝                   │
       │                         │
       │ execute()               │
       ▼                         │
    ╔════════╗                   │
    ║THINKING║                   │
    ╚════════╝                   │
       │                         │
       ▼                         │
    ╔════════╗                   │
    ║EXECUTING║                  │
    ╚════════╝                   │
       │                         │
       ├─ Success ──────────────►│
       │   ╔═════════╗           │
       │   ║COMPLETED║───────────┘
       │   ╚═════════╝
       │
       └─ Failure
           ╔═════╗
           ║ERROR║
           ╚═════╝
              │
              └─ retry() ◄─ (within max_iterations)
                  └─ back to THINKING
```

### Runner State Machine

```
    ╔═════╗
    ║START║
    ╚═════╝
      │
      ▼
   ╔═════╗
   ║READY║
   ╚═════╝
      │
      │ run()
      ▼
   ╔═════════╗
   ║ RUNNING ║
   ╚═════════╝
      │
      ├─ pause()
      │   ▼
      │ ╔═══════╗
      │ ║ PAUSED║
      │ ╚═══════╝
      │   │
      │   └─ resume() ──→ (back to RUNNING)
      │
      ├─ stop()
      │   ▼
      │ ╔═══════╗
      │ ║STOPPED║
      │ ╚═══════╝
      │
      └─ complete() ──→ (back to READY)
```

## Memory Organization

```
Agent Memory
│
├─ messages (List[BaseMessage])
│  ├─ HumanMessage("Show me customers")
│  ├─ AIMessage("Thinking about the query...")
│  ├─ HumanMessage("Add city = Hanoi")
│  └─ AIMessage("Generated SQL...")
│
├─ context (Dict)
│  ├─ last_query: "Show me customers..."
│  ├─ tables_involved: ["customers", "orders"]
│  └─ user_intent: "Data retrieval"
│
└─ execution_history (List[Dict])
   ├─ {
   │   "tool": "generate_sql",
   │   "input": {"query": "..."},
   │   "output": "SELECT ...",
   │   "success": true
   │ }
   ├─ {
   │   "tool": "validate_sql",
   │   "input": {"sql": "SELECT ..."},
   │   "output": {"syntax_valid": true},
   │   "success": true
   │ }
   └─ {
       "tool": "execute_query",
       "input": {"sql": "SELECT ..."},
       "output": [{"id": 1, "name": "John"}],
       "success": true
     }
```

## Request/Response Flow

```
CLIENT REQUEST
    │
    ├─ POST /agent/query
    │  └─ {"query": "...", "execute": bool, "max_iterations": int}
    │
    ▼
┌─────────────────────────────────┐
│ FastAPI Endpoint Handler        │
│ (mcp/server.py)                 │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ AgentOrchestrator.process_query │
│ (base/agent_runner.py)          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ AgentRunner.run()               │
│ (base/agent_runner.py)          │
└────────────┬────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
  ┌─────────┐   ┌──────────────┐
  │ Agent   │   │ ToolManager  │
  │ .think()│   │ .execute()   │
  └─────────┘   └──────────────┘
      │             │
      └──────┬──────┘
             │
             ▼
      ┌──────────────┐
      │ Format Result│
      └──────┬───────┘
             │
             ▼
        SERVER RESPONSE
            │
            ├─ HTTP 200
            │  {
            │    "success": true,
            │    "sql": "...",
            │    "validation": {...},
            │    "result": [...],
            │    "thinking": "...",
            │    "iterations": 1,
            │    "agent_state": "idle",
            │    "agent_memory": {...}
            │  }
            │
            └─ HTTP 500 (on error)
               {
                 "success": false,
                 "error": "..."
               }
```

## Tool Registration & Execution

```
Agent Startup
    │
    ▼
┌─────────────────────────────────┐
│ AgentRunner.setup_tools()       │
└────────────┬────────────────────┘
             │
    ┌────────┼────────┬────────┬─────────────┐
    │        │        │        │             │
    ▼        ▼        ▼        ▼             ▼
 Tool 1   Tool 2   Tool 3   Tool 4        Tool 5
   │        │        │        │             │
   └────────┴────────┴────────┴─────────────┘
            │
            ▼
    ┌──────────────────┐
    │ ToolManager      │
    ├──────────────────┤
    │ tools: {         │
    │   "generate_sql":│◄─── Tool 1
    │   "validate_sql":│◄─── Tool 2
    │   "execute_...": │◄─── Tool 3
    │   "explain_...": │◄─── Tool 4
    │   "get_metadata":│◄─── Tool 5
    │ }                │
    └──────────────────┘
            │
            │ Tool Request
            │ {"tool_name": "...", "params": {...}}
            │
            ▼
    Call Tool → Execute → Return Result
```

## Performance Flow

```
┌─────────────────────────────────────┐
│ Query Complexity                    │
│                                     │
│ Simple Query (1 iteration)          │ ~500-800ms
│ └─ Think + Generate + Validate      │
│                                     │
│ Medium Query (2 iterations)         │ ~1000-1500ms
│ └─ Think + Generate + Validate      │
│    └─ Refine + Generate + Validate  │
│                                     │
│ Complex Query (3 iterations)        │ ~1500-2500ms
│ └─ Think + Generate + Validate      │
│    └─ Refine + Generate + Validate  │
│    └─ Refine + Generate + Validate  │
│                                     │
│ + Execution Time (if execute=true)  │ +100-5000ms
│ └─ DB query + results formatting    │
└─────────────────────────────────────┘
```

---

**This visual guide helps understand the complex interactions in the AI Agent System!**
