"""
Node 1: Natural Language to SQL Query Generator
"""
import re
from openai import OpenAI
from typing import Dict, Any

from nl_to_sql.config import Config
from nl_to_sql.langgraph_schema import OverallState
from nl_to_sql.database.mysql_schema_loader import MySQLSchemaLoader
from nl_to_sql.database.database_manager import DatabaseManager
from nl_to_sql.utils.few_shot_examples_sql import LogisticsSQLExamples
from nl_to_sql.utils.logger import setup_logger
from nl_to_sql.utils.exceptions import LLMGenerationError

logger = setup_logger(__name__)

class NLToSQLNode:
    """
    Convert natural language questions to MySQL SQL queries.

    This node uses OpenAI's LLM to generate SQL queries based on the database schema
    and provided few-shot examples relevant to the logistics domain.
    """

    def __init__(self):
        """Initialize the node with necessary clients and managers."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.db_manager = DatabaseManager()
        self.schema_loader = MySQLSchemaLoader(self.db_manager)

    def _build_prompt(self, state: OverallState) -> str:
        """
        Build the prompt for SQL query generation.

        Args:
            state: The current state of the workflow.

        Returns:
            A formatted prompt string for the LLM.
        """
        schema_text = self.schema_loader.format_schema_for_llm()
        few_shot_text = LogisticsSQLExamples.get_examples_as_text(
            max_examples=Config.MAX_FEW_SHOT_EXAMPLES
        )

        prompt_template = f"""You are an expert MySQL SQL query generator for logistics and transport management systems.

DATABASE SCHEMA:
{schema_text}

EXAMPLE QUERIES (Learn from these):
{few_shot_text}

CRITICAL SQL RULES:
1. Generate ONLY ONE complete, valid SQL statement
2. NEVER nest SELECT statements in WHERE clauses
3. Structure: SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT
4. Table name: lr_dump (or relevant table from schema)
5. Column names use UNDERSCORES (Billing_Party, CN_Date, Total_Freight, etc.)
6. ALL date fields are stored as TEXT format - handle accordingly

DATE OPERATIONS (Dates are TEXT format):
- Extract year: YEAR(STR_TO_DATE(CN_Date, '%Y-%m-%d')) = 2022 OR SUBSTRING(CN_Date, 1, 4) = '2022'
- Extract month: MONTH(STR_TO_DATE(CN_Date, '%Y-%m-%d')) = 3 OR SUBSTRING(CN_Date, 6, 2) = '03'
- Date range: CN_Date BETWEEN '2021-01-01' AND '2021-12-31'
- Simple year filter: CN_Date LIKE '2022%'

Question: {state['question']}

Generate ONE complete MySQL query following the above rules:"""

        return prompt_template

    def generate_query(self, state: OverallState) -> Dict[str, Any]:
        """
        Generate MySQL SQL query from natural language question.

        Args:
            state: The current state of the workflow.

        Returns:
            A dictionary containing the generated query or error message.
        """
        logger.info(f"Generating SQL query for: '{state['question']}'")

        try:
            prompt_content = self._build_prompt(state)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful SQL assistant expert in transport data."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0
            )

            generated_query = response.choices[0].message.content.strip()

            # Clean up markdown
            if generated_query.startswith("```"):
                generated_query = re.sub(r'```sql\n|```', '', generated_query).strip()

            logger.info(f"Generated SQL query: {generated_query[:100]}...")

            return {
                "generated_query": generated_query,
                "schema_info": self.schema_loader.format_schema_for_llm()
            }

        except Exception as e:
            logger.error(f"Failed to generate SQL: {e}")
            return {
                "generated_query": None,
                "error_message": f"LLM Generation failed: {str(e)}"
            }

def nl_to_query_node(state: OverallState) -> Dict[str, Any]:
    """LangGraph node wrapper for NLToSQLNode."""
    return NLToSQLNode().generate_query(state)
