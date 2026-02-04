"""
Agent Runner - Agentic loop implementation
Handles the iterative execution of the agent
"""
import logging
from typing import Any, Dict, List, Optional
from enum import Enum
from base.agent_core import SQLAgent, AgentState
from base.tool_manager import ToolManager, ToolFactory

logger = logging.getLogger(__name__)


class RunnerState(Enum):
    """Runner execution states"""
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class AgentRunner:
    """
    Runs the agent in an agentic loop
    Handles tool calls, feedback, and iterative refinement
    """
    
    def __init__(self, agent: SQLAgent, tool_manager: ToolManager):
        self.agent = agent
        self.tool_manager = tool_manager
        self.state = RunnerState.READY
        self.max_iterations = 5
        self.current_iteration = 0
        self.execution_log: List[Dict[str, Any]] = []
    
    def setup_tools(self):
        """Setup default tools for the agent"""
        logger.info("Setting up agent tools...")
        
        # Register SQL generation tool
        sql_gen_tool = ToolFactory.create_sql_generator_tool(self.agent.rag_pipeline)
        self.tool_manager.register_tool(sql_gen_tool)
        
        # Register query executor tool
        executor_tool = ToolFactory.create_query_executor_tool(self.agent.execute_query)
        self.tool_manager.register_tool(executor_tool)
        
        # Register metadata tool
        metadata_tool = ToolFactory.create_metadata_tool(self.agent.rag_pipeline)
        self.tool_manager.register_tool(metadata_tool)
        
        # Register SQL validator tool
        validator_tool = ToolFactory.create_sql_validator_tool(self.agent.validate_sql)
        self.tool_manager.register_tool(validator_tool)
        
        # Register query explainer tool
        explainer_tool = ToolFactory.create_query_explainer_tool(self.agent.explain_query)
        self.tool_manager.register_tool(explainer_tool)
        
        logger.info(f"Tools setup complete. Available tools: {len(self.tool_manager.tools)}")
    
    def run(
        self,
        user_query: str,
        execute: bool = False,
        max_iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run agent loop
        
        Args:
            user_query: User's natural language query
            execute: Whether to execute the generated SQL
            max_iterations: Maximum iterations (overrides default)
        
        Returns:
            Final result dictionary
        """
        self.state = RunnerState.RUNNING
        self.current_iteration = 0
        self.execution_log.clear()
        
        if max_iterations:
            self.max_iterations = max_iterations
        
        logger.info(f"Starting agent loop for query: {user_query}")
        
        iteration_results = []
        
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration + 1
            logger.info(f"=== Iteration {self.current_iteration}/{self.max_iterations} ===")
            
            # Check runner state
            if self.state == RunnerState.STOPPED:
                logger.info("Runner stopped")
                break
            
            if self.state == RunnerState.PAUSED:
                logger.info("Runner paused")
                continue
            
            # Execute agent
            try:
                result = self.agent.execute(user_query, execute=execute)
                iteration_results.append(result)
                
                # Log execution
                self.execution_log.append({
                    "iteration": self.current_iteration,
                    "status": "success" if result.get("success") else "failed",
                    "result": result
                })
                
                # If successful, return
                if result.get("success"):
                    self.state = RunnerState.READY
                    return self._format_final_result(iteration_results)
                
                # If failed, try to refine
                if iteration < self.max_iterations - 1:
                    logger.info(f"Iteration {self.current_iteration} had issues, attempting refinement...")
                    user_query = self._refine_query(user_query, result.get("error"))
                
            except Exception as e:
                logger.error(f"Iteration {self.current_iteration} failed: {str(e)}")
                self.execution_log.append({
                    "iteration": self.current_iteration,
                    "status": "error",
                    "error": str(e)
                })
        
        self.state = RunnerState.READY
        
        # Return best result found
        successful = [r for r in iteration_results if r.get("success")]
        if successful:
            return self._format_final_result([successful[-1]])
        else:
            return {
                "success": False,
                "error": "Could not generate valid SQL after multiple attempts",
                "iterations": len(iteration_results),
                "logs": self.execution_log
            }
    
    def _refine_query(self, original_query: str, error: str) -> str:
        """Refine query based on error"""
        refined = f"{original_query} (Note: Previous attempt failed with: {error}. Please adjust.)"
        logger.info(f"Refined query: {refined}")
        return refined
    
    def _format_final_result(self, results: List[Dict]) -> Dict[str, Any]:
        """Format final result from iteration results"""
        if not results:
            return {"success": False, "error": "No results"}
        
        best_result = results[-1]  # Last successful result
        
        return {
            "success": True,
            "sql": best_result.get("sql"),
            "validation": best_result.get("validation"),
            "result": best_result.get("result"),
            "thinking": best_result.get("thinking"),
            "executed": best_result.get("executed"),
            "iterations": len(results),
            "agent_state": self.agent.get_state(),
            "agent_memory": self.agent.get_memory()
        }
    
    def pause(self):
        """Pause runner"""
        self.state = RunnerState.PAUSED
        logger.info("Runner paused")
    
    def resume(self):
        """Resume runner"""
        if self.state == RunnerState.PAUSED:
            self.state = RunnerState.RUNNING
            logger.info("Runner resumed")
    
    def stop(self):
        """Stop runner"""
        self.state = RunnerState.STOPPED
        logger.info("Runner stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get runner status"""
        return {
            "state": self.state.value,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "available_tools": len(self.tool_manager.tools),
            "agent_state": self.agent.get_state()
        }
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get execution logs"""
        return self.execution_log.copy()


class AgentOrchestrator:
    """
    Orchestrates the complete agent system
    Sets up and manages agent, runner, and tools
    """
    
    def __init__(self, rag_pipeline, llm):
        self.rag_pipeline = rag_pipeline
        self.llm = llm
        self.agent = SQLAgent(rag_pipeline, llm)
        self.tool_manager = ToolManager()
        self.runner = AgentRunner(self.agent, self.tool_manager)
        
        # Setup tools
        self.runner.setup_tools()
    
    def process_query(
        self,
        user_query: str,
        execute: bool = False,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Process a user query through the agent
        
        Args:
            user_query: Natural language query
            execute: Whether to execute the generated SQL
            max_iterations: Maximum iterations for agent loop
        
        Returns:
            Complete result with SQL, validation, and optionally data
        """
        logger.info(f"Processing query: {user_query}")
        return self.runner.run(user_query, execute, max_iterations)
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return self.tool_manager.list_tools()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "runner": self.runner.get_status(),
            "agent": {
                "state": self.agent.get_state(),
                "memory": self.agent.get_memory()
            },
            "tools": {
                "available": len(self.tool_manager.tools),
                "tools": self.get_available_tools()
            }
        }
    
    def reset(self):
        """Reset agent and runner"""
        self.agent.reset()
        self.runner.execution_log.clear()
        logger.info("System reset")
