"""
Node 2: SQL Query Validator
"""
from openai import OpenAI
from typing import Dict, Any

from nl_to_sql.config import Config
from nl_to_sql.langgraph_schema import OverallState
from nl_to_sql.utils.logger import setup_logger

logger = setup_logger(__name__)

class QueryValidatorNode:
    """Validate MySQL SQL queries for syntax and logical correctness"""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL

    def _build_validation_prompt(self, state: OverallState) -> str:
        query_to_validate = state.get("corrected_query") or state.get("generated_query")
        schema_text = state.get("schema_info", "Schema information not available.")

        prompt_template = f"""You are an expert MySQL SQL query validator.

Your task is to validate the following SQL query against the schema and identify any issues.

{schema_text}

Original Question: {state['question']}

SQL Query to Validate:
{query_to_validate}

Validation Checklist:
1. SYNTAX: Is the MySQL syntax correct?
2. TABLES: Do all tables exist in the schema?
3. COLUMNS: Do all columns exist in the mentioned tables?
4. GROUP BY: Are all non-aggregated columns in SELECT present in GROUP BY?
5. LOGIC: Does the query logically answer the question?

Respond in the following format:
VALIDATION: [PASS/FAIL]
ISSUES: [List issues]
SUGGESTIONS: [List suggestions]"""

        return prompt_template

    def validate_query(self, state: OverallState) -> Dict[str, Any]:
        """Validate the SQL query"""
        query_to_validate = state.get("corrected_query") or state.get("generated_query")

        if not query_to_validate:
            return {"validation_passed": False, "error_message": "No query to validate"}

        is_revalidation = state.get("corrected_query") is not None
        logger.info(f"Validating query ({'re-validation' if is_revalidation else 'initial'})...")

        try:
            prompt_content = self._build_validation_prompt(state)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful SQL validator."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0
            )

            validation_result = response.choices[0].message.content.strip()
            validation_passed = "VALIDATION: PASS" in validation_result

            logger.info(f"Validation {'PASSED' if validation_passed else 'FAILED'}")

            result_key = "final_validation_passed" if is_revalidation else "validation_passed"
            return {
                result_key: validation_passed,
                "validation_result": validation_result
            }

        except Exception as e:
            error_msg = f"Error during validation: {str(e)}"
            logger.error(error_msg)
            return {"validation_passed": False, "validation_result": error_msg}

def validate_query_node(state: OverallState) -> Dict[str, Any]:
    return QueryValidatorNode().validate_query(state)
