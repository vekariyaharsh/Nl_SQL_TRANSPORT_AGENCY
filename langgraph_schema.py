"""
LangGraph state schema for NL-to-SQL pipeline
"""
from typing import TypedDict, List, Dict, Any, Optional


class OverallState(TypedDict):
    """
    State for the LangGraph workflow
    
    This state is passed between all nodes and maintains the complete context
    of the query generation and validation process.
    """
    
    # Input
    question: str  # Original natural language question
    
    # Query Generation
    generated_query: Optional[str]  # Initial SQL query from NL
    # Removed context_embeddings as we are not using vector search anymore
    
    # First Validation
    validation_result: Optional[str]  # Validation feedback
    validation_passed: Optional[bool]  # Whether validation passed
    
    # Query Correction
    corrected_query: Optional[str]  # Query after correction
    iteration_count: int  # Number of correction attempts
    
    # Second Validation
    final_validation_passed: Optional[bool]  # Final validation status
    
    # Query Execution
    execution_result: Optional[Any]  # Results from query execution
    execution_success: Optional[bool]  # Whether execution succeeded
    
    # Error Tracking
    error_message: Optional[str]  # Any error messages
    
    # Metadata
    schema_info: Optional[str]  # MySQL schema information
    timestamp: Optional[str]  # When the query was processed


def create_initial_state(question: str) -> OverallState:
    """
    Create initial state for a new question
    
    Args:
        question: Natural language question
    
    Returns:
        Initialized OverallState
    """
    from datetime import datetime
    
    return OverallState(
        # Input
        question=question,
        
        # Query Generation
        generated_query=None,
        
        # Validation
        validation_result=None,
        validation_passed=None,
        
        # Correction
        corrected_query=None,
        iteration_count=0,
        
        # Final Validation
        final_validation_passed=None,
        
        # Execution
        execution_result=None,
        execution_success=None,
        
        # Error Tracking
        error_message=None,
        
        # Metadata
        schema_info=None,
        timestamp=datetime.now().isoformat()
    )


if __name__ == "__main__":
    # Test state creation
    print("Testing State Schema...")
    
    state = create_initial_state("Show all users")
    print(f"\n✅ Created initial state:")
    print(f"  Question: {state['question']}")
    print(f"  Timestamp: {state['timestamp']}")
    print(f"  Iteration Count: {state['iteration_count']}")
