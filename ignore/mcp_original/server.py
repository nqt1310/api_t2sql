from fastapi import FastAPI, HTTPException
from mcp.tools import RAG_SQL_TOOL, AGENT_TOOLS
from pydantic import BaseModel

app = FastAPI()
rag_pipeline = None
agent_orchestrator = None


class AgentQuery(BaseModel):
    query: str
    execute: bool = False
    max_iterations: int = 3


class ToolCall(BaseModel):
    tool_name: str
    params: dict


def inject_pipeline(pipeline):
    global rag_pipeline
    rag_pipeline = pipeline


def inject_agent(orchestrator):
    global agent_orchestrator
    agent_orchestrator = orchestrator
    if agent_orchestrator:
        import logging
        logging.info("✓ Agent Orchestrator injected into server")


@app.get("/health")
def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "agent_ready": agent_orchestrator is not None
    }


@app.get("/mcp")
def manifest():
    return {
        "name": "sql-ai-agent-mcp",
        "version": "2.0.0",
        "description": "SQL Generation Agent with RAG and Tool Management",
        "tools": [RAG_SQL_TOOL] + AGENT_TOOLS,
    }


@app.get("/agent/status")
def agent_status():
    if agent_orchestrator is None:
        raise HTTPException(500, "Agent not initialized")
    
    return agent_orchestrator.get_system_status()


@app.get("/agent/tools")
def list_agent_tools():
    if agent_orchestrator is None:
        raise HTTPException(500, "Agent not initialized")
    
    return {"tools": agent_orchestrator.get_available_tools()}


@app.post("/agent/query")
def run_agent_query(request: AgentQuery):
    """Run agent loop with natural language query"""
    if agent_orchestrator is None:
        raise HTTPException(500, "Agent not initialized")
    
    try:
        result = agent_orchestrator.process_query(
            request.query,
            execute=request.execute,
            max_iterations=request.max_iterations
        )
        # Ensure result is a dict
        if result is None:
            return {
                "success": False,
                "error": "No result returned from agent"
            }
        # Convert any non-serializable objects to strings
        return {
            "success": result.get("success", False),
            "sql": result.get("sql", ""),
            "validation": result.get("validation"),
            "result": result.get("result"),
            "thinking": result.get("thinking", ""),
            "executed": result.get("executed", False),
            "iterations": result.get("iterations", 0),
            "agent_state": result.get("agent_state", "unknown"),
            "error": result.get("error")
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/agent/tool")
def call_agent_tool(request: ToolCall):
    """Call specific agent tool"""
    if agent_orchestrator is None:
        raise HTTPException(500, "Agent not initialized")
    
    try:
        result = agent_orchestrator.tool_manager.execute_tool(
            request.tool_name,
            **request.params
        )
        return {
            "success": True,
            "tool": request.tool_name,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "tool": request.tool_name,
            "error": str(e)
        }


@app.post("/mcp/call")
def call_tool(payload: dict):
    """Legacy endpoint for backward compatibility"""
    if rag_pipeline is None:
        raise HTTPException(500, "RAG pipeline not initialized")

    if payload.get("name") == "rag_sql":
        args = payload.get("arguments", {})
        query = args.get("query")
        execute = args.get("execute", False)

        sql = rag_pipeline.generate_sql_query(query)

        if execute:
            return {"sql": sql, "result": rag_pipeline.execute_query(sql)}

        return {"sql": sql}
    
    elif payload.get("name") == "agent_query":
        if agent_orchestrator is None:
            raise HTTPException(500, "Agent not initialized")
        
        args = payload.get("arguments", {})
        result = agent_orchestrator.process_query(
            args.get("query"),
            execute=args.get("execute", False),
            max_iterations=args.get("max_iterations", 3)
        )
        return result
    
    else:
        raise HTTPException(400, "Unknown tool")


@app.post("/agent/reset")
def reset_agent():
    """Reset agent state"""
    if agent_orchestrator is None:
        raise HTTPException(500, "Agent not initialized")
    
    agent_orchestrator.reset()
    return {"success": True, "message": "Agent reset successfully"}

