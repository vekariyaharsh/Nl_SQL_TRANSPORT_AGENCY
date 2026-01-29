
"""
Utility script to generate and inspect prompts for different scenarios.
Useful for prompt engineering and manual verification of prompt quality.
"""
from unittest.mock import MagicMock, patch
import sys

# Mocking to avoid external dependencies
mock_mysql_connector = MagicMock()
mock_mysql_connector.Error = Exception
sys.modules['mysql'] = MagicMock()
sys.modules['mysql.connector'] = mock_mysql_connector
sys.modules['openai'] = MagicMock()
sys.modules['neo4j'] = MagicMock()

from node_nl_to_query import NLToSQLNode
from node_query_validator import QueryValidatorNode
from node_query_corrector import QueryCorrectorNode
from langgraph_schema import create_initial_state

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

@patch('node_nl_to_query.MySQLConnection')
@patch('node_nl_to_query.MySQLSchemaLoader')
@patch('node_nl_to_query.OpenAI')
def evaluate_prompts(mock_openai, mock_loader_cls, mock_conn_cls):
    # Setup mocks
    mock_loader = MagicMock()
    mock_loader.format_schema_for_llm.return_value = """
# MySQL Database Schema
Database: logistics_db

## Tables:
### lr_dump
Columns:
  - Billing_Party: varchar NOT NULL
  - CN_No: int NOT NULL
  - CN_Date: varchar NOT NULL
  - Total_Freight: decimal NOT NULL
  - LR_Profit: decimal NOT NULL
    """
    mock_loader_cls.return_value = mock_loader

    nl_node = NLToSQLNode()
    val_node = QueryValidatorNode()
    corr_node = QueryCorrectorNode()

    test_cases = [
        {
            "question": "Top 5 billing parties by revenue in 2022",
            "query": "SELECT Billing_Party, SUM(Total_Freight) FROM lr_dump GROUP BY Billing_Party LIMIT 5",
            "validation": "VALIDATION: FAIL\nISSUES:\n- Missing ORDER BY for 'Top 5'"
        },
        {
            "question": "How many consignments were handled in March 2023?",
            "query": "SELECT COUNT(*) FROM lr_dump WHERE CN_Date LIKE '2023-03%'",
            "validation": "VALIDATION: FAIL\nISSUES:\n- Date format might be inconsistent with database"
        },
        {
            "question": "Total profit for route 'Mumbai to Delhi'",
            "query": "SELECT SUM(LR_Profit) FROM lr_dump WHERE Route = 'Mumbai to Delhi'",
            "validation": "VALIDATION: FAIL\nISSUES:\n- Column 'Route' does not exist in lr_dump"
        }
    ]

    for case in test_cases:
        question = case["question"]
        print_banner(f"SCENARIO: {question}")

        # 1. Generation Prompt
        state = create_initial_state(question)
        gen_prompt = nl_node._build_prompt(state)
        print("\n--- 1. GENERATION PROMPT ---")
        print(gen_prompt[:500] + "...")

        # 2. Validation Prompt
        state["generated_query"] = case["query"]
        state["schema_info"] = mock_loader.format_schema_for_llm()
        val_prompt = val_node._build_validation_prompt(state)
        print("\n--- 2. VALIDATION PROMPT ---")
        print(val_prompt[:500] + "...")

        # 3. Correction Prompt
        state["validation_result"] = case["validation"]
        corr_prompt = corr_node._build_correction_prompt(state)
        print("\n--- 3. CORRECTION PROMPT ---")
        print(corr_prompt[:500] + "...")

if __name__ == "__main__":
    evaluate_prompts()
