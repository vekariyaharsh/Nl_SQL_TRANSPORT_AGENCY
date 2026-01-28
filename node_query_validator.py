"""
Node 2: SQL Query Validator
"""
from openai import OpenAI
from typing import Dict, Any

from config import Config
from langgraph_schema import OverallState


class QueryValidatorNode:
    """Validate MySQL SQL queries for syntax and logical correctness"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
    
    def _build_validation_prompt(self, state: OverallState) -> str:
        """Build prompt for query validation"""
        
        # Determine which query to validate
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
4. GROUP BY: Are all non-aggregated columns in the SELECT clause present in GROUP BY?
5. LOGIC: Does the query logically answer the question?
6. JOINs: Are JOIN conditions correct (if any)?

Respond in the following format:

VALIDATION: [PASS/FAIL]

ISSUES:
- [List any issues found, or "None" if validation passes]

SUGGESTIONS:
- [List specific suggestions to fix the issues, or "None" if validation passes]

Your response:"""
        
        return prompt_template
    
    def validate_query(self, state: OverallState) -> Dict[str, Any]:
        """
        Validate the SQL query
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with validation results
        """
        # Determine which query to validate
        query_to_validate = state.get("corrected_query") or state.get("generated_query")
        
        if not query_to_validate:
            return {
                "validation_result": "No query to validate",
                "validation_passed": False,
                "error_message": "No query generated"
            }
        
        is_revalidation = state.get("corrected_query") is not None
        node_label = "Node 2 (Re-validation)" if is_revalidation else "Node 2 (Initial Validation)"
        
        print(f"\n🔍 [{node_label}] Validating query...")
        print(f"Query: {query_to_validate[:100]}...")
        
        try:
            # Build prompt
            prompt_content = self._build_validation_prompt(state)
            
            # Validate
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful SQL validator."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0
            )
            
            validation_result = response.choices[0].message.content.strip()
            
            # Parse validation result
            validation_passed = "VALIDATION: PASS" in validation_result
            
            status_icon = "✅" if validation_passed else "❌"
            print(f"{status_icon} Validation {'PASSED' if validation_passed else 'FAILED'}")
            
            if not validation_passed:
                print(f"Validation feedback:\n{validation_result}\n")
            
            # Update state based on whether this is initial or re-validation
            if is_revalidation:
                return {
                    "final_validation_passed": validation_passed,
                    "validation_result": validation_result
                }
            else:
                return {
                    "validation_passed": validation_passed,
                    "validation_result": validation_result
                }
            
        except Exception as e:
            error_msg = f"Error during validation: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "validation_passed": False,
                "validation_result": error_msg,
                "error_message": error_msg
            }


def validate_query_node(state: OverallState) -> Dict[str, Any]:
    """
    LangGraph node function for query validation
    
    Args:
        state: Current state
    
    Returns:
        State updates
    """
    node = QueryValidatorNode()
    return node.validate_query(state)


if __name__ == "__main__":
    # Test the node
    print("Testing Query Validator Node (Direct OpenAI)...")
    
    try:
        from langgraph_schema import create_initial_state
        
        Config.validate()
        
        # Create test state with a query
        state = create_initial_state("Show all users")
        state["generated_query"] = "SELECT * FROM lr_dump LIMIT 5"
        state["schema_info"] = "Table: lr_dump, Columns: Billing_Party, CN_No"
        
        # Validate query
        node = QueryValidatorNode()
        result = node.validate_query(state)
        
        print("\n" + "="*80)
        print("Validation Result:")
        print(f"Passed: {result.get('validation_passed')}")
        print(f"Details:\n{result.get('validation_result')}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
