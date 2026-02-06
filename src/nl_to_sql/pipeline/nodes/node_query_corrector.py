"""
Node 3: Query Corrector
"""
import re
from openai import OpenAI
from typing import Dict, Any

from nl_to_sql.config import Config
from nl_to_sql.langgraph_schema import OverallState
from nl_to_sql.utils.logger import setup_logger

logger = setup_logger(__name__)

class QueryCorrectorNode:
    """
    Correct SQL queries based on validation feedback.

    This node takes an invalid SQL query and the feedback from the validation node,
    and asks the LLM to provide a corrected version of the query.
    """

    def __init__(self):
        """Initialize the corrector node with OpenAI client."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL

    def _build_correction_prompt(self, state: OverallState) -> str:
        """
        Build the prompt for query correction.

        Args:
            state: The current state of the workflow.

        Returns:
            A formatted prompt string for the LLM.
        """
        original_query = state.get("generated_query")
        validation_feedback = state.get("validation_result", "")

        prompt_template = f"""You are an expert at correcting MySQL SQL queries.

Original Question: {state['question']}
Original SQL Query: {original_query}
Validation Feedback: {validation_feedback}
Schema Information: {state.get("schema_info", "")}

Your task:
1. Identify all issues mentioned in feedback
2. Correct the SQL query
3. Return ONLY the corrected SQL query

Corrected SQL Query:"""

        return prompt_template

    def correct_query(self, state: OverallState) -> Dict[str, Any]:
        """
        Correct the SQL query based on validation feedback.

        Args:
            state: The current state of the workflow.

        Returns:
            State updates containing the corrected query and incremented iteration count.
        """
        iteration = state.get("iteration_count", 0) + 1
        logger.info(f"Correcting query (Iteration {iteration}/{Config.MAX_CORRECTION_ITERATIONS})...")

        if iteration > Config.MAX_CORRECTION_ITERATIONS:
            return {"error_message": "Max iterations exceeded", "final_validation_passed": False}

        try:
            prompt_content = self._build_correction_prompt(state)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful SQL corrector."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0
            )

            corrected_query = response.choices[0].message.content.strip()
            if corrected_query.startswith("```"):
                corrected_query = re.sub(r'```sql\n|```', '', corrected_query).strip()

            logger.info("Corrected query generated.")
            return {"corrected_query": corrected_query, "iteration_count": iteration}

        except Exception as e:
            logger.error(f"Error correcting query: {e}")
            return {"error_message": str(e), "final_validation_passed": False}

def correct_query_node(state: OverallState) -> Dict[str, Any]:
    """LangGraph node wrapper for QueryCorrectorNode."""
    return QueryCorrectorNode().correct_query(state)
