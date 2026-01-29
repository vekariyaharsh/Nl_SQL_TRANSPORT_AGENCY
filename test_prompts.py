
import unittest
from unittest.mock import MagicMock, patch
import sys

# Pre-mocking to avoid import errors
mock_mysql_connector = MagicMock()
mock_mysql_connector.Error = Exception # So it can be caught
sys.modules['mysql'] = MagicMock()
sys.modules['mysql.connector'] = mock_mysql_connector
sys.modules['openai'] = MagicMock()
sys.modules['neo4j'] = MagicMock()

from node_nl_to_query import NLToSQLNode
from node_query_validator import QueryValidatorNode
from node_query_corrector import QueryCorrectorNode
from langgraph_schema import create_initial_state

class TestPrompts(unittest.TestCase):

    @patch('node_nl_to_query.MySQLConnection')
    @patch('node_nl_to_query.MySQLSchemaLoader')
    @patch('node_nl_to_query.OpenAI')
    def test_nl_to_sql_prompt_building(self, mock_openai, mock_loader_cls, mock_conn_cls):
        # Setup mocks
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn

        mock_loader = MagicMock()
        mock_loader.format_schema_for_llm.return_value = "### TABLE: lr_dump\nColumns: Billing_Party, CN_Date"
        mock_loader_cls.return_value = mock_loader

        # Initialize node
        node = NLToSQLNode()

        # Test state
        test_question = "Find total freight for Billing Party ABC"
        state = create_initial_state(test_question)

        # Build prompt
        prompt = node._build_prompt(state)

        # Assertions
        self.assertIn(test_question, prompt)
        self.assertIn("lr_dump", prompt)
        self.assertIn("Billing_Party", prompt)
        self.assertIn("CRITICAL SQL RULES", prompt)
        self.assertIn("EXAMPLE QUERIES", prompt)
        print("✅ NLToSQLNode prompt test passed")

    @patch('node_query_validator.OpenAI')
    def test_validator_prompt_building(self, mock_openai):
        # Initialize node
        node = QueryValidatorNode()

        # Test state
        state = create_initial_state("How many consignments?")
        state["generated_query"] = "SELECT COUNT(*) FROM lr_dump"
        state["schema_info"] = "Table: lr_dump, Columns: CN_No"

        # Build prompt
        prompt = node._build_validation_prompt(state)

        # Assertions
        self.assertIn("SELECT COUNT(*) FROM lr_dump", prompt)
        self.assertIn("Table: lr_dump", prompt)
        self.assertIn("Validation Checklist", prompt)
        self.assertIn("VALIDATION:", prompt)
        print("✅ QueryValidatorNode prompt test passed")

    @patch('node_query_corrector.OpenAI')
    def test_corrector_prompt_building(self, mock_openai):
        # Initialize node
        node = QueryCorrectorNode()

        # Test state
        state = create_initial_state("How many consignments?")
        state["generated_query"] = "SELECT COUNT(*) FROM wrong_table"
        state["validation_result"] = "VALIDATION: FAIL\nISSUES:\n- Table 'wrong_table' does not exist."
        state["schema_info"] = "Table: lr_dump, Columns: CN_No"

        # Build prompt
        prompt = node._build_correction_prompt(state)

        # Assertions
        self.assertIn("SELECT COUNT(*) FROM wrong_table", prompt)
        self.assertIn("Table 'wrong_table' does not exist", prompt)
        self.assertIn("Table: lr_dump", prompt)
        self.assertIn("Corrected SQL Query:", prompt)
        print("✅ QueryCorrectorNode prompt test passed")

if __name__ == '__main__':
    unittest.main()
