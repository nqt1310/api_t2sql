"""
AI Agent Core - Main agent logic with memory, reasoning, and tool execution
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from base.rag_core import RAGSQLPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


class AgentMemory:
    """Agent memory management"""
    
    def __init__(self, max_messages: int = 50):
        self.messages: List[BaseMessage] = []
        self.max_messages = max_messages
        self.context: Dict[str, Any] = {}
        self.execution_history: List[Dict] = []
    
    def add_message(self, message: BaseMessage):
        """Add message to memory"""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self) -> List[BaseMessage]:
        """Get conversation history"""
        return self.messages.copy()
    
    def add_execution(self, tool: str, input_data: Dict, output: Any, success: bool):
        """Record tool execution"""
        execution = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool,
            "input": input_data,
            "output": output,
            "success": success
        }
        self.execution_history.append(execution)
        logger.info(f"Execution recorded: {tool}")
    
    def clear(self):
        """Clear memory"""
        self.messages.clear()
        self.context.clear()
        self.execution_history.clear()


class SQLAgent:
    """
    SQL Agent - Converts natural language to SQL queries using RAG
    Maintains state, memory, and can execute queries
    """
    
    def __init__(
        self,
        rag_pipeline: RAGSQLPipeline,
        llm,
        max_iterations: int = 10
    ):
        self.rag_pipeline = rag_pipeline
        self.llm = llm
        self.max_iterations = max_iterations
        self.state = AgentState.IDLE
        self.memory = AgentMemory()
        self.available_tools = self._initialize_tools()
        
    def _initialize_tools(self) -> Dict[str, callable]:
        """Initialize available tools"""
        return {
            "generate_sql": self.rag_pipeline.generate_sql_query,
            "execute_query": self.execute_query,
            "get_metadata": self.rag_pipeline.get_related_table_metadata,
            "explain_query": self.explain_query,
            "validate_sql": self.validate_sql,
        }
    
    def think(self, user_query: str) -> str:
        """Agent thinking phase - analyze user query"""
        self.state = AgentState.THINKING
        
        # Add user query to memory
        self.memory.add_message(HumanMessage(content=user_query))
        
        # Analyze query intent
        thinking_prompt = f"""
Analyze this database query request and break it down:
- What tables might be involved?
- What is the user trying to accomplish?
- Are there any constraints or conditions?

User Query: {user_query}

Provide your analysis:
"""
        analysis = self.llm.invoke(thinking_prompt)
        logger.info(f"Agent Analysis: {analysis}")
        return analysis
    
    def execute(self, user_query: str, execute: bool = False) -> Dict[str, Any]:
        """Execute agent loop"""
        self.state = AgentState.EXECUTING
        
        try:
            # Step 1: Think
            thinking = self.think(user_query)
            
            # Step 2: Generate SQL
            logger.info(f"Generating SQL for: {user_query}")
            sql_query = self.rag_pipeline.generate_sql_query(user_query)
            
            if not sql_query:
                self.state = AgentState.ERROR
                return {
                    "success": False,
                    "error": "Could not generate SQL query",
                    "user_query": user_query
                }
            
            logger.info(f"Generated SQL: {sql_query}")
            self.memory.add_execution("generate_sql", {"query": user_query}, sql_query, True)
            
            # Step 3: Validate SQL
            validation = self.validate_sql(sql_query)
            logger.info(f"SQL Validation: {validation}")
            
            # Step 4: Execute if requested
            result = None
            if execute:
                result = self.execute_query(sql_query)
                self.memory.add_execution("execute_query", {"sql": sql_query}, result, True)
                logger.info(f"Query executed successfully")
            
            # Add AI response to memory
            self.memory.add_message(AIMessage(content=f"SQL Query: {sql_query}"))
            
            self.state = AgentState.COMPLETED
            
            return {
                "success": True,
                "sql": sql_query,
                "validation": validation,
                "result": result if execute else None,
                "thinking": thinking,
                "executed": execute
            }
            
        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"Agent execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_query": user_query
            }
    
    def execute_query(self, sql_query: str) -> List[Dict]:
        """Execute SQL query and return results"""
        try:
            if self.rag_pipeline.output_conn is None:
                return []
            
            with self.rag_pipeline.output_conn.connect() as conn:
                result = conn.execute(sql_query)
                rows = result.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return []
    
    def validate_sql(self, sql_query: str) -> Dict[str, Any]:
        """Validate SQL syntax and semantics"""
        validation = {
            "syntax_valid": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            # Basic syntax checks
            sql_upper = sql_query.upper()
            
            # Check for common issues
            if ";" not in sql_query:
                validation["warnings"].append("Query missing semicolon")
            
            if not any(keyword in sql_upper for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
                validation["syntax_valid"] = False
                validation["issues"].append("No valid SQL statement found")
            
            if sql_upper.count("SELECT") != sql_upper.count("FROM"):
                validation["warnings"].append("Mismatched SELECT and FROM clauses")
            
            logger.info(f"SQL validation result: {validation['syntax_valid']}")
            return validation
            
        except Exception as e:
            validation["syntax_valid"] = False
            validation["issues"].append(str(e))
            return validation
    
    def explain_query(self, sql_query: str) -> str:
        """Explain what the SQL query does"""
        explain_prompt = f"""
Explain this SQL query in simple business terms:

{sql_query}

Provide a clear explanation of:
1. What data is being retrieved
2. Which tables are involved
3. What conditions are applied
4. How results are organized
"""
        explanation = self.llm.invoke(explain_prompt)
        return explanation
    
    def get_state(self) -> str:
        """Get current agent state"""
        return self.state.value
    
    def get_memory(self) -> Dict[str, Any]:
        """Get memory summary"""
        return {
            "message_count": len(self.memory.messages),
            "execution_history_count": len(self.memory.execution_history),
            "context": self.memory.context,
            "last_execution": self.memory.execution_history[-1] if self.memory.execution_history else None
        }
    
    def reset(self):
        """Reset agent state"""
        self.memory.clear()
        self.state = AgentState.IDLE
        logger.info("Agent reset")
