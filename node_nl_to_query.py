"""
Node 1: Natural Language to SQL Query Generator
For Logistics/Transport Management System
"""
from openai import OpenAI
from typing import Dict, Any

from config import Config
from langgraph_schema import OverallState
from mysql_schema_loader import MySQLSchemaLoader
from mysql_connection import MySQLConnection
from few_shot_examples_sql import LogisticsSQLExamples


class NLToSQLNode:
    """Convert natural language questions to MySQL SQL queries for logistics"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        
        # Connect to MySQL and load schema
        self.mysql_conn = MySQLConnection(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )
        self.mysql_conn.connect()
        self.schema_loader = MySQLSchemaLoader(self.mysql_conn)
    
    def _build_prompt(self, state: OverallState) -> str:
        """Build the prompt for SQL query generation"""
        
        # Get MySQL schema information
        schema_text = self.schema_loader.format_schema_for_llm()
        
        # Get logistics SQL examples (Static only, no vector search)
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
2. NEVER nest SELECT statements in WHERE clauses - use proper syntax
3. Structure: SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT
4. Table name: lr_dump (or relevant table from schema)
5. Column names use UNDERSCORES (Billing_Party, CN_Date, Total_Freight, etc.)
6. ALL date fields are stored as TEXT format - handle accordingly

DATE OPERATIONS (Dates are TEXT format):
- Extract year: YEAR(STR_TO_DATE(CN_Date, '%Y-%m-%d')) = 2022 OR SUBSTRING(CN_Date, 1, 4) = '2022'
- Extract month: MONTH(STR_TO_DATE(CN_Date, '%Y-%m-%d')) = 3 OR SUBSTRING(CN_Date, 6, 2) = '03'
- Date range: CN_Date BETWEEN '2021-01-01' AND '2021-12-31' (text comparison works if format is YYYY-MM-DD)
- Simple year filter: CN_Date LIKE '2022%' (fastest for text dates)

COLUMN NAMING:
- Use underscores: Billing_Party, CN_Date, Total_Freight, LR_Profit
- NO backticks needed (no spaces in column names)
- NO spaces in column names

AGGREGATIONS:
- Always use GROUP BY with aggregate functions
- Available: SUM(), COUNT(), AVG(), MAX(), MIN()
- Filter aggregates with HAVING, not WHERE

Common Patterns:
- For revenue: SUM(Total_Freight)
- For count: COUNT(CN_No)
- For profit: SUM(LR_Profit)

Question: {state['question']}

Generate ONE complete MySQL query following the above rules:"""
        
        return prompt_template
    
    def generate_query(self, state: OverallState) -> Dict[str, Any]:
        """
        Generate MySQL SQL query from natural language question
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with generated SQL query
        """
        print(f"\n🔄 [Node 1] Generating SQL query for: '{state['question']}'")
        
        try:
            # Build prompt
            prompt_content = self._build_prompt(state)
            
            # Generate SQL query
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful SQL assistant.hows  work is to create  the sql for the table transport data."
                    "Think as SQL enginer how had mastery in the create the SQl query from the  natural  language."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0
            )
            
            generated_query = response.choices[0].message.content.strip()
            
            # Clean up the query (remove markdown code blocks if present)
            if generated_query.startswith("```"):
                lines = generated_query.split("\n")
                # Remove first and last lines if they're markdown markers
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                generated_query = "\n".join(lines).strip()
            
            # Basic SQL validation
            generated_query_lower = generated_query.lower()
            
            # Check for common syntax errors
            if "where select" in generated_query_lower:
                print("⚠️  Detected nested SELECT in WHERE - attempting to fix...")
                # Try to extract the proper query
                if generated_query_lower.count("select") > 1:
                    # Take the last SELECT as the main query
                    parts = generated_query.upper().split("SELECT")
                    if len(parts) > 2:
                        # Use the last SELECT statement
                        generated_query = "SELECT" + parts[-1]
                        print(f"🔧 Fixed query:\n{generated_query}\n")
            
            # Ensure query starts with SELECT
            if not generated_query_lower.strip().startswith("select"):
                raise ValueError("Generated query must start with SELECT")
            
            print(f"✅ Generated SQL query:\n{generated_query}\n")
            
            # Get schema info
            schema_info = self.schema_loader.format_schema_for_llm()
            
            return {
                "generated_query": generated_query,
                "schema_info": schema_info
            }
            
        except Exception as e:
            error_msg = f"Error generating SQL query: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "generated_query": None,
                "error_message": error_msg
            }


def nl_to_query_node(state: OverallState) -> Dict[str, Any]:
    """
    LangGraph node function for NL to SQL generation
    
    Args:
        state: Current state
    
    Returns:
        State updates
    """
    node = NLToSQLNode()
    return node.generate_query(state)


if __name__ == "__main__":
    # Test the SQL generation node
    print("Testing NL to SQL Node (Direct OpenAI)...")
    
    try:
        from langgraph_schema import create_initial_state
        
        Config.validate()
        Config.display()
        
        # Test with logistics question
        test_question = "Top 5 billing parties based on revenue in 2022"
        
        print(f"\\n📝 Test Question: {test_question}\\n")
        
        state = create_initial_state(test_question)
        
        # Generate SQL query
        node = NLToSQLNode()
        result = node.generate_query(state)
        
        print("\\n" + "="*80)
        print("Generated SQL Query:")
        print("="*80)
        print(result.get("generated_query"))
        print("="*80)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

