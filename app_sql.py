"""
Hybrid NL-to-SQL Pipeline Application
- Queries MySQL database for business analytics
- Stores query examples as embeddings in Neo4j for learning
"""
from langgraph.graph import StateGraph, END
from typing import Literal, Dict, Any
import sys

from config import Config
from langgraph_schema import OverallState, create_initial_state
from embeddings_utils import EmbeddingManager
from neo4j_connection import get_neo4j_connection
from mysql_connection import MySQLConnection
from mysql_schema_loader import MySQLSchemaLoader
from few_shot_examples_sql import SQLFewShotExamples

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


class NLToSQLPipeline:
    """Natural Language to SQL pipeline with Neo4j embedding storage"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0,
            api_key=Config.OPENAI_API_KEY
        )
        self.embedding_manager = EmbeddingManager()
        
        # MySQL connection for data queries
        self.mysql = MySQLConnection(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )
        self.mysql.connect()
        
        self.mysql_schema_loader = MySQLSchemaLoader(self.mysql)
        
        self.graph = None
        self.app = None
        self._build_graph()
    
    # ========== NODE 1: NL to SQL Generator ==========
    def nl_to_sql_node(self, state: OverallState) -> Dict[str, Any]:
        """Generate SQL query from natural language"""
        print(f"\n🔄 [Node 1] Generating SQL query for: '{state['question']}'")
        
        try:
            # Get schema
            schema_text = self.mysql_schema_loader.format_schema_for_llm()
            
            # Get few-shot examples
            few_shot_text = SQLFewShotExamples.get_examples_as_text(
                max_examples=Config.MAX_FEW_SHOT_EXAMPLES,
                business_only=True
            )
            
            # Get similar queries from Neo4j vector search
            similar_queries = self.embedding_manager.find_similar_queries(
                state["question"], 
                top_k=3
            )
            
            similar_context = ""
            if similar_queries:
                similar_context = "\n\nSimilar Past Queries:\n"
                for i, sim in enumerate(similar_queries, 1):
                    # Note: stored as 'cypher_query' but contains SQL
                    similar_context += f"{i}. Q: {sim['question']}\n"
                    similar_context += f"   SQL: {sim['cypher_query']}\n"
                    similar_context += f"   Similarity: {sim['score']:.2f}\n"
            
            prompt_template = f"""You are an expert at converting natural language questions to MySQL SQL queries for business analytics.

{schema_text}

Few-Shot Examples:
{few_shot_text}
{similar_context}

IMPORTANT GUIDELINES:
1. Generate ONLY valid MySQL SQL syntax
2. Use the exact table and column names from the schema
3. For date operations, use YEAR(), MONTH(), DATE_SUB(), CURDATE()
4. Always use proper JOIN syntax (INNER JOIN, LEFT JOIN, etc.)
5. Use aggregation functions appropriately (SUM, COUNT, AVG, etc.)
6. Add ORDER BY and LIMIT clauses when relevant
7. Use GROUP BY when aggregating
8. Use HAVING for filtering aggregated results
9. Always return meaningful column aliases
10. Handle date ranges properly with BETWEEN or >= and <=

Question: {{question}}

Generate the SQL query (MySQL syntax):"""
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm
            response = chain.invoke({"question": state["question"]})
            
            generated_query = response.content.strip()
            
            # Clean up markdown
            if generated_query.startswith("```"):
                lines = generated_query.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                generated_query = "\n".join(lines).strip()
            
            print(f"✅ Generated SQL query:\n{generated_query}\n")
            
            return {
                "generated_query": generated_query,
                "context_embeddings": similar_queries,
                "schema_info": schema_text
            }
            
        except Exception as e:
            error_msg = f"Error generating SQL query: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "generated_query": None,
                "error_message": error_msg
            }
    
    # ========== NODE 2: SQL Validator ==========
    def validate_sql_node(self, state: OverallState) -> Dict[str, Any]:
        """Validate the SQL query"""
        query_to_validate = state.get("corrected_query") or state.get("generated_query")
        
        if not query_to_validate:
            return {
                "validation_result": "No query to validate",
                "validation_passed": False,
                "error_message": "No query generated"
            }
        
        is_revalidation = state.get("corrected_query") is not None
        node_label = "Node 2 (Re-validation)" if is_revalidation else "Node 2 (Initial Validation)"
        
        print(f"\n🔍 [{node_label}] Validating SQL query...")
        print(f"Query: {query_to_validate[:100]}...")
        
        try:
            schema_text = state.get("schema_info") or self.mysql_schema_loader.format_schema_for_llm()
            
            prompt_template = f"""You are an expert MySQL SQL query validator.

{schema_text}

Original Question: {{question}}

SQL Query to Validate:
{{query}}

Validation Checklist:
1. SYNTAX: Is the MySQL SQL syntax correct?
2. SCHEMA: Do all tables exist in the schema?
3. COLUMNS: Do all columns exist in their respective tables?
4. JOINS: Are JOINs properly specified with correct foreign keys?
5. LOGIC: Does the query logically answer the question?
6. DATE FUNCTIONS: Are MySQL date functions used correctly?
7. AGGREGATION: Are GROUP BY and aggregation functions used correctly?
8. PERFORMANCE: Are there any obvious performance issues?

Respond in this format:

VALIDATION: [PASS/FAIL]

ISSUES:
- [List issues, or "None" if validation passes]

SUGGESTIONS:
- [List specific fixes, or "None" if validation passes]

Your response:"""
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm
            response = chain.invoke({
                "question": state["question"],
                "query": query_to_validate
            })
            
            validation_result = response.content.strip()
            validation_passed = "VALIDATION: PASS" in validation_result
            
            status_icon = "✅" if validation_passed else "❌"
            print(f"{status_icon} Validation {'PASSED' if validation_passed else 'FAILED'}")
            
            if not validation_passed:
                print(f"Validation feedback:\n{validation_result}\n")
            
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
    
    # ========== NODE 3: SQL Corrector ==========
    def correct_sql_node(self, state: OverallState) -> Dict[str, Any]:
        """Correct the SQL query based on validation feedback"""
        iteration = state.get("iteration_count", 0) + 1
        
        print(f"\n🔧 [Node 3] Correcting SQL query (Iteration {iteration}/{Config.MAX_CORRECTION_ITERATIONS})...")
        
        if iteration > Config.MAX_CORRECTION_ITERATIONS:
            error_msg = f"Maximum correction iterations ({Config.MAX_CORRECTION_ITERATIONS}) exceeded"
            print(f"⚠️  {error_msg}")
            return {
                "error_message": error_msg,
                "final_validation_passed": False
            }
        
        try:
            prompt_template = f"""You are an expert at correcting MySQL SQL queries.

Original Question: {{question}}

Original SQL Query:
{{original_query}}

Validation Feedback:
{{validation_feedback}}

Schema Information:
{{schema_info}}

Your task:
1. Read the validation feedback carefully
2. Identify all issues mentioned
3. Correct the SQL query to address ALL issues
4. Ensure the corrected query still answers the original question
5. Use proper MySQL syntax
6. Return ONLY the corrected SQL query, no explanations

Corrected SQL Query:"""
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm
            response = chain.invoke({
                "question": state["question"],
                "original_query": state.get("generated_query"),
                "validation_feedback": state.get("validation_result", ""),
                "schema_info": state.get("schema_info", "")
            })
            
            corrected_query = response.content.strip()
            
            # Clean up markdown
            if corrected_query.startswith("```"):
                lines = corrected_query.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                corrected_query = "\n".join(lines).strip()
            
            print(f"✅ Corrected SQL query:\n{corrected_query}\n")
            
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
    
    # ========== NODE 4: SQL Executor ==========
    def execute_sql_node(self, state: OverallState) -> Dict[str, Any]:
        """Execute the SQL query on MySQL and store in Neo4j"""
        query_to_execute = None
        
        if state.get("final_validation_passed"):
            query_to_execute = state.get("corrected_query")
        elif state.get("validation_passed"):
            query_to_execute = state.get("generated_query")
        
        if not query_to_execute:
            query_to_execute = state.get("corrected_query") or state.get("generated_query")
            if not query_to_execute:
                return {
                    "execution_success": False,
                    "error_message": "No query available to execute"
                }
        
        print(f"\n⚡ [Node 4] Executing SQL query on MySQL...")
        print(f"Query:\n{query_to_execute}\n")
        
        try:
            # Execute on MySQL
            results = self.mysql.execute_query(query_to_execute)
            
            # Format results
            formatted_results = self._format_results(results)
            
            print(f"✅ Query executed successfully on MySQL!")
            print(f"📊 Returned {len(results)} result(s)\n")
            
            # Store in Neo4j as embedding
            try:
                if state.get("validation_passed") or state.get("final_validation_passed"):
                    metadata = {
                        "result_count": len(results),
                        "iteration_count": state.get("iteration_count", 0),
                        "had_corrections": state.get("corrected_query") is not None,
                        "query_type": "SQL"
                    }
                    
                    self.embedding_manager.store_query_example(
                        question=state["question"],
                        cypher_query=query_to_execute,  # Stored as cypher_query field but contains SQL
                        metadata=metadata
                    )
                    print("💾 Stored SQL query example in Neo4j for future reference\n")
            except Exception as store_error:
                print(f"⚠️  Warning: Could not store query example: {store_error}")
            
            return {
                "execution_result": {
                    "data": results,
                    "formatted": formatted_results,
                    "count": len(results)
                },
                "execution_success": True
            }
            
        except Exception as e:
            error_msg = f"SQL execution failed: {str(e)}"
            print(f"❌ {error_msg}\n")
            
            return {
                "execution_result": None,
                "execution_success": False,
                "error_message": error_msg
            }
    
    def _format_results(self, results: list) -> str:
        """Format query results for display"""
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
    
    # ========== Graph Building ==========
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(OverallState)
        
        # Add nodes
        workflow.add_node("nl_to_sql", self.nl_to_sql_node)
        workflow.add_node("validate_sql", self.validate_sql_node)
        workflow.add_node("correct_sql", self.correct_sql_node)
        workflow.add_node("execute_sql", self.execute_sql_node)
        
        # Set entry point
        workflow.set_entry_point("nl_to_sql")
        
        # Add edges
        workflow.add_edge("nl_to_sql", "validate_sql")
        
        workflow.add_conditional_edges(
            "validate_sql",
            self._route_after_validation,
            {
                "execute": "execute_sql",
                "correct": "correct_sql",
                "end": END
            }
        )
        
        workflow.add_edge("correct_sql", "validate_sql")
        workflow.add_edge("execute_sql", END)
        
        self.app = workflow.compile()
        print("✅ NL-to-SQL LangGraph workflow compiled successfully")
    
    def _route_after_validation(self, state: OverallState) -> Literal["execute", "correct", "end"]:
        """Routing logic after validation"""
        is_revalidation = state.get("corrected_query") is not None
        
        if is_revalidation:
            if state.get("final_validation_passed"):
                print("🎯 Final validation passed → Executing SQL query")
                return "execute"
            else:
                iteration_count = state.get("iteration_count", 0)
                if iteration_count >= Config.MAX_CORRECTION_ITERATIONS:
                    print(f"⚠️  Max iterations ({Config.MAX_CORRECTION_ITERATIONS}) reached → Ending")
                    return "end"
                else:
                    print("🔄 Final validation failed → Correcting again")
                    return "correct"
        else:
            if state.get("validation_passed"):
                print("✅ Initial validation passed → Executing SQL query")
                return "execute"
            else:
                print("🔧 Initial validation failed → Correcting SQL query")
                return "correct"
    
    def run(self, question: str) -> OverallState:
        """Run the pipeline"""
        print("\n" + "="*80)
        print(f"🚀 Starting NL-to-SQL Pipeline")
        print(f"Question: {question}")
        print("="*80)
        
        initial_state = create_initial_state(question)
        final_state = self.app.invoke(initial_state)
        
        print("\n" + "="*80)
        print("🏁 Pipeline Completed")
        print("="*80)
        
        return final_state
    
    def print_results(self, state: OverallState):
        """Pretty print results"""
        print("\n" + "="*80)
        print("📊 RESULTS")
        print("="*80)
        
        print(f"\n📝 Question: {state['question']}")
        
        if state.get("generated_query"):
            print(f"\n🔹 Initial SQL Query:")
            print(f"{state['generated_query']}")
        
        if state.get("corrected_query"):
            print(f"\n🔸 Corrected SQL Query (after {state.get('iteration_count', 0)} iterations):")
            print(f"{state['corrected_query']}")
        
        if state.get("validation_passed") or state.get("final_validation_passed"):
            print(f"\n✅ Validation: PASSED")
        else:
            print(f"\n❌ Validation: FAILED")
            if state.get("validation_result"):
                print(f"Feedback: {state['validation_result'][:200]}...")
        
        if state.get("execution_success"):
            print(f"\n✅ Execution: SUCCESS (MySQL)")
            if state.get("execution_result"):
                result = state["execution_result"]
                print(f"📊 Result Count: {result['count']}")
                print(f"\nResults:\n{result['formatted']}")
        elif state.get("execution_success") is False:
            print(f"\n❌ Execution: FAILED")
            if state.get("error_message"):
                print(f"Error: {state['error_message']}")
        
        print("\n" + "="*80)
    
    def shutdown(self):
        """Close connections"""
        if self.mysql:
            self.mysql.close()


def interactive_mode():
    """Interactive mode for SQL queries"""
    print("\n" + "="*80)
    print("🤖 NL-to-SQL Pipeline - Business Analytics Mode")
    print("="*80)
    print("\nQueries will be executed on MySQL and stored in Neo4j for learning")
    print("\nCommands:")
    print("  - Type your business question to generate and execute SQL")
    print("  - Type 'quit' or 'exit' to exit")
    print("="*80 + "\n")
    
    try:
        Config.validate()
        pipeline = NLToSQLPipeline()
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return
    
    # Ensure Neo4j vector index
    try:
        neo4j = get_neo4j_connection()
        neo4j.create_vector_index()
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize Neo4j vector index: {e}")
    
    while True:
        try:
            question = input("\n💬 Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            final_state = pipeline.run(question)
            pipeline.print_results(final_state)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    pipeline.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="NL-to-SQL Pipeline for MySQL with Neo4j Learning"
    )
    parser.add_argument(
        "--question",
        "-q",
        type=str,
        help="Natural language question (single query mode)"
    )
    
    args = parser.parse_args()
    
    if args.question:
        try:
            Config.validate()
            pipeline = NLToSQLPipeline()
            
            neo4j = get_neo4j_connection()
            neo4j.create_vector_index()
            
            final_state = pipeline.run(args.question)
            pipeline.print_results(final_state)
            
            pipeline.shutdown()
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        interactive_mode()
