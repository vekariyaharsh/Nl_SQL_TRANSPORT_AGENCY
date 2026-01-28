"""
Node 3: Query Corrector
"""
from openai import OpenAI
from typing import Dict, Any

from config import Config
from langgraph_schema import OverallState


class QueryCorrectorNode:
    """Correct SQL queries based on validation feedback"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
    
    def _build_correction_prompt(self, state: OverallState) -> str:
        """Build prompt for query correction"""
        
        original_query = state.get("generated_query")
        validation_feedback = state.get("validation_result", "")
        
        prompt_template = f"""You are an expert at correcting MySQL SQL queries.

Original Question: {state['question']}

Original SQL Query:
{original_query}

Validation Feedback:
{validation_feedback}

Schema Information:
{state.get("schema_info", "")}

Your task:
1. Carefully read the validation feedback
2. Identify all issues mentioned
3. Correct the SQL query to address ALL issues
4. Ensure the corrected query still answers the original question
5. Return ONLY the corrected SQL query, no explanations

Corrected SQL Query:"""
        
        return prompt_template
    
    def correct_query(self, state: OverallState) -> Dict[str, Any]:
        """
        Correct the SQL query based on validation feedback
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with corrected query
        """
        iteration = state.get("iteration_count", 0) + 1
        
        print(f"\n🔧 [Node 3] Correcting query (Iteration {iteration}/{Config.MAX_CORRECTION_ITERATIONS})...")
        
        # Check if we've exceeded max iterations
        if iteration > Config.MAX_CORRECTION_ITERATIONS:
            error_msg = f"Maximum correction iterations ({Config.MAX_CORRECTION_ITERATIONS}) exceeded"
            print(f"⚠️  {error_msg}")
            return {
                "error_message": error_msg,
                "final_validation_passed": False
            }
        
        try:
            # Build prompt
            prompt_content = self._build_correction_prompt(state)
            
            # Generate corrected query
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful SQL corrector."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0
            )
            
            corrected_query = response.choices[0].message.content.strip()
            
            # Clean up the query (remove markdown code blocks if present)
            if corrected_query.startswith("```"):
                lines = corrected_query.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                corrected_query = "\n".join(lines).strip()
            
            print(f"✅ Corrected query:\n{corrected_query}\n")
            
            return {
                "corrected_query": corrected_query,
                "iteration_count": iteration
            }
            
        except Exception as e:
            error_msg = f"Error correcting query: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error_message": error_msg,
                "final_validation_passed": False
            }


def correct_query_node(state: OverallState) -> Dict[str, Any]:
    """
    LangGraph node function for query correction
    
    Args:
        state: Current state
    
    Returns:
        State updates
    """
    node = QueryCorrectorNode()
    return node.correct_query(state)


if __name__ == "__main__":
    # Test the node
    print("Testing Query Corrector Node (Direct OpenAI)...")
    
    try:
        from langgraph_schema import create_initial_state
        
        Config.validate()
        
        # Create test state with validation failure
        state = create_initial_state("Show all users")
        state["generated_query"] = "SELECT * FROM non_existent_table" 
        state["validation_result"] = """VALIDATION: FAIL

ISSUES:
- Table 'non_existent_table' does not exist in schema. Should use 'users'

SUGGESTIONS:
- Change table name for 'users'"""
        state["schema_info"] = "Tables: users, orders"
        
        # Correct query
        node = QueryCorrectorNode()
        result = node.correct_query(state)
        
        print("\n" + "="*80)
        print("Corrected Query:")
        print(result.get("corrected_query"))
        print(f"Iteration: {result.get('iteration_count')}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
