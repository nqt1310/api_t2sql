"""
Agent Test Suite - Test agent functionality
"""

import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentTestSuite:
    """Test suite for agent functionality"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.results = []
    
    def test_agent_initialization(self):
        """Test: Agent is properly initialized"""
        test_name = "Agent Initialization"
        try:
            status = self.orchestrator.get_system_status()
            
            assert status is not None, "Status is None"
            assert 'runner' in status, "Missing runner status"
            assert 'agent' in status, "Missing agent status"
            assert 'tools' in status, "Missing tools status"
            assert status['tools']['available'] > 0, "No tools available"
            
            self.record_result(test_name, True, None)
            logger.info(f"✓ {test_name}")
            return True
        except Exception as e:
            self.record_result(test_name, False, str(e))
            logger.error(f"✗ {test_name}: {e}")
            return False
    
    def test_tools_registration(self):
        """Test: All tools are registered"""
        test_name = "Tools Registration"
        try:
            tools = self.orchestrator.get_available_tools()
            
            expected_tools = [
                'generate_sql',
                'execute_query',
                'validate_sql',
                'explain_query',
                'get_metadata'
            ]
            
            tool_names = [t['name'] for t in tools]
            
            for expected in expected_tools:
                assert expected in tool_names, f"Missing tool: {expected}"
            
            self.record_result(test_name, True, None)
            logger.info(f"✓ {test_name}: {len(tools)} tools registered")
            return True
        except Exception as e:
            self.record_result(test_name, False, str(e))
            logger.error(f"✗ {test_name}: {e}")
            return False
    
    def test_sql_generation(self, query: str = "Show me all customers"):
        """Test: SQL generation works"""
        test_name = "SQL Generation"
        try:
            result = self.orchestrator.tool_manager.execute_tool(
                'generate_sql',
                query=query
            )
            
            assert isinstance(result, str), "SQL is not a string"
            assert len(result) > 0, "Generated SQL is empty"
            assert any(keyword in result.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']), \
                "No valid SQL statement found"
            
            self.record_result(test_name, True, f"Generated: {result[:50]}...")
            logger.info(f"✓ {test_name}: {result[:50]}...")
            return True
        except Exception as e:
            self.record_result(test_name, False, str(e))
            logger.error(f"✗ {test_name}: {e}")
            return False
    
    def test_sql_validation(self):
        """Test: SQL validation works"""
        test_name = "SQL Validation"
        try:
            sql = "SELECT * FROM customers WHERE city = 'Hanoi'"
            
            result = self.orchestrator.tool_manager.execute_tool(
                'validate_sql',
                sql=sql
            )
            
            assert isinstance(result, dict), "Validation result is not a dict"
            assert 'syntax_valid' in result, "Missing syntax_valid in result"
            assert isinstance(result['syntax_valid'], bool), "syntax_valid is not boolean"
            
            self.record_result(test_name, True, f"Valid: {result['syntax_valid']}")
            logger.info(f"✓ {test_name}: SQL validated")
            return True
        except Exception as e:
            self.record_result(test_name, False, str(e))
            logger.error(f"✗ {test_name}: {e}")
            return False
    
    def test_agent_execution(self, query: str = "Show me all customers"):
        """Test: Agent full execution"""
        test_name = "Agent Execution"
        try:
            result = self.orchestrator.process_query(
                query,
                execute=False,
                max_iterations=1
            )
            
            assert isinstance(result, dict), "Result is not a dict"
            assert 'success' in result, "Missing success in result"
            assert 'sql' in result or 'error' in result, "Missing sql or error"
            
            if result.get('success'):
                assert len(result.get('sql', '')) > 0, "SQL is empty"
                self.record_result(test_name, True, f"SQL: {result['sql'][:50]}...")
                logger.info(f"✓ {test_name}: Query executed successfully")
            else:
                self.record_result(test_name, False, result.get('error'))
                logger.warning(f"⚠ {test_name}: {result.get('error')}")
            
            return result.get('success', False)
        except Exception as e:
            self.record_result(test_name, False, str(e))
            logger.error(f"✗ {test_name}: {e}")
            return False
    
    def test_agent_memory(self):
        """Test: Agent memory management"""
        test_name = "Agent Memory"
        try:
            # Execute a query
            self.orchestrator.process_query("Show me customers", execute=False, max_iterations=1)
            
            memory = self.orchestrator.agent.get_memory()
            
            assert 'message_count' in memory, "Missing message_count"
            assert 'execution_history_count' in memory, "Missing execution_history_count"
            assert memory['message_count'] > 0, "No messages in memory"
            
            self.record_result(
                test_name,
                True,
                f"Messages: {memory['message_count']}, Executions: {memory['execution_history_count']}"
            )
            logger.info(f"✓ {test_name}: Memory tracked correctly")
            return True
        except Exception as e:
            self.record_result(test_name, False, str(e))
            logger.error(f"✗ {test_name}: {e}")
            return False
    
    def test_agent_reset(self):
        """Test: Agent reset functionality"""
        test_name = "Agent Reset"
        try:
            # Execute query
            self.orchestrator.process_query("Test query", execute=False, max_iterations=1)
            
            # Get memory before reset
            memory_before = self.orchestrator.agent.get_memory()
            
            # Reset
            self.orchestrator.reset()
            
            # Get memory after reset
            memory_after = self.orchestrator.agent.get_memory()
            
            assert memory_before['message_count'] > 0, "No messages before reset"
            assert memory_after['message_count'] == 0, "Memory not cleared after reset"
            
            self.record_result(test_name, True, "Agent reset successfully")
            logger.info(f"✓ {test_name}: Reset works correctly")
            return True
        except Exception as e:
            self.record_result(test_name, False, str(e))
            logger.error(f"✗ {test_name}: {e}")
            return False
    
    def test_runner_status(self):
        """Test: Runner status tracking"""
        test_name = "Runner Status"
        try:
            status = self.orchestrator.runner.get_status()
            
            assert 'state' in status, "Missing state"
            assert 'current_iteration' in status, "Missing current_iteration"
            assert 'max_iterations' in status, "Missing max_iterations"
            assert 'available_tools' in status, "Missing available_tools"
            
            self.record_result(
                test_name,
                True,
                f"State: {status['state']}, Tools: {status['available_tools']}"
            )
            logger.info(f"✓ {test_name}: Runner status accessible")
            return True
        except Exception as e:
            self.record_result(test_name, False, str(e))
            logger.error(f"✗ {test_name}: {e}")
            return False
    
    def record_result(self, test_name: str, passed: bool, details: str = None):
        """Record test result"""
        self.results.append({
            'test': test_name,
            'passed': passed,
            'timestamp': datetime.now().isoformat(),
            'details': details
        })
    
    def print_summary(self):
        """Print test summary"""
        if not self.results:
            logger.info("No tests run")
            return
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        for result in self.results:
            status = "✓" if result['passed'] else "✗"
            details = f" - {result['details']}" if result['details'] else ""
            print(f"{status} {result['test']}{details}")
        
        print("=" * 70)
        print(f"Results: {passed}/{total} passed ({int(passed/total*100)}%)")
        print("=" * 70 + "\n")
    
    def get_results(self):
        """Get test results as dict"""
        return {
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r['passed']),
                'failed': sum(1 for r in self.results if not r['passed'])
            },
            'results': self.results
        }
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting Agent Test Suite")
        logger.info("=" * 70)
        
        # Run tests
        self.test_agent_initialization()
        self.test_tools_registration()
        self.test_sql_generation()
        self.test_sql_validation()
        self.test_agent_execution()
        self.test_agent_memory()
        self.test_runner_status()
        self.test_agent_reset()
        
        # Print summary
        self.print_summary()
        
        return self.get_results()


def run_tests(orchestrator):
    """Run test suite"""
    suite = AgentTestSuite(orchestrator)
    return suite.run_all_tests()


if __name__ == "__main__":
    print("Note: This script should be imported from main_mcp.py context")
    print("Usage: python -c \"from main_mcp import agent_orchestrator; from base.agent_test import run_tests; run_tests(agent_orchestrator)\"")
