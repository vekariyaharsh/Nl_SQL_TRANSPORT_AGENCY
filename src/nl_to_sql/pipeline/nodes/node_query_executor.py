"""
Node 4: SQL Query Executor
"""
from typing import Dict, Any, List
import traceback

from nl_to_sql.config import Config
from nl_to_sql.langgraph_schema import OverallState
from nl_to_sql.database.database_manager import DatabaseManager
from nl_to_sql.utils.logger import setup_logger
from nl_to_sql.utils.exceptions import QueryExecutionError

logger = setup_logger(__name__)

class QueryExecutorNode:
    """
    Execute validated SQL queries via DatabaseManager.

    This node takes the validated (and potentially corrected) SQL query from the state,
    executes it against the MySQL database, and formats the results.
    """

    def __init__(self):
        """Initialize the executor node with the database manager."""
        self.db = DatabaseManager()

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format query results into a human-readable string.

        Args:
            results: List of result rows from the database.

        Returns:
            A formatted string representation of the results.
        """
        if not results:
            return "Query executed successfully but returned no results."

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
        Execute the validated SQL query and update the state.

        Args:
            state: The current state of the workflow.

        Returns:
            State updates containing execution results and success status.
        """
        query_to_execute = (state.get("corrected_query") if state.get("final_validation_passed")
                           else state.get("generated_query") if state.get("validation_passed")
                           else None)

        if not query_to_execute:
            query_to_execute = state.get("corrected_query") or state.get("generated_query")
            if not query_to_execute:
                return {"execution_success": False, "error_message": "No query available to execute"}

        logger.info("Executing SQL query...")

        try:
            results = self.db.execute_query(query_to_execute)
            formatted_results = self._format_results(results)

            logger.info(f"Successfully executed query, returned {len(results)} rows.")

            return {
                "execution_result": {
                    "data": results,
                    "formatted": formatted_results,
                    "count": len(results)
                },
                "execution_success": True
            }

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {"execution_success": False, "error_message": f"Database execution error: {str(e)}"}

def execute_query_node(state: OverallState) -> Dict[str, Any]:
    """LangGraph node wrapper for QueryExecutorNode."""
    return QueryExecutorNode().execute_query(state)
