"""
Test script for Logistics SQL Pipeline
Tests all components before running the full application
"""
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

def print_header(text):
    print("\n" + "="*80)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}")
    print("="*80)

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}")

def print_warning(text):
    print(f"{Fore.YELLOW}⚠️  {text}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ️  {text}")


def test_configuration():
    """Test configuration loading"""
    print_header("1. Testing Configuration")
    
    try:
        from config import Config
        Config.validate()
        Config.display()
        print_success("Configuration loaded successfully")
        return True
    except Exception as e:
        print_error(f"Configuration error: {e}")
        print_info("Please check your .env file")
        return False


def test_mysql_connection():
    """Test MySQL connection"""
    print_header("2. Testing MySQL Connection")
    
    try:
        from mysql_connection import MySQLConnection
        from config import Config
        
        conn = MySQLConnection(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )
        
        if conn.connect():
            print_success("MySQL connection successful")
            
            # Health check
            if conn.health_check():
                print_success("Health check passed")
            
            # Get schema
            schema = conn.get_schema()
            print_info(f"Found {len(schema['tables'])} tables: {', '.join(schema['tables'][:5])}")
            
            # Check if lr_dump exists
            if 'lr_dump' in schema['tables']:
                print_success("Found lr_dump table")
                columns = schema['table_columns']['lr_dump']
                print_info(f"lr_dump has {len(columns)} columns")
            else:
                print_warning("lr_dump table not found. Update examples if your table name is different.")
            
            conn.close()
            return True
        else:
            print_error("MySQL connection failed")
            return False
            
    except Exception as e:
        print_error(f"MySQL error: {e}")
        print_info("Check MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE in .env")
        return False


def test_neo4j_connection():
    """Test Neo4j connection"""
    print_header("3. Testing Neo4j Connection (for embeddings)")
    
    try:
        from neo4j_connection import Neo4jConnection
        
        conn = Neo4jConnection()
        if conn.connect():
            print_success("Neo4j connection successful")
            
            # Health check
            if conn.health_check():
                print_success("Health check passed")
            
            # Create vector index
            try:
                conn.create_vector_index()
                print_success("Vector index created/verified")
            except Exception as e:
                print_warning(f"Vector index warning: {e}")
            
            conn.close()
            return True
        else:
            print_error("Neo4j connection failed")
            return False
            
    except Exception as e:
        print_error(f"Neo4j error: {e}")
        print_info("Check NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env")
        return False


def test_openai_connection():
    """Test OpenAI API"""
    print_header("4. Testing OpenAI API")
    
    try:
        from openai import OpenAI
        from config import Config
        
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Test with a simple embedding
        response = client.embeddings.create(
            model=Config.EMBEDDING_MODEL,
            input="test"
        )
        
        embedding = response.data[0].embedding
        print_success("OpenAI API connection successful")
        print_info(f"Embedding dimensions: {len(embedding)}")
        return True
        
    except Exception as e:
        print_error(f"OpenAI error: {e}")
        print_info("Check OPENAI_API_KEY in .env")
        return False


def test_sql_examples():
    """Test SQL examples loading"""
    print_header("5. Testing Logistics SQL Examples")
    
    try:
        from few_shot_examples_sql import LogisticsSQLExamples
        
        count = LogisticsSQLExamples.get_example_count()
        print_success(f"Loaded {count} logistics SQL examples")
        
        # Show first example
        examples = LogisticsSQLExamples.get_all_examples()
        if examples:
            first = examples[0]
            print_info(f"Example: {first['question']}")
        
        return True
        
    except Exception as e:
        print_error(f"SQL examples error: {e}")
        return False


def test_pipeline_initialization():
    """Test pipeline initialization"""
    print_header("6. Testing Pipeline Initialization")
    
    try:
        # Import but don't run
        print_info("Importing app_sql module...")
        from app_sql import NLToSQLPipeline
        print_success("app_sql module imported successfully")
        
        print_info("Note: Full pipeline initialization will happen when you run the app")
        return True
        
    except Exception as e:
        print_error(f"Pipeline initialization error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*80}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}🧪 Logistics SQL Pipeline - System Test")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}{'='*80}\n")
    
    results = {
        "Configuration": test_configuration(),
        "MySQL Connection": test_mysql_connection(),
        "Neo4j Connection": test_neo4j_connection(),
        "OpenAI API": test_openai_connection(),
        "SQL Examples": test_sql_examples(),
        "Pipeline Init": test_pipeline_initialization()
    }
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Fore.GREEN}✅ PASSED" if result else f"{Fore.RED}❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{Fore.CYAN}Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 All tests passed! Your system is ready to use.")
        print(f"\n{Fore.CYAN}Next steps:")
        print(f"  1. Run: python app_sql.py")
        print(f"  2. Ask: 'Top 5 billing parties by revenue in 2022'")
    else:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️  Some tests failed. Please fix the issues above.")
        print(f"\n{Fore.CYAN}Common fixes:")
        print(f"  • Configuration: Check .env file")
        print(f"  • MySQL: Verify database is running and credentials are correct")
        print(f"  • Neo4j: Verify Neo4j is running")
        print(f"  • OpenAI: Check API key is valid")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
