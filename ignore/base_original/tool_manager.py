"""
Tool Manager - Manages available tools for the agent
"""
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    func: Callable
    input_schema: Dict[str, Any]
    required_params: List[str]
    
    def execute(self, **kwargs) -> Any:
        """Execute tool with given parameters"""
        # Validate required parameters
        missing = [p for p in self.required_params if p not in kwargs]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")
        
        logger.info(f"Executing tool: {self.name}")
        try:
            result = self.func(**kwargs)
            logger.info(f"Tool {self.name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {str(e)}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class ToolManager:
    """Manages agent tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.info(f"Tool registered: {tool.name}")
    
    def unregister_tool(self, tool_name: str):
        """Unregister a tool"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Tool unregistered: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        return tool.execute(**kwargs)
    
    def tool_exists(self, tool_name: str) -> bool:
        """Check if tool exists"""
        return tool_name in self.tools


class ToolFactory:
    """Factory for creating standard tools"""
    
    @staticmethod
    def create_sql_generator_tool(rag_pipeline) -> Tool:
        """Create SQL generator tool"""
        return Tool(
            name="generate_sql",
            description="Generate SQL query from business requirements using RAG",
            func=rag_pipeline.generate_sql_query,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language business query"
                    }
                },
                "required": ["query"]
            },
            required_params=["query"]
        )
    
    @staticmethod
    def create_query_executor_tool(executor_func) -> Tool:
        """Create query executor tool"""
        return Tool(
            name="execute_query",
            description="Execute SQL query and return results",
            func=executor_func,
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                },
                "required": ["sql"]
            },
            required_params=["sql"]
        )
    
    @staticmethod
    def create_metadata_tool(rag_pipeline) -> Tool:
        """Create metadata retrieval tool"""
        return Tool(
            name="get_metadata",
            description="Retrieve table metadata and schema information",
            func=rag_pipeline.get_related_table_metadata,
            input_schema={
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "Query to find related metadata"
                    }
                },
                "required": ["query_text"]
            },
            required_params=["query_text"]
        )
    
    @staticmethod
    def create_sql_validator_tool(validator_func) -> Tool:
        """Create SQL validator tool"""
        return Tool(
            name="validate_sql",
            description="Validate SQL query syntax and semantics",
            func=validator_func,
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to validate"
                    }
                },
                "required": ["sql"]
            },
            required_params=["sql"]
        )
    
    @staticmethod
    def create_query_explainer_tool(explainer_func) -> Tool:
        """Create query explanation tool"""
        return Tool(
            name="explain_query",
            description="Explain what a SQL query does in business terms",
            func=explainer_func,
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to explain"
                    }
                },
                "required": ["sql"]
            },
            required_params=["sql"]
        )
