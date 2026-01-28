"""
Node 4: SQL Query Executor
"""
from typing import Dict, Any, List
import traceback

from config import Config
from langgraph_schema import OverallState
from mysql_connection import MySQLConnection


class QueryExecutorNode:
    """Execute validated SQL queries via MySQL"""
    
    def __init__(self):
        self.mysql_conn = MySQLConnection(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )
        self.mysql_conn.connect()
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format query results for display"""
        if not results:
            return "Query executed successfully but returned no results."
        
        # Limit to first 10 results for display
        display_results = results[:10]
        
        formatted = []
        for i, record in enumerate(display_results, 1):
            formatted.append(f"Result {i}:")
            for key, value in record.items():
                formatted.append(f"  {key}: {value}")
            formatted.append("")
        
        if len(results) > 10:
            formatted.append(f"... and {len(results) - 10} more results")
        
        return "\n".join(formatted)
    
    def execute_query(self, state: OverallState) -> Dict[str, Any]:
        """
        Execute the validated SQL query
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with execution results
        """
        # Determine which query to execute
        query_to_execute = None
        
        # If we have a corrected query that passed final validation, use it
        if state.get("final_validation_passed"):
            query_to_execute = state.get("corrected_query")
        # Otherwise, if initial query passed validation, use it
        elif state.get("validation_passed"):
            query_to_execute = state.get("generated_query")
        
        if not query_to_execute:
            # Check if we have any query at all
            query_to_execute = state.get("corrected_query") or state.get("generated_query")
            if not query_to_execute:
                return {
                    "execution_success": False,
                    "error_message": "No query available to execute"
                }
        
        print(f"\n⚡ [Node 4] Executing query...")
        print(f"Query:\n{query_to_execute}\n")
        
        try:
            # Execute the query
            results = self.mysql_conn.execute_query(query_to_execute)
            
            # Format results
            formatted_results = self._format_results(results)
            
            print(f"✅ Query executed successfully!")
            print(f"📊 Returned {len(results)} result(s)\n")
            
            # Note: We are NO LONGER storing query examples in vector store (Neo4j removal)
            
            return {
                "execution_result": {
                    "data": results,
                    "formatted": formatted_results,
                    "count": len(results)
                },
                "execution_success": True
            }
            
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            error_trace = traceback.format_exc()
            
            print(f"❌ {error_msg}")
            print(f"Traceback:\n{error_trace}\n")
            
            return {
                "execution_result": None,
                "execution_success": False,
                "error_message": error_msg
            }


def execute_query_node(state: OverallState) -> Dict[str, Any]:
    """
    LangGraph node function for query execution
    
    Args:
        state: Current state
    
    Returns:
        State updates
    """
    node = QueryExecutorNode()
    return node.execute_query(state)


if __name__ == "__main__":
    # Test the node
    print("Testing Query Executor Node...")
    
    try:
        from langgraph_schema import create_initial_state
        
        Config.validate()
        
        # Create test state with a valid query
        state = create_initial_state("Count all requests")
        state["generated_query"] = "SELECT COUNT(*) as count FROM lr_dump"
        state["validation_passed"] = True
        
        # Execute query
        node = QueryExecutorNode()
        result = node.execute_query(state)
        
        print("\n" + "="*80)
        print("Execution Result:")
        print(f"Success: {result.get('execution_success')}")
        if result.get('execution_result'):
            print(f"\nFormatted Results:\n{result['execution_result']['formatted']}")
        else:
            print(f"Error: {result.get('error_message')}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
