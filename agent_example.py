#!/usr/bin/env python3
"""
Agent Example Script - Demonstrates how to use the SQL Agent
"""

import asyncio
import json
from datetime import datetime
from base.agent_core import SQLAgent
from base.agent_runner import AgentOrchestrator


async def main_example():
    """Example of using the agent"""
    
    # This assumes you've already initialized the orchestrator in main_mcp.py
    # For standalone demo:
    
    print("\n" + "=" * 70)
    print("SQL AI AGENT - INTERACTIVE EXAMPLE")
    print("=" * 70 + "\n")
    
    # Example queries to demonstrate the agent
    example_queries = [
        "Show me all customers in Hanoi",
        "What is the total revenue by product category?",
        "List employees with salary above 50 million VND",
        "Get top 10 selling products",
    ]
    
    print("Example Queries:")
    for i, query in enumerate(example_queries, 1):
        print(f"  {i}. {query}")
    
    print("\nUsage Examples:")
    print("-" * 70)
    
    # Example 1: Simple SQL generation without execution
    print("\nExample 1: Generate SQL (no execution)")
    print(">>> query = 'Show me all customers in Hanoi'")
    print(">>> result = agent_orchestrator.process_query(query, execute=False)")
    print("Result: Generated SQL query for analysis\n")
    
    # Example 2: Generate and execute
    print("Example 2: Generate and Execute SQL")
    print(">>> query = 'What is the total revenue by category?'")
    print(">>> result = agent_orchestrator.process_query(query, execute=True)")
    print("Result: SQL generated + executed + data returned\n")
    
    # Example 3: Check system status
    print("Example 3: Check Agent System Status")
    print(">>> status = agent_orchestrator.get_system_status()")
    print("Result: Returns available tools, agent state, memory info\n")
    
    # Example 4: Reset agent
    print("Example 4: Reset Agent")
    print(">>> agent_orchestrator.reset()")
    print("Result: Clears memory and resets state\n")
    
    print("-" * 70)
    print("\nKey Features of the AI Agent:")
    print("  ✓ Multi-step reasoning with agent thinking")
    print("  ✓ Automatic SQL generation from natural language")
    print("  ✓ SQL validation and explanation")
    print("  ✓ Query execution with result handling")
    print("  ✓ Memory management and execution history")
    print("  ✓ Tool-based architecture for extensibility")
    print("  ✓ Iterative refinement (up to 3+ iterations)")
    print("  ✓ REST API endpoints for integration")
    print("\nAPI Endpoints:")
    print("  POST /agent/query          - Run agent with natural language")
    print("  GET  /agent/status         - Get system status")
    print("  GET  /agent/tools          - List available tools")
    print("  POST /agent/tool           - Call specific tool")
    print("  POST /agent/reset          - Reset agent state")
    print("\n" + "=" * 70 + "\n")


class AgentDemo:
    """Demo class for agent capabilities"""
    
    @staticmethod
    def print_result(result: dict, query: str):
        """Pretty print agent result"""
        print(f"\nQuery: {query}")
        print("=" * 70)
        
        if result.get("success"):
            print(f"✓ Success!")
            print(f"\nGenerated SQL:")
            print(f"  {result.get('sql')}")
            
            if result.get('validation'):
                validation = result.get('validation')
                print(f"\nValidation:")
                print(f"  Syntax Valid: {validation.get('syntax_valid')}")
                if validation.get('warnings'):
                    print(f"  Warnings: {validation.get('warnings')}")
            
            if result.get('result'):
                print(f"\nQuery Results:")
                rows = result.get('result', [])[:5]  # Show first 5 rows
                for row in rows:
                    print(f"  {row}")
                if len(result.get('result', [])) > 5:
                    print(f"  ... and {len(result.get('result')) - 5} more rows")
            
            print(f"\nIterations: {result.get('iterations')}")
            print(f"Agent State: {result.get('agent_state')}")
            
        else:
            print(f"✗ Failed!")
            print(f"Error: {result.get('error')}")
    
    @staticmethod
    def demo_tool_calling(orchestrator):
        """Demonstrate tool calling"""
        print("\n" + "=" * 70)
        print("TOOL CALLING DEMO")
        print("=" * 70)
        
        # Example: Call validate_sql tool directly
        sql = "SELECT * FROM customers WHERE city = 'Ha Noi'"
        
        print(f"\nValidating SQL: {sql}")
        try:
            validation = orchestrator.tool_manager.execute_tool(
                "validate_sql",
                sql=sql
            )
            print(f"Result: {json.dumps(validation, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main_example())
